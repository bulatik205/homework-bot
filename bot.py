# all code written from AI
# check quality, before use

import requests
import telebot
from config import (
    BOT_TOKEN, BACKEND_URL,
    PROXY_ENABLED, PROXY_URL, PROXY_SECRET,
)

bot = telebot.TeleBot(BOT_TOKEN)


def call_backend(path: str) -> str:
    if PROXY_ENABLED:
        r = requests.get(
            PROXY_URL,
            params={"secret": PROXY_SECRET, "path": path},
            timeout=15,
        )
    else:
        r = requests.get(BACKEND_URL + path, timeout=15)
    return r.text


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!")


@bot.message_handler(commands=["ping"])
def ping(message):
    try:
        text = call_backend("/api/v1/ping")
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)