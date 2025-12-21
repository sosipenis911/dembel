from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler, CommandHandler
)
from datetime import datetime, timedelta
import json
import os
import calendar

FILENAME = "users.json"

# ================= АРМЕЙСКИЕ ДАТЫ (БЕЗ ИЗМЕНЕНИЙ) =================
army_dates = {
     7: "Малая кочерга — 7 дпп",
    11: "Малые барабанные палочки / Первые зеркала — 11 дпп",
    22: "Вторые зеркала — 22 дпп",
    30: "Присяга — 30 дпп",
    32: "333 ддд",
    33: "Малые кудряшки / Третьи зеркала — 33 дпп",
    36: "10% — 36 дпп",
    38: "Малые попугайчики — 38 дпп",
    44: "Маленькие стульчики / Четвертые зеркала — 44 дпп",
    50: "50 дпп",
    55: "Пятые зеркала — 55 дпп",
    65: "300 дней до дома",
    66: "Шестые зеркала — 66 дпп",
    73: "20% — 73 дпп",
    77: "Малые топорики / Седьмые зеркала — 77 дпп",
    88: "Малые матрешки / Восьмые зеркала — 88 дпп",
    91: "Прошла четверть службы",
    99: "Девятые зеркала — 99 дпп",
    100: "100 дней после призыва",
    109: "30% — 109 дпп",
    111: "Малый заборчик — 111 дпп",
    115: "250 ддд",
    122: "Прошла треть службы",
    143: "Малые гуси-лебеди — 222 ддд",
    145: "Малая розетка — 220 ддд",
    146: "40% — 146 дпп",
    150: "150 дпп",
    165: "200 дней до дембеля",
    182: "ЭКВАТОР",
    200: "200 дней после призыва",
    215: "150 дней до дембеля",
    219: "60% — 219 дпп",
    220: "Большая розетка — 220 дпп",
    222: "Большие гуси-лебеди — 222 дпп",
    250: "Осталась треть службы",
    254: "Большой заборчик — 111 ддд",
    265: "100 дней до дембеля",
    266: "Десятые зеркала — 99 ддд",
    274: "Осталась четверть службы",
    277: "Большие матрешки / Одиннадцатые зеркала — 88 ддд",
    288: "Большие топорики / Двенадцатые зеркала — 77 ддд",
    299: "Тринадцатые зеркала — 66 ддд",
    300: "300 дней после призыва",
    315: "Ставьте водку в холодильник - нам до дембеля полтинник!",
    321: "Большие стульчики / Четырнадцатые зеркала — 44 ддд",
    325: "Ставьте водку на паркет - нам до дома сорокет!",
    327: "Большие попугайчики — 38 ддд",
    329: "90% — 36 ддд",
    332: "Большие кудряшки / Пятнадцатые зеркала — 33 ддд",
    343: "Шестнадцатые зеркала — 22 ддд",
    350: "350 дпп",
    354: "Большие барабанные палочки / Семнадцатые зеркала — 11 ддд",
    355: "КОСМОС",
    362: "Светофор красный ❤️",
    363: "Светофор жёлтый 💛",
    364: "Светофор зеленый 💚",
    365: "Дембель!!!"
}

for i in range(1, 53):
    army_dates.setdefault(i * 7, f"{i} неделя 💜")

for i in range(1, 13):
    army_dates.setdefault(i * 30, f"{i}/12 💖")

# ================= ФАЙЛ =================
def load_users():
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            raw = json.load(f)
        users = {}
        for cid, d in raw.items():
            users[cid] = {
                'end_date': datetime.strptime(d['end_date'], "%d.%m.%Y"),
                'custom_dates': {k: datetime.strptime(v, "%d.%m.%Y") for k, v in d.get('custom_dates', {}).items()},
                'hidden_dates': set(d.get('hidden_dates', [])),
                'utc_offset': d.get('utc_offset', 3),
                'notify_time': d.get('notify_time', '00:01'),
                'last_notify': datetime.strptime(d['last_notify'], "%d.%m.%Y").date() if d.get('last_notify') else None
            }
        return users
    except:
        return {}

def save_users(data):
    out = {}
    for cid, d in data.items():
        out[cid] = {
            'end_date': d['end_date'].strftime("%d.%m.%Y"),
            'custom_dates': {k: v.strftime("%d.%m.%Y") for k, v in d['custom_dates'].items()},
            'hidden_dates': list(d['hidden_dates']),
            'utc_offset': d['utc_offset'],
            'notify_time': d['notify_time'],
            'last_notify': d['last_notify'].strftime("%d.%m.%Y") if d['last_notify'] else None
        }
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

user_dates = load_users()

# ================= ВСПОМОГАТЕЛЬНЫЕ =================
def user_now(chat_id):
    return datetime.utcnow() + timedelta(hours=user_dates[chat_id].get('utc_offset', 3))

def service_start(chat_id):
    return user_dates[chat_id]['end_date'] - timedelta(days=365)

def today_events(chat_id):
    today = user_now(chat_id).date()
    start = service_start(chat_id)
    hidden = user_dates[chat_id]['hidden_dates']
    events = []

    for d, e in army_dates.items():
        if e not in hidden and (start + timedelta(days=d)).date() == today:
            events.append(e)

    for name, dt in user_dates[chat_id]['custom_dates'].items():
        if name not in hidden and dt.date() == today:
            events.append(name)

    return events

# ================= START =================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет 👋\nВыбери часовой пояс:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("UTC+2", callback_data="tz|2"),
             InlineKeyboardButton("UTC+3 🇷🇺", callback_data="tz|3"),
             InlineKeyboardButton("UTC+4", callback_data="tz|4")],
            [InlineKeyboardButton("UTC+5", callback_data="tz|5"),
             InlineKeyboardButton("UTC+6", callback_data="tz|6")]
        ])
    )

# ================= СОХРАНЕНИЕ ДАТ =================
def save_date(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    text = update.message.text

    if context.user_data.get('adding_custom'):
        try:
            name, date_str = text.split('-', 1)
            dt = datetime.strptime(date_str.strip(), "%d.%m.%Y")
            user_dates[chat_id]['custom_dates'][name.strip()] = dt
            save_users(user_dates)
            context.user_data['adding_custom'] = False
            update.message.reply_text("✅ Дата добавлена", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Назад", callback_data="all")]]
            ))
        except:
            update.message.reply_text("❌ Формат: Название - ДД.MM.ГГГГ")
        return

    try:
        end_date = datetime.strptime(text, "%d.%m.%Y")
    except:
        update.message.reply_text("❌ Формат: ДД.MM.ГГГГ")
        return

    user_dates.setdefault(chat_id, {
        'custom_dates': {},
        'hidden_dates': set(),
        'utc_offset': 3,
        'notify_time': '00:01',
        'last_notify': None
    })
    user_dates[chat_id]['end_date'] = end_date
    save_users(user_dates)

    update.message.reply_text(
        "Дата сохранена ✅",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Информация", callback_data="info"),
             InlineKeyboardButton("Все даты", callback_data="all")],
            [InlineKeyboardButton("Календарь", callback_data="calendar")]
        ])
    )

# ================= КНОПКИ =================
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = str(query.message.chat_id)

    if query.data.startswith("tz|"):
        user_dates.setdefault(chat_id, {})['utc_offset'] = int(query.data.split("|")[1])
        save_users(user_dates)
        query.edit_message_text("Введите дату конца службы\nДД.MM.ГГГГ")
        return

    if chat_id not in user_dates:
        query.edit_message_text("❗ Сначала введи дату конца службы")
        return

    today = user_now(chat_id)
    start = service_start(chat_id)

    # === ИНФОРМАЦИЯ ===
    if query.data == "info":
        passed = today - start
        remaining = user_dates[chat_id]['end_date'] - today

        passed_sec = int(passed.total_seconds())
        remaining_sec = int(remaining.total_seconds())

        events_today = today_events(chat_id)
        today_block = ""
        if events_today:
            today_block = "🔥 Сегодня:\n" + "\n".join(f"• {e}" for e in events_today) + "\n\n"

        query.edit_message_text(
            f"📅 Сегодня: {today.strftime('%d.%m.%Y')}\n"
            f"{today_block}"
            f"Прошло: {passed_sec//86400} дн\n"
            f"Осталось: {remaining_sec//86400} дн\n\n"
            "Выберите вид прогресса:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Проценты", callback_data="info_percent")],
                [InlineKeyboardButton("Недели", callback_data="info_weeks")],
                [InlineKeyboardButton("Месяцы", callback_data="info_months")],
                [InlineKeyboardButton("Назад", callback_data="back")]
            ])
        )

    elif query.data == "info_percent":
        total = (user_dates[chat_id]['end_date'] - start).total_seconds()
        passed = (today - start).total_seconds()
        percent = max(0, min(100, (passed / total) * 100))
        bar = "🔵" * int(percent // 10) + "⚪️" * (10 - int(percent // 10))
        query.edit_message_text(f"{percent:.4f}%\n{bar}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="info")]]))

    elif query.data == "info_weeks":
        passed_days = (today - start).days
        weeks = passed_days // 7
        bar = "🔵" * min(7, int((weeks / 52) * 7)) + "⚪️" * (7 - min(7, int((weeks / 52) * 7)))
        query.edit_message_text(f"Прошло: {weeks} недель\n{bar}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="info")]]))

    elif query.data == "info_months":
        passed_days = (today - start).days
        months = passed_days // 30
        bar = "🔵" * min(12, int((months / 12) * 12)) + "⚪️" * (12 - min(12, int((months / 12) * 12)))
        query.edit_message_text(f"Прошло: {months} месяцев\n{bar}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="info")]]))

    elif query.data == "calendar":
        cal = calendar.monthcalendar(today.year, today.month)
        text = f"📆 {calendar.month_name[today.month]} {today.year}\nПн Вт Ср Чт Пт Сб Вс\n"
        for w in cal:
            text += " ".join(f"{d:2}" if d else "  " for d in w) + "\n"
        query.edit_message_text(text,
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]]))

    elif query.data == "back":
        query.edit_message_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Информация", callback_data="info"),
                 InlineKeyboardButton("Все даты", callback_data="all")],
                [InlineKeyboardButton("Календарь", callback_data="calendar")]
            ])
        )

# ================= УВЕДОМЛЕНИЯ =================
def check_notifications(context: CallbackContext):
    for chat_id in user_dates:
        now = user_now(chat_id)
        h, m = map(int, user_dates[chat_id]['notify_time'].split(":"))
        if now.hour == h and now.minute == m:
            if user_dates[chat_id]['last_notify'] != now.date():
                events = today_events(chat_id)
                if events:
                    context.bot.send_message(chat_id=chat_id,
                        text="🔥 Сегодня:\n" + "\n".join(f"• {e}" for e in events))
                user_dates[chat_id]['last_notify'] = now.date()
                save_users(user_dates)

# ================= MAIN =================
def main():
    updater = Updater(os.getenv("BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, save_date))
    dp.add_handler(CallbackQueryHandler(button))

    updater.job_queue.run_repeating(check_notifications, 60, first=10)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
