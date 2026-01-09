import random
from telebot import types
from storage.repositories.users import create_or_update_user
from storage.repositories.credits import get_credits
from security.channel_guard import is_channel_subscribed, send_channel_prompt
from storage.repositories.bans import is_banned
VIDEO_LINKS = [
    "https://t.me/L_O_S_H_A_1/26",
    "https://t.me/L_O_S_H_A_1/27",
    "https://t.me/L_O_S_H_A_1/28",
    "https://t.me/L_O_S_H_A_1/31",
    "https://t.me/L_O_S_H_A_1/34",
    "https://t.me/L_O_S_H_A_1/35",
    "https://t.me/L_O_S_H_A_1/41",
    "https://t.me/L_O_S_H_A_1/67",
    "https://t.me/L_O_S_H_A_1/148",
]

def register_start(bot):


    @bot.message_handler(commands=["start"])
    def start_handler(message):
        user_id = message.from_user.id
        name = message.from_user.first_name
    

        if is_banned(user_id):
            bot.send_message(
                message.chat.id,
                "🚫 You are banned from using this bot."
            )
            return
    

        if not is_channel_subscribed(bot, user_id):
            send_channel_prompt(bot, message.chat.id, name)
            return

        create_or_update_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=name
        )

        vip = get_credits(user_id) != 0

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("ϟ Programmer - Losha ϟ", url="https://t.me/I_EOR"))

        if vip:
            caption = f"""✨ Welcome -> {name} ✨

- Subscription active ✅
- Combo check Send Your Combo
ϟ Programmer • @I_EOR ϟ"""
        else:
            caption = f"""✨ Welcome Dear -> {name} ✨

/cmds | /buy"""

        bot.send_video(
            chat_id=message.chat.id,
            video=random.choice(VIDEO_LINKS),
            caption=caption,
            reply_markup=kb
        )
        
        
        
