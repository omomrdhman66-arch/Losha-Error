from storage.repositories.bans import is_banned
from security.channel_guard import is_channel_subscribed, send_channel_prompt

def guard_or_block(bot, message):
    user_id = message.from_user.id

    # حظر
    if is_banned(user_id):
        return False

    # اشتراك القنوات (مش /start)
    if not is_channel_subscribed(bot, user_id):
        send_channel_prompt(
            bot,
            message.chat.id,
            message.from_user.first_name or ""
        )
        return False

    return True