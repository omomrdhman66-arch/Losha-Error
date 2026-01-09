import time

def run_single_check(bot, message, cc, gate_name, gate_func):
    ko = bot.reply_to(
        message,
        "<b>⏳ Please wait checking your card...</b>",
        parse_mode="HTML"
    ).message_id

    start_time = time.time()
    try:
        result = str(gate_func(cc))
    except Exception:
        result = "Gateway Error"

    execution_time = round(time.time() - start_time, 2)
    r = result.lower()

    # Approved
    if "approved" in r:
        msg = approved_message(cc, result, gate_name, execution_time, dato)
        bot.edit_message_text(
            msg,
            chat_id=message.chat.id,
            message_id=ko,
            parse_mode="HTML"
        )
        bot.pin_chat_message(message.chat.id, ko, disable_notification=True)
        return

    # Charged
    if "charged" in r or "thank you for your donation" in r:
        msg = charged_message(cc, result, gate_name, execution_time, dato)
        bot.edit_message_text(
            msg,
            chat_id=message.chat.id,
            message_id=ko,
            parse_mode="HTML"
        )
        bot.pin_chat_message(message.chat.id, ko, disable_notification=True)
        return

    # Funds
    if "fund" in r or "insufficient" in r:
        msg = insufficient_funds_message(cc, result, gate_name, execution_time, dato)
        bot.edit_message_text(
            msg,
            chat_id=message.chat.id,
            message_id=ko,
            parse_mode="HTML"
        )
        bot.pin_chat_message(message.chat.id, ko, disable_notification=True)
        return

    # Declined (بدون pin)
    msg = declined_message(cc, result, gate_name, execution_time, dato)
    bot.edit_message_text(
        msg,
        chat_id=message.chat.id,
        message_id=ko,
        parse_mode="HTML"
    )