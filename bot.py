# all code written from AI
# check quality, before use

import requests
import telebot
from config import BOT_TOKEN, BACKEND_URL

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!")


@bot.message_handler(commands=["ping"])
def ping(message):
    try:
        r = requests.get(BACKEND_URL + "/api/v1/ping", timeout=10)
        bot.send_message(message.chat.id, r.text)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)