def register_prices(bot):
    @bot.message_handler(commands=['prices'])
    def prices_handler(message):
        bot.reply_to(message, '''
💎 VIP Prices

• 1 Hour  - 10 ⭐
• 1 Day   - 60 ⭐
• 1 Week  - 250 ⭐

Use /buy to continue
''')
