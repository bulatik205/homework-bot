# all code written from AI
# check quality, before use

import requests
import telebot
from datetime import datetime
from config import BOT_TOKEN, BACKEND_URL, PROXY_ENABLED, PROXY_URL, PROXY_SECRET

bot = telebot.TeleBot(BOT_TOKEN)


def call_backend(path: str) -> dict:
    if PROXY_ENABLED:
        r = requests.get(
            PROXY_URL,
            params={"secret": PROXY_SECRET, "path": path},
            timeout=15,
        )
    else:
        r = requests.get(BACKEND_URL + path, timeout=15)
    return r.json()

MONTHS_SHORT = [
    "янв", "фев", "мар", "апр", "мая", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        date_part = iso.split("T")[0]
        d = datetime.strptime(date_part, "%Y-%m-%d")
        return f"{d.day} {MONTHS_SHORT[d.month - 1]}"
    except Exception:
        return iso


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!")


@bot.message_handler(commands=["ping"])
def ping(message):
    try:
        data = call_backend("/api/v1/ping")
        bot.send_message(message.chat.id, data.get("success", "no") and "pong 🐛")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


@bot.message_handler(commands=["tasks"])
def tasks(message):
    try:
        data = call_backend("/api/v1/tasks")
        if not data.get("success"):
            bot.send_message(message.chat.id, f"Ошибка: {data.get('error', 'unknown')}")
            return

        items = data.get("body") or []
        if not items:
            bot.send_message(message.chat.id, "Задач нет 🎉")
            return

        by_subject = {}
        for t in items:
            by_subject.setdefault(t["subject"], []).append(t)

        lines = []
        for subject, ts in by_subject.items():
            lines.append(f"📚 {subject}")
            for t in ts:
                date_str = ""
                if t.get("date_to"):
                    date_str = f" (до {fmt_date(t['date_to'])})"
                lines.append(f"  • {t['task']}{date_str}")
            lines.append("")

        bot.send_message(message.chat.id, "\n".join(lines))
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)