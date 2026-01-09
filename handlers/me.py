from storage.db import get_connection
from storage.repositories.credits import ensure_row, get_credits
from storage.repositories.bans import is_banned
def register_me(bot):

    @bot.message_handler(commands=["me"])
    def me_handler(message):
        user = message.from_user
        user_id = user.id

        uid = message.from_user.id

        if is_banned(user_id):
            bot.send_message(
                message.chat.id,
                "🚫 You are banned from using this bot."
            )
            return

        ensure_row(user_id)
        credits = get_credits(user_id)

        name = user.first_name or "NoName"
        username = f"@{user.username}" if user.username else "NoUsername"
        credits_text = "Unlimited" if credits == -1 else credits

        text = f"""
𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐈𝐧𝐟𝐨

𝐍𝐚𝐦𝐞 : {name}
𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 : {username}
𝐔𝐬𝐞𝐫 𝐈𝐃 : {user_id}
𝐂𝐫𝐞𝐝𝐢𝐭𝐬 : {credits_text}
"""

        bot.send_message(message.chat.id, text)