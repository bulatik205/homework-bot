# all code written from AI
# check quality, before use

import telebot

from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!"
    )


if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)