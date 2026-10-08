# all code written from AI
# check quality, before use

import html
import re
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from datetime import datetime, timedelta
from config import BOT_TOKEN, BACKEND_URL, PROXY_ENABLED, PROXY_URL, PROXY_SECRET

bot = telebot.TeleBot(BOT_TOKEN)

WEB_URL = "https://hw.bulatik.website"

def call_backend(path: str) -> dict:
    if PROXY_ENABLED:
        r = requests.get(
            PROXY_URL,
            params={"secret": PROXY_SECRET, "path": path},
            timeout=15,
        )
    else:
        r = requests.get(BACKEND_URL + path, timeout=15)
    r.raise_for_status()
    return r.json()


SUBJECT_NAMES = {
    "math": "Алгебра",
    "geometry": "Геометрия",
    "russian": "Русский язык",
    "literature": "Литература",
    "history": "История",
    "physics": "Физика",
    "chemistry": "Химия",
    "biology": "Биология",
    "geography": "География",
    "english": "Английский",
    "social": "Общество",
    "informatics": "Информатика",
    "pe": "Физкультура",
    "obzh": "ОБЖ",
    "technology": "Технология",
    "random-and-stat": "Вероятность и статистика",
    "projects": "Проекты",
}

SUBJECT_SHORT = {
    "алг": "math", "мат": "math", "алгебра": "math",
    "геом": "geometry",
    "геог": "geography", "география": "geography",
    "рус": "russian", "русс": "russian",
    "лит": "literature", "литра": "literature",
    "ист": "history",
    "физ": "physics",
    "хим": "chemistry",
    "био": "biology", "биол": "biology",
    "англ": "english", "eng": "english",
    "общ": "social", "общество": "social",
    "инф": "informatics", "инфа": "informatics", "информ": "informatics",
    "физра": "pe", "физ-ра": "pe",
    "обж": "obzh", "обзр": "obzh",
    "техн": "technology", "тех": "technology",
    "вер": "random-and-stat", "стат": "random-and-stat",
    "проект": "projects", "проекты": "projects",
}


def subject_display(code: str) -> str:
    return SUBJECT_NAMES.get(code, code)


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


MONTHS_SHORT = [
    "янв", "фев", "мар", "апр", "мая", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def tomorrow_local() -> datetime:
    now = datetime.now()
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def fmt_date_human(iso: str) -> str:
    if not iso:
        return ""
    try:
        d = datetime.strptime(iso.split("T")[0], "%Y-%m-%d")
        return f"{d.day} {MONTHS_SHORT[d.month - 1]}"
    except Exception:
        return iso


def days_until(iso: str):
    if not iso:
        return None
    try:
        d = datetime.strptime(iso.split("T")[0], "%Y-%m-%d").date()
        today = datetime.now().date()
        return (d - today).days
    except Exception:
        return None


def human_days(n: int) -> str:
    if n == 0:
        return "сегодня"
    if n == 1:
        return "завтра"
    if n == 2:
        return "послезавтра"
    if n > 0:
        return f"через {n} дн."
    if n == -1:
        return "вчера"
    return f"{-n} дн. назад"


def web_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏝️ Сайт", web_app=WebAppInfo(url=WEB_URL)))
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "👋 <b>Привет!</b>\n\n"
        "Я показываю домашку:\n"
        "<blockquote><code>@дз</code> — что задано на <b>завтра</b>\n"
        "<code>@дз мат</code> — последнее ДЗ по предмету</blockquote>\n\n"
        "<i>Сокращения: алг, геом, геог, рус, лит, ист, физ, хим, био, англ, общ, инф, физра, обж, тех, вер, проект</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=web_kb())


@bot.message_handler(commands=["ping"])
def ping(message):
    try:
        data = call_backend("/api/v1/ping")
        if data.get("success"):
            bot.send_message(message.chat.id, "pong 🏓", parse_mode="HTML", reply_markup=web_kb())
        else:
            bot.send_message(
                message.chat.id,
                f"⚠️ Ошибка: {e(data.get('error', 'unknown'))}",
                parse_mode="HTML",
                reply_markup=web_kb(),
            )
    except Exception as ex:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e(ex)}",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )


DZ_RE = re.compile(r"^@дз\s*(?:#\s*)?(.*)$", re.IGNORECASE)


@bot.message_handler(func=lambda m: m.text and DZ_RE.match(m.text.strip()))
def handle_dz(message):
    m = DZ_RE.match(message.text.strip())
    query = m.group(1).strip()

    if not query:
        show_tomorrow(message)
    else:
        show_subject(message, query)


def show_tomorrow(message):
    tomorrow = tomorrow_local()
    date_str = tomorrow.strftime("%Y-%m-%d")

    try:
        data = call_backend(f"/api/v1/tasks?date={date_str}")
    except Exception as ex:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e(ex)}",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    if not data.get("success"):
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e(data.get('error', 'unknown'))}",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    items = data.get("body") or []
    if not items:
        bot.send_message(
            message.chat.id,
            f"👻 <b>На завтра</b> ({e(fmt_date_human(date_str))}) заданий я не нашел...",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    groups = {}
    for t in items:
        key = t.get("instead_of") or t["subject"]
        groups.setdefault(key, []).append(t)

    lines = [f"🏎️ <b>Завтра</b> · <i>{e(fmt_date_human(date_str))}</i>", ""]

    for key, tasks in groups.items():
        first = tasks[0]
        if first.get("instead_of"):
            header = (
                f"🧸 <b>{e(subject_display(first['subject']))}</b> "
                f"(вместо <u>{e(subject_display(first['instead_of']))}</u>)"
            )
        else:
            header = f"🧸 <b>{e(subject_display(key))}</b>"

        lines.append(header)
        for t in tasks:
            lines.append(f"\n<blockquote><code>{e(t['task'])}</code></blockquote>")
        lines.append("")

    bot.send_message(
        message.chat.id,
        "\n".join(lines).rstrip(),
        parse_mode="HTML",
        reply_markup=web_kb(),
    )


def show_subject(message, query: str):
    code = SUBJECT_SHORT.get(query.lower().strip())
    if not code:
        bot.send_message(
            message.chat.id,
            f"🤔 Не знаю предмет «<b>{e(query)}</b>».\n"
            f"<i>Попробуй: алг, геом, геог, рус, лит, ист, физ, хим, био, англ, общ, инф</i>",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    try:
        data = call_backend(f"/api/v1/tasks?subject={code}&recency=last")
    except Exception as ex:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e(ex)}",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    if not data.get("success"):
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e(data.get('error', 'unknown'))}",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    items = data.get("body") or []
    if not items:
        bot.send_message(
            message.chat.id,
            f"💕 <b>{e(subject_display(code))}</b>\n\n<i>Я не нашел задания</i>",
            parse_mode="HTML",
            reply_markup=web_kb(),
        )
        return

    t = items[0]

    header = f"🏎️ <b>{e(subject_display(code))}</b>"
    if t.get("instead_of"):
        header += f" <i>(вместо {e(subject_display(t['instead_of']))})</i>"

    lines = [header, "", f"<blockquote><code>{e(t['task'])}</code></blockquote>"]

    if t.get("date_to"):
        d = days_until(t["date_to"])
        tail = f" ({e(human_days(d))})" if d is not None else ""
        lines.append(f"\n🍌 <b>На</b> {e(fmt_date_human(t['date_to']))}{tail}")

    bot.send_message(
        message.chat.id,
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=web_kb(),
    )


if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)