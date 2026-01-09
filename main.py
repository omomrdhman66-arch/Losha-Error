from core.bot import create_bot
from handlers import register_all
from storage.db import init_db
from storage.repositories.gates import init_gates


def main():
    # ===== INIT DATABASE =====
    init_db()
    init_gates()

    # ===== CREATE BOT =====
    bot = create_bot()

    # ===== REGISTER ALL HANDLERS =====
    register_all(bot)

    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()