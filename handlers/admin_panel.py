import threading
import sqlite3
import time
from datetime import datetime, timedelta
from telebot import types
from storage.db import get_connection
# استيراد الإعدادات من ملف config
try:
    from config.config import ADMINS, OWNER_ID, TOOL_BY
except ImportError:


# الحالة المؤقتة للأدمن
ADMIN_STATES = {}

def is_admin(bot, chat_id, user_id):
    """
    فحص ذكي للصلاحيات:
    1. التحقق إذا كان المستخدم في قائمة الأدمن (ADMINS) أو هو المالك (OWNER_ID).
    2. التحقق من رتبة المستخدم في الشات (Admin/Creator) لضمان الأمان في المجموعات العامة.
    """
    # فحص القائمة الثابتة أولاً (سريع)
    if user_id == OWNER_ID or user_id in ADMINS:
        return True
    
    # فحص رتبة المستخدم في الشات (للمجموعات العامة)
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error checking admin status: {e}")
    
    return False

# ================= GATES INFO =================
GATES = {
    "stripe_auth": "Stripe_Auth",
    "shopify_charge": "Shopify_Charge",
    "braintree_auth": "Braintree_Auth",
    "stripe_charge": "Stripe_Charge",
    "paypal_donation": "Paypal_Donation",
}

# ================= HELPER FUNCTIONS =================
def safe_int(text):
    try:
        return int(text)
    except:
        return None

def get_gate_info(gate_key):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT enabled, max_cards, cost_per_card FROM gate_state WHERE gate_key = ?", (gate_key,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO gate_state (gate_key, enabled, max_cards, cost_per_card) VALUES (?, 1, 200, 1)", (gate_key,))
            return 1, 200, 1
        return row

# ================= PANELS =================
def render_main_panel(bot, chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Users", callback_data="ap:users"),
        types.InlineKeyboardButton("💰 Credits", callback_data="ap:credits"),
        types.InlineKeyboardButton("🚪 Gates", callback_data="ap:gates"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="ap:broadcast")
    )
    text = f"🛠 <b>Admin Control Panel</b>\n\nBy: {TOOL_BY}"
    try:
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        print(f"Render Error: {e}")

def render_gate_panel(bot, chat_id, message_id, gate_key):
    enabled, max_cards, cost = get_gate_info(gate_key)
    status = "✅ ON" if enabled else "❌ OFF"
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(f"Status: {status}", callback_data=f"gate:toggle:{gate_key}"),
        types.InlineKeyboardButton(f"Max Cards: {max_cards}", callback_data=f"gate:limit:{gate_key}"),
        types.InlineKeyboardButton(f"Cost: {cost}", callback_data=f"gate:cost:{gate_key}"),
        types.InlineKeyboardButton("⬅ Back", callback_data="ap:gates")
    )
    
    bot.edit_message_text(f"🚪 <b>Gate: {GATES.get(gate_key, gate_key)}</b>", chat_id, message_id, reply_markup=kb, parse_mode="HTML")

# ================= REGISTER HANDLERS =================
def register_admin_panel(bot):

    @bot.message_handler(commands=['admin'])
    def open_admin(message):
        if is_admin(bot, message.chat.id, message.from_user.id):
            render_main_panel(bot, message.chat.id)
        else:
            bot.reply_to(message, "❌ <b>انطر يا كسمك انت مش ادمن/b>", parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('ap:'))
    def admin_callbacks(c):
        # فحص ذكي: هل لا يزال المستخدم أدمن؟
        if not is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.answer_callback_query(c.id, "❌ <b>انطر يا كسمك انت مش ادمن/b>", show_alert=True)
            try: bot.delete_message(c.message.chat.id, c.message.message_id)
            except: pass
            return

        action = c.data.split(':')[1]
        
        if action == "back":
            ADMIN_STATES.pop(c.from_user.id, None)
            render_main_panel(bot, c.message.chat.id, c.message.message_id)
            
        elif action == "users":
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💎 VIP List", callback_data="ap:vip_list"),
                   types.InlineKeyboardButton("⬅ Back", callback_data="ap:back"))
            bot.edit_message_text("👤 <b>User Management</b>", c.message.chat.id, c.message.message_id, reply_markup=kb, parse_mode="HTML")

        elif action == "vip_list":
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, first_name, username, vip_until FROM users WHERE vip_until IS NOT NULL")
                rows = cur.fetchall()
            
            if not rows:
                bot.answer_callback_query(c.id, "No VIP users found.")
                return

            txt = "💎 <b>VIP Users:</b>\n\n"
            now = datetime.now()
            for uid, name, user, until in rows:
                try:
                    exp = datetime.fromisoformat(until) if isinstance(until, str) else until
                    if exp > now:
                        rem = exp - now
                        txt += f"• <a href='tg://user?id={uid}'>{name}</a> | <code>{uid}</code>\nExp: {until} ({rem.days}d {rem.seconds//3600}h)\n\n"
                except: continue
            
            bot.send_message(c.message.chat.id, txt, parse_mode="HTML")

        elif action == "gates":
            kb = types.InlineKeyboardMarkup(row_width=1)
            for k, v in GATES.items():
                kb.add(types.InlineKeyboardButton(v, callback_data=f"gate:manage:{k}"))
            kb.add(types.InlineKeyboardButton("⬅ Back", callback_data="ap:back"))
            bot.edit_message_text("🚪 <b>Gate Control</b>", c.message.chat.id, c.message.message_id, reply_markup=kb, parse_mode="HTML")

        elif action == "broadcast":
            ADMIN_STATES[c.from_user.id] = "waiting_broadcast"
            bot.send_message(c.message.chat.id, "📢 <b>أرسل الرسالة التي تريد نشرها (نص، صورة، الخ):</b>", parse_mode="HTML")

    # ================= GATES MANAGEMENT =================
    @bot.callback_query_handler(func=lambda c: c.data.startswith('gate:'))
    def gate_callbacks(c):
        # فحص ذكي في كل ضغطة زر
        if not is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.answer_callback_query(c.id, "❌ <b>انطر يا كسمك انت مش ادمن/b>", show_alert=True)
            try: bot.delete_message(c.message.chat.id, c.message.message_id)
            except: pass
            return

        parts = c.data.split(':')
        action, gate_key = parts[1], parts[2]

        if action == "manage":
            render_gate_panel(bot, c.message.chat.id, c.message.message_id, gate_key)
        
        elif action == "toggle":
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE gate_state SET enabled = 1 - enabled WHERE gate_key = ?", (gate_key,))
            render_gate_panel(bot, c.message.chat.id, c.message.message_id, gate_key)
            
        elif action == "cost":
            ADMIN_STATES[c.from_user.id] = {"action": "set_cost", "gate": gate_key}
            bot.send_message(c.message.chat.id, f"💰 <b>أرسل السعر الجديد لـ {gate_key}:</b>", parse_mode="HTML")

    # ================= INPUT HANDLER =================
    @bot.message_handler(func=lambda m: m.from_user.id in ADMIN_STATES)
    def handle_admin_inputs(m):
        # فحص الصلاحية عند إرسال مدخلات (برودكاست أو سعر)
        if not is_admin(bot, m.chat.id, m.from_user.id):
            ADMIN_STATES.pop(m.from_user.id, None)
            bot.reply_to(m, "❌ <b>انطر يا كسمك انت مش ادمن/b>", parse_mode="HTML")
            return

        state = ADMIN_STATES[m.from_user.id]

        if state == "waiting_broadcast":
            ADMIN_STATES.pop(m.from_user.id)
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM users")
                users = cur.fetchall()
            
            msg = bot.send_message(m.chat.id, f"🚀 <b>جاري النشر لـ {len(users)} مستخدم...</b>", parse_mode="HTML")
            
            success, fail = 0, 0
            for (uid,) in users:
                try:
                    bot.copy_message(uid, m.chat.id, m.message_id)
                    success += 1
                    time.sleep(0.05)
                except:
                    fail += 1
            
            bot.edit_message_text(f"✅ <b>تم النشر بنجاح!</b>\n\nنجاح: {success}\nفشل: {fail}", m.chat.id, msg.message_id, parse_mode="HTML")

        elif isinstance(state, dict) and state.get("action") == "set_cost":
            new_cost = safe_int(m.text)
            if new_cost is None:
                bot.reply_to(m, "❌ يرجى إرسال رقم صحيح.")
                return
            
            gate = state["gate"]
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE gate_state SET cost_per_card = ? WHERE gate_key = ?", (new_cost, gate))
            
            ADMIN_STATES.pop(m.from_user.id)
            bot.send_message(m.chat.id, f"✅ تم تحديث سعر <b>{gate}</b> إلى <b>{new_cost}</b>", parse_mode="HTML")
