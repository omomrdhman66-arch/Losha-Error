from telebot import types
import time
from datetime import datetime

from storage.repositories.bans import is_banned
from storage.repositories.credits import get_credits, deduct_one_atomic
from storage.repositories.gates import is_gate_enabled
from utils.messages import (
    approved_message,
    charged_message,
    insufficient_funds_message,
    declined_message,
    dato
)

# ===== GATES =====
from gates.stripe_auth import check as stripe_auth_check
from gates.shopify_charge import check as shopify_charge_check
from gates.braintree_auth import check as braintree_auth_check
from gates.stripe_charge import check as stripe_charge_check
from gates.paypal_donation import check as paypal_donation_check


SINGLE_GATES = {
    "str": ("ϟ Stripe Auth ϟ", stripe_auth_check, "AUTH", "stripe_auth"),
    "sh":  ("ϟ Shopify Charge ϟ", shopify_charge_check, "CHARGE", "shopify_charge"),
    "br":  ("ϟ Braintree Auth ϟ", braintree_auth_check, "AUTH", "braintree_auth"),
    "st":  ("ϟ Stripe Charge ϟ", stripe_charge_check, "CHARGE", "stripe_charge"),
    "pp":  ("ϟ Paypal Donation ϟ", paypal_donation_check, "CHARGE", "paypal_donation"),
}


def register_single_commands(bot):

    # ===== CORE RUNNER =====
    def run_single_check(message, gate_key, card):
        user_id = message.from_user.id

        # 🚫 BANNED
        if is_banned(user_id):
            bot.reply_to(
                message,
                "<b>🚫 YOU ARE BANNED FROM USING THIS BOT</b>",
                parse_mode="HTML"
            )
            return

        # ✅ UNPACK مرة واحدة فقط
        gate_name, gate_func, gate_type, db_key = SINGLE_GATES[gate_key]

        # ⛔ GATE DISABLED
        if not is_gate_enabled(db_key):
            bot.reply_to(
                message,
                f"<b>⛔ GATE DISABLED</b>\n\n<b>{gate_name}</b> is currently closed by admin.",
                parse_mode="HTML"
            )
            return

        # 💳 CREDITS
        credits = get_credits(user_id)
        if credits == 0:
            bot.reply_to(
                message,
                "<b>❌ YOU HAVE NO CREDITS</b>\n<b>Please buy credits to continue.</b>",
                parse_mode="HTML"
            )
            return

        # ⏳ WAIT MESSAGE
        wait_msg = bot.reply_to(
            message,
            "<b>⏳ PLEASE WAIT CHECKING YOUR CARD...</b>",
            parse_mode="HTML"
        )
        msg_id = wait_msg.message_id

        start = time.time()
        try:
            result = str(gate_func(card))
        except Exception:
            result = "Gateway Error ❌"

        exec_time = round(time.time() - start, 2)
        result_l = result.lower()

        # 💳 DEDUCT CREDIT
        if credits != -1:
            deduct_one_atomic(user_id)

        # ===== AUTH GATES =====
        if gate_type == "AUTH":
            if "approved" in result_l:
                text = approved_message(card, result, gate_name, exec_time, dato)
                bot.edit_message_text(text, message.chat.id, msg_id, parse_mode="HTML")
                bot.pin_chat_message(message.chat.id, msg_id, disable_notification=True)
            else:
                text = declined_message(card, result, gate_name, exec_time, dato)
                bot.edit_message_text(text, message.chat.id, msg_id, parse_mode="HTML")

        # ===== CHARGE GATES =====
        else:
            if "charged" in result_l or "thank you" in result_l:
                text = charged_message(card, result, gate_name, exec_time, dato)
                bot.edit_message_text(text, message.chat.id, msg_id, parse_mode="HTML")
                bot.pin_chat_message(message.chat.id, msg_id, disable_notification=True)

            elif "fund" in result_l:
                text = insufficient_funds_message(card, result, gate_name, exec_time, dato)
                bot.edit_message_text(text, message.chat.id, msg_id, parse_mode="HTML")
                bot.pin_chat_message(message.chat.id, msg_id, disable_notification=True)

            else:
                text = declined_message(card, result, gate_name, exec_time, dato)
                bot.edit_message_text(text, message.chat.id, msg_id, parse_mode="HTML")

    # ===== SINGLE COMMAND HANDLER =====
    @bot.message_handler(
        func=lambda m: (
            m.text
            and (
                (m.text.startswith(".") and m.text.split()[0][1:].lower() in SINGLE_GATES)
                or
                (m.text.startswith("/") and m.text.split()[0][1:].lower() in SINGLE_GATES)
            )
        )
    )
    def single_handler(message):
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) != 2:
            return

        cmd = parts[0][1:].lower()
        card = parts[1]

        run_single_check(message, cmd, card)