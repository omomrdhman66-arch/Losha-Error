from telebot import types
from storage.db import get_connection
from storage.repositories.credits import ensure_row, get_credits
from storage.repositories.bans import is_banned


def register_redeem(bot):

    @bot.message_handler(commands=["redeem"])
    def redeem_code(message):
        uid = message.from_user.id
        user_id = message.from_user.id
        if is_banned(user_id):
            bot.send_message(
                message.chat.id,
                "🚫 You are banned from using this bot."
            )
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 2:
                return

            code = parts[1].strip().upper()
            user_id = message.from_user.id

            conn = get_connection()
            cur = conn.cursor()

            # 1️⃣ تحقق إن المستخدم ما استخدمش الكود قبل كده
            cur.execute(
                "SELECT 1 FROM code_redeems WHERE code = ? AND user_id = ?",
                (code, user_id)
            )
            if cur.fetchone():
                conn.close()
                bot.reply_to(message, "❌ You already redeemed this code.")
                return

            # 2️⃣ جلب بيانات الكود
            cur.execute(
                """
                SELECT credits, max_uses, used_count
                FROM codes
                WHERE code = ?
                """,
                (code,)
            )
            row = cur.fetchone()

            if not row:
                conn.close()
                bot.reply_to(message, "❌ Invalid or expired code.")
                return

            credits, max_uses, used_count = row

            if used_count >= max_uses:
                conn.close()
                bot.reply_to(message, "❌ This code has reached its maximum uses.")
                return

            # 3️⃣ تجهيز المستخدم
            ensure_row(user_id)
            balance = get_credits(user_id)

            # 4️⃣ إضافة الرصيد (إلا لو Unlimited)
            if balance != -1:
                cur.execute(
                    "UPDATE credits SET balance = balance + ? WHERE user_id = ?",
                    (credits, user_id)
                )

            # 5️⃣ تحديث استخدام الكود
            cur.execute(
                "UPDATE codes SET used_count = used_count + 1 WHERE code = ?",
                (code,)
            )

            # 6️⃣ تسجيل إن المستخدم استخدم الكود
            cur.execute(
                "INSERT INTO code_redeems (code, user_id) VALUES (?, ?)",
                (code, user_id)
            )

            conn.commit()

            new_balance = get_credits(user_id)
            conn.close()

            # 7️⃣ رسالة النجاح (HTML + Compact)
            bot.send_message(
                message.chat.id,
                f"""━━━━━━━━━━━━━━━━━━
✅ <b>CODE REDEEMED</b>
━━━━━━━━━━━━━━━━━━

🎟Code -> <code>{code}</code>
💰Credits -> +{credits}
💳Balance -> {'Unlimited' if new_balance == -1 else new_balance}

✨Enjoy using all bot commands
━━━━━━━━━━━━━━━━━━
""",
                parse_mode="HTML"
            )

        except Exception:
            bot.reply_to(message, "❌ Error redeeming the code.")