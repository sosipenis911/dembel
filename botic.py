from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, CommandHandler
from datetime import datetime, timedelta
import json
import os

FILENAME = "user.json"
PAGE_SIZE = 8
MSK_NOW = datetime.utcnow() + timedelta(hours=3)

# --- Армейские даты ---
army_dates = {
    7: "Малая кочерга 🪵 — 7 дпп",
    11: "Малые барабанные палочки 🥁 / Первые зеркала 🪞 — 11 дпп",
    22: "Вторые зеркала 🪞 — 22 дпп",
    30: "Присяга — 30 дпп",
    32: "333 ддд",
    33: "Малые кудряшки 💇‍♂️ / Третьи зеркала 🪞 — 33 дпп",
    36: "10% — 36 дпп",
    38: "Малые попугайчики 🦜 — 38 дпп",
    44: "Маленькие стульчики 🪑 / Четвертые зеркала 🪞 — 44 дпп",
    50: "50 дпп",
    55: "Пятые зеркала 🪞 — 55 дпп",
    65: "300 дней до дома",
    66: "Шестые зеркала 🪞 — 66 дпп",
    73: "20% — 73 дпп",
    77: "Малые топорики / Седьмые зеркала 🪞 — 77 дпп",
    88: "Малые матрешки 🪆 / Восьмые зеркала 🪞 — 88 дпп",
    91: "Прошла четверть службы",
    99: "Девятые зеркала 🪞 — 99 дпп",
    100: "100 дней после призыва",
    109: "30% — 109 дпп",
    111: "Малый заборчик 🏡 — 111 дпп",
    115: "250 ддд",
    122: "Прошла треть службы",
    143: "Малые гуси-лебеди 🦢 — 222 ддд",
    145: "Малая розетка 🔌 — 220 ддд",
    146: "40% — 146 дпп",
    150: "150 дпп",
    165: "200 дней до дембеля",
    182: "ЭКВАТОР",
    200: "200 дней после призыва",
    215: "150 дней до дембеля",
    219: "60% — 219 дпп",
    220: "Большая розетка 🔌 — 220 дпп",
    222: "Большие гуси-лебеди 🦢 — 222 дпп",
    250: "Осталась треть службы",
    254: "Большой заборчик 🏡 — 111 ддд",
    265: "100 дней до дембеля",
    266: "Десятые зеркала 🪞 — 99 ддд",
    274: "Осталась четверть службы",
    277: "Большие матрешки 🪆 / Одиннадцатые зеркала 🪞 — 88 ддд",
    288: "Большие топорики / Двенадцатые зеркала 🪞 — 77 ддд",
    299: "Тринадцатые зеркала 🪞 — 66 ддд",
    300: "300 дней после призыва",
    315: "Ставьте водку 🥂 в холодильник - нам до дембеля полтинник!",
    321: "Большие стульчики 🪑 / Четырнадцатые зеркала 🪞 — 44 ддд",
    325: "Ставьте водку 🥂 на паркет - нам до дома сорокет!",
    327: "Большие попугайчики 🦜 — 38 ддд",
    329: "90% — 36 ддд",
    332: "Большие кудряшки 💇‍♂️ / Пятнадцатые зеркала 🪞 — 33 ддд",
    343: "Шестнадцатые зеркала 🪞 — 22 ддд",
    350: "350 дпп",
    354: "Большие барабанные палочки 🥁 / Семнадцатые зеркала 🪞 — 11 ддд",
    355: "КОСМОС",
    362: "Светофор красный ❤️ 🚦",
    363: "Светофор жёлтый 💛 🚦",
    364: "Светофор зеленый 💚 🚦",
    365: "Дембель!!!"
}

# Добавляем недели (1–52)
for i in range(1, 53):
    day = i * 7
    if day not in army_dates:
        army_dates[day] = f"{i} неделя 💜"

# Добавляем месяцы (1–12)
for i in range(1, 13):
    day = i * 30
    if day not in army_dates:
        army_dates[day] = f"{i}/12 💖"


# --- Работа с файлом ---
def load_users():
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            for chat_id in list(data.keys()):
                if not isinstance(data[chat_id], dict):
                    data[chat_id] = {}
                if 'end_date' in data[chat_id]:
                    if isinstance(data[chat_id]['end_date'], str):
                        data[chat_id]['end_date'] = datetime.strptime(
                            data[chat_id]['end_date'], "%d.%m.%Y"
                        )
                else:
                    data[chat_id]['end_date'] = datetime.now()
                if 'custom_dates' in data[chat_id]:
                    for name, dt in data[chat_id]['custom_dates'].items():
                        if isinstance(dt, str):
                            data[chat_id]['custom_dates'][name] = datetime.strptime(dt, "%d.%m.%Y")
                else:
                    data[chat_id]['custom_dates'] = {}
                if 'hidden_dates' in data[chat_id]:
                    data[chat_id]['hidden_dates'] = set(data[chat_id]['hidden_dates'])
                else:
                    data[chat_id]['hidden_dates'] = set()
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(data):
    data_to_save = {}
    for chat_id in data:
        data_to_save[str(chat_id)] = {}
        data_to_save[str(chat_id)]['end_date'] = data[chat_id]['end_date'].strftime("%d.%m.%Y")
        data_to_save[str(chat_id)]['custom_dates'] = {
            name: dt.strftime("%d.%m.%Y") for name, dt in data[chat_id].get('custom_dates', {}).items()
        }
        data_to_save[str(chat_id)]['hidden_dates'] = list(data[chat_id].get('hidden_dates', set()))
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

user_dates = load_users()

# --- Статистика бота ---
STATS_FILE = "stats.json"

def load_stats():
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"total_starts": 0, "users": {}}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def register_start(update):
    stats = load_stats()
    user_id = str(update.effective_user.id)
    now = datetime.utcnow().isoformat()

    stats["total_starts"] += 1

    if user_id not in stats["users"]:
        stats["users"][user_id] = {
            "first_seen": now,
            "last_seen": now,
            "starts": 1
        }
    else:
        stats["users"][user_id]["last_seen"] = now
        stats["users"][user_id]["starts"] += 1

    save_stats(stats)

# --- Старт ---
def start(update: Update, context: CallbackContext):
    register_start(update)
    update.message.reply_text(
        "Привет, это ДМБ таймер в тг <3\n"
        "Мой тикток — barannikova\n"
        "Введите дату дембеля в формате ДД.ММ.ГГГГ\n"
        "Например: 15.11.2026"
    )
def stats(update: Update, context: CallbackContext):
    print("КОМАНДА STATS ПОЛУЧЕНА")
    admin_id = os.getenv("795174337")

    if not admin_id or str(update.effective_user.id) != admin_id:
        update.message.reply_text("⛔ Эта команда доступна только администратору.")
        return

    data = load_stats()

    total = data["total_starts"]
    unique = len(data["users"])
    repeated = total - unique

    today = datetime.utcnow().date().isoformat()

    today_users = sum(
        1 for u in data["users"].values()
        if u["last_seen"][:10] == today
    )

    update.message.reply_text(
        f"📊 Статистика ДМБ таймера\n\n"
        f"🚀 Всего запусков: {total}\n"
        f"👥 Уникальных пользователей: {unique}\n"
        f"🔁 Повторных запусков: {repeated}\n"
        f"📅 Активных сегодня: {today_users}"
    )
# --- Сохранение даты ---
def save_date(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    text = update.message.text

    # --- Сохранение пользовательской цитаты ---
    if context.user_data.get('editing_quote'):
        chat_id = str(update.message.chat_id)
        user_dates[chat_id]['quote'] = update.message.text  # сохраняем цитату
        save_users(user_dates)  # сохраняем в файл
        context.user_data['editing_quote'] = False

        # Кнопка "Вернуться" после сохранения
        keyboard = [[InlineKeyboardButton("Вернуться", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text("✅ Цитата сохранена!", reply_markup=reply_markup)
        return  # не продолжаем обработку других сообщений

    # --- Добавление пользовательской даты ---
    if context.user_data.get('adding_custom'):
        chat_id = str(update.message.chat_id)
        text = update.message.text

        if '-' not in text:
            update.message.reply_text("❌ Неверный формат. Используй: Название - ДД.MM.ГГГГ")
            return

        try:
            name, date_str = text.split('-', 1)
            name = name.strip()
            date_obj = datetime.strptime(date_str.strip(), "%d.%m.%Y")

            # Если пользователь ещё не добавил дату конца службы
            if chat_id not in user_dates:
                update.message.reply_text("Сначала введите дату конца службы :)")
                return

            # Добавляем или обновляем пользовательскую дату
            user_dates[chat_id]['custom_dates'][name] = date_obj

            # Сортируем пользовательские даты по дате
            user_dates[chat_id]['custom_dates'] = dict(
                sorted(user_dates[chat_id]['custom_dates'].items(), key=lambda x: x[1])
            )

            save_users(user_dates)
            context.user_data['adding_custom'] = False
            update.message.reply_text(f"✅ Дата '{name}' сохранена!")

            # Кнопка назад в меню всех дат
            keyboard = [[InlineKeyboardButton("Назад", callback_data='all')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Вы можете вернуться назад:", reply_markup=reply_markup)

        except Exception:
            update.message.reply_text("❌ Неверный формат. Попробуйте так: Название - ДД.MM.ГГГГ")
        return

    # --- Сохранение даты конца службы ---
    try:
        end_date = datetime.strptime(text, "%d.%m.%Y")

        if chat_id not in user_dates or not isinstance(user_dates[chat_id], dict):
            user_dates[chat_id] = {
                'end_date': end_date,
                'custom_dates': {},
                'hidden_dates': set(),
                'quote': ""  # <-- сюда будем сохранять цитату пользователя
            }

        else:
            user_dates[chat_id]['end_date'] = end_date
            if 'custom_dates' not in user_dates[chat_id]:
                user_dates[chat_id]['custom_dates'] = {}
            if 'hidden_dates' not in user_dates[chat_id]:
                user_dates[chat_id]['hidden_dates'] = set()

        save_users(user_dates)

        today = datetime.utcnow() + timedelta(hours=3)

        days_to_end = (end_date - today).days
        days_text = "завтра" if days_to_end == 0 else f"{days_to_end} дн"
        start_date = end_date - timedelta(days=365)

        # --- Ближайшее событие ---
        upcoming_event = None
        min_days = None
        hidden = user_dates[chat_id].get('hidden_dates', set())

        for day, event in sorted(army_dates.items()):
            if event in hidden:
                continue
            event_date = start_date + timedelta(days=int(day))
            days_until_event = (event_date - today).days
            if days_until_event >= 0:
                upcoming_event = f"{event} — {'завтра' if days_until_event==0 else f'через {days_until_event} дн'} ({event_date.strftime('%d.%m.%Y')})"
                min_days = days_until_event
                break

        for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
            if isinstance(dt, str):
                dt = datetime.strptime(dt, "%d.%m.%Y")
                user_dates[chat_id]['custom_dates'][name] = dt
            if name in hidden:
                continue
            days_until_event = (dt - today).days
            if days_until_event >= 0 and (min_days is None or days_until_event < min_days):
                upcoming_event = f"{name} — {'завтра' if days_until_event==0 else f'через {days_until_event} дн'} ({dt.strftime('%d.%m.%Y')})"
                min_days = days_until_event

        if not upcoming_event:
            upcoming_event = "Все события уже прошли."

        keyboard = [
            [
                InlineKeyboardButton("Таймер", callback_data='info')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"Дата сохранена ✅\n",
            reply_markup=reply_markup
        )

    except ValueError:
        update.message.reply_text("❌ Неверный формат. Попробуйте: ДД.ММ.ГГГГ")

# --- Обработка кнопок ---
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = str(query.message.chat_id)

    if chat_id not in user_dates or not isinstance(user_dates[chat_id], dict):
        user_dates[chat_id] = {
            'end_date': datetime.now(),
            'custom_dates': {},
            'hidden_dates': set()
        }
    end_date = user_dates[chat_id]['end_date']
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%d.%m.%Y")
        user_dates[chat_id]['end_date'] = end_date

    # --- Информация ---
    if query.data == 'info':
        end_date = user_dates[chat_id]['end_date']
        today = datetime.utcnow() + timedelta(hours=3)

        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        # --- Прошло и осталось ---
        passed = today - start_date
        remaining = end_date - today
        passed_days = passed.days
        passed_hours = passed.seconds // 3600
        passed_minutes = (passed.seconds % 3600) // 60
        passed_seconds = passed.seconds % 60

        remaining_days = remaining.days
        remaining_hours = remaining.seconds // 3600
        remaining_minutes = (remaining.seconds % 3600) // 60
        remaining_seconds = remaining.seconds % 60


        # Проверяем армейские даты
        today_events = []
        for day, event in army_dates.items():
            event_date = start_date + timedelta(days=int(day))
            if event_date.date() == today.date():  # совпадает с сегодня
                today_events.append(event)

        # Проверяем пользовательские даты
        for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
            if dt.date() == today.date():
                today_events.append(name)

        # --- Ближайшее событие ---
        upcoming_event = None
        min_days = None
        hidden = user_dates[chat_id].get('hidden_dates', set())
        for day, event in sorted(army_dates.items()):
            if event in hidden:
                continue
            event_date = start_date + timedelta(days=int(day))
            days_until_event = (event_date - today).days
            if days_until_event >= 0:
                if days_until_event == 0:
                    day_text = "завтра"
                else:
                    day_text = f"через {days_until_event} {pluralize(days_until_event, ['день', 'дня', 'дней'])}"
                upcoming_event = f"{event} — {day_text} ({event_date.strftime('%d.%m.%Y')})"
                min_days = days_until_event
                break

        for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
            if name in hidden:
                continue
            days_until_event = (dt - today).days
            if days_until_event >= 0 and (min_days is None or days_until_event < min_days):
                if days_until_event == 0:
                    day_text = "завтра"
                else:
                    day_text = f"через {days_until_event} {pluralize(days_until_event, ['день', 'дня', 'дней'])}"
                upcoming_event = f"{name} — {day_text} ({dt.strftime('%d.%m.%Y')})"
                min_days = days_until_event

        if not upcoming_event:
            upcoming_event = "Все события уже прошли."

        # --- Кнопки выбора вида прогресса ---
        keyboard = [
            [InlineKeyboardButton("Обновить", callback_data='info')],  # отдельная строка
            [
                InlineKeyboardButton("Проценты", callback_data='info_percent'),
                InlineKeyboardButton("Недели", callback_data='info_weeks'),
                InlineKeyboardButton("Месяцы", callback_data='info_months')
            ],  # строка с тремя кнопками
            [InlineKeyboardButton("Настройки", callback_data='settings'), InlineKeyboardButton("Все даты", callback_data='all')]  # отдельная строка
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        quote = user_dates[chat_id].get('quote', "")
        today_text = today.strftime('%d.%m.%Y')
        if today_events:
            today_text += " — " + ", ".join(today_events)  # перечисляем события сегодня
        text = (
            f"📅 Сегодня: {today_text}\n"
            "\n"
            f"Ближайшее событие: {upcoming_event}\n\n")
        if quote:
            text += f" {quote} \n\n"



        text +=(
            f"Прошло: {passed_days} {pluralize(passed_days, ['день', 'дня', 'дней'])}, "
            f"{passed_hours} {pluralize(passed_hours, ['час', 'часа', 'часов'])}, "
            f"{passed_minutes} {pluralize(passed_minutes, ['минута', 'минуты', 'минут'])}, "
            f"{passed_seconds} {pluralize(passed_seconds, ['секунда', 'секунды', 'секунд'])}\n"
            f"Осталось: {remaining_days} {pluralize(remaining_days, ['день', 'дня', 'дней'])}, "
            f"{remaining_hours} {pluralize(remaining_hours, ['час', 'часа', 'часов'])}, "
            f"{remaining_minutes} {pluralize(remaining_minutes, ['минута', 'минуты', 'минут'])}, "
            f"{remaining_seconds} {pluralize(remaining_seconds, ['секунда', 'секунды', 'секунд'])}\n\n"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    # --- Обработка нажатий на подменю информации ---
    elif query.data == 'info_percent':
        today = datetime.utcnow() + timedelta(hours=3)

        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']

        total_seconds = (end_date - start_date).total_seconds()
        passed_seconds = (today - start_date).total_seconds()
        percent = (passed_seconds / total_seconds) * 100
        percent_bar = "🔵" * int(percent // 10) + "⚪" * (10 - int(percent // 10))

        keyboard = [[InlineKeyboardButton("Обновить", callback_data='info_percent')],[InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(f"Прогресс службы: {percent:.6f}%\n{percent_bar}", reply_markup=reply_markup)



    elif query.data == 'info_weeks':
        today = datetime.utcnow() + timedelta(hours=3)

        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']
        passed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        passed_weeks = passed_days // 7
        days_in_current_week = passed_days % 7
        remaining_weeks = remaining_days // 7
        # строим индикатор текущей недели
        weeks_bar = "💜" * days_in_current_week + "🤍" * (7 - days_in_current_week)
        keyboard = [[InlineKeyboardButton("Обновить", callback_data='info_weeks')], [InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"Прошло: {passed_weeks} {pluralize(passed_weeks, ['неделя', 'недели', 'недель'])}, "
            f"{days_in_current_week} {pluralize(days_in_current_week, ['день', 'дня', 'дней'])}\n"
            f"Осталось: {remaining_weeks} {pluralize(remaining_weeks, ['неделя', 'недели', 'недель'])}, "
            f"{remaining_days % 7} {pluralize(remaining_days % 7, ['день', 'дня', 'дней'])}\n"
            f"{weeks_bar}"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    elif query.data == 'info_months':
        today = datetime.utcnow() + timedelta(hours=3)

        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']
        passed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        # Подсчет прошедших и оставшихся месяцев
        passed_months = passed_days // 30
        remaining_months = remaining_days // 30
        # Шкала месяцев (как раньше)
        total_months = 12
        months_bar = "💖" * min(total_months, passed_months) + "🤍" * (total_months - min(total_months, passed_months))
        keyboard = [[InlineKeyboardButton("Обновить", callback_data='info_months')], [InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"Прошло: {passed_months} {pluralize(passed_months, ['месяц', 'месяца', 'месяцев'])}, "
            f"{passed_days % 30} {pluralize(passed_days % 30, ['день', 'дня', 'дней'])}\n"
            f"Осталось: {remaining_months} {pluralize(remaining_months, ['месяц', 'месяца', 'месяцев'])}, "
            f"{remaining_days % 30} {pluralize(remaining_days % 30, ['день', 'дня', 'дней'])} \n"
            f"{months_bar}"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    elif query.data == 'settings':
        query.edit_message_text(
            "Запустить бота сначала:/start \nВведите текст, который будет отображаться в меню:\nНапример: Илья💖"
        )
        context.user_data['editing_quote'] = True

    # --- Все даты с двумя кнопками ---
    elif query.data == 'all':
        try:
            chat_id = str(query.message.chat_id)
            today = datetime.utcnow() + timedelta(hours=3)

            hidden = user_dates[chat_id].get('hidden_dates', set())

            all_events = []
            start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)

            # --- Армейские даты ---
            for day, event in sorted(army_dates.items()):
                if event in hidden:
                    continue
                event_date = start_date + timedelta(days=int(day))
                if event_date < today:
                    event_text = f" ✅ {event}"  # прошедшее событие с галочкой
                else:
                    event_text = event  # будущие события без галочки
                all_events.append((event_date, f"{event_date.strftime('%d.%m.%Y')} — {event_text}"))

            # --- Пользовательские даты ---
            for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
                if dt < today:
                    date_text = f"✅ {name}"
                else:
                    date_text = name
                all_events.append((dt, f"{dt.strftime('%d.%m.%Y')} — {date_text} ({(dt - start_date).days} дпп)"))

            # --- Сортировка всех событий ---
            all_events.sort(key=lambda x: x[0])

            # --- Разбиваем текст на куски по 4000 символов ---
            max_len = 4000
            chunks = []
            current = "Все даты:\n"
            for dt, txt in all_events:
                if len(current) + len(txt) + 1 > max_len:
                    chunks.append(current)
                    current = ""
                current += txt + "\n"
            if current:
                chunks.append(current)

            # Кнопки только в первом сообщении
            keyboard = [
                [InlineKeyboardButton("Добавить свою дату", callback_data='add_custom'), InlineKeyboardButton("Удалить дату", callback_data='delete_custom')],
                [InlineKeyboardButton("Назад", callback_data='info')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части
            for i, chunk in enumerate(chunks):
                if i == 0:
                    query.edit_message_text(chunk, reply_markup=reply_markup)
                else:
                    context.bot.send_message(chat_id=query.message.chat_id, text=chunk)

        except Exception as e:
            query.edit_message_text(f"❌ Ошибка: {e}")
    # --- Добавление своей даты ---
    elif query.data == 'add_custom':
        query.edit_message_text(
            "Введите название вашей даты и дату в формате:\n"
            "Название события - ДД.MM.ГГГГ\n"
            "Например: День рождения - 31.08.2026"
        )
        context.user_data['adding_custom'] = True

    # --- Удаление даты ---
    elif query.data == 'delete_custom':
        context.user_data['del_page'] = 0
        show_delete_page(query, context)

    elif query.data == 'del_next':
        context.user_data['del_page'] += 1
        show_delete_page(query, context)

    elif query.data == 'del_prev':
        context.user_data['del_page'] -= 1
        show_delete_page(query, context)

        # --- Удаление конкретной даты ---
    elif query.data.startswith('del|'):
        _, typ, key = query.data.split('|', 2)
        chat_id = str(query.message.chat_id)

        if typ == 'army':
            # Скрываем встроенную дату
            if 'hidden_dates' not in user_dates[chat_id]:
                user_dates[chat_id]['hidden_dates'] = set()
            user_dates[chat_id]['hidden_dates'].add(army_dates[int(key)])
            query.answer("✅ Дата скрыта")
        else:
            # Удаляем пользовательскую дату полностью
            if key in user_dates[chat_id]['custom_dates']:
                del user_dates[chat_id]['custom_dates'][key]
                query.answer("✅ Дата удалена")

        # Сохраняем изменения
        save_users(user_dates)
        # Перерисовываем страницу удаления
        show_delete_page(query, context)




    # --- Назад ---
    elif query.data == 'back':
        keyboard = [
            [
                InlineKeyboardButton("Информация", callback_data='info'),
                InlineKeyboardButton("Все даты", callback_data='all')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Выберите действие:", reply_markup=reply_markup)

def pluralize(value, forms):
    """
    value: число
    forms: список из 3 форм: ["день", "дня", "дней"]
    """
    value = abs(value) % 100
    if 11 <= value <= 19:
        return forms[2]
    i = value % 10
    if i == 1:
        return forms[0]
    elif 2 <= i <= 4:
        return forms[1]
    else:
        return forms[2]

def show_delete_page(query, context):
    chat_id = str(query.message.chat_id)
    page_size = 10  # сколько кнопок на странице
    page = context.user_data.get('del_page', 0)

    # Получаем даты
    hidden = user_dates[chat_id].get('hidden_dates', set())
    start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)

    events = []

    # Армейские даты
    for day, event in sorted(army_dates.items()):
        if event in hidden:
            continue
        events.append({
            'type': 'army',
            'key': str(day),
            'name': event,
            'date': start_date + timedelta(days=int(day))
        })

    # Пользовательские даты
    for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
        if name in hidden:
            continue
        events.append({
            'type': 'custom',
            'key': name,
            'name': name,
            'date': dt
        })

    # Сортировка по дате
    events.sort(key=lambda x: x['date'])

    total_pages = (len(events) - 1) // page_size + 1
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_events = events[start_idx:end_idx]

    # Кнопки
    keyboard = []
    for ev in page_events:
        btn_text = f"{ev['name']} ({ev['date'].strftime('%d.%m.%Y')})"
        callback_data = f"del|{ev['type']}|{ev['key']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data='del_prev'))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data='del_next'))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка назад в главное меню
    keyboard.append([InlineKeyboardButton("Назад", callback_data='all')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправка/редактирование сообщения
    query.edit_message_text("Выберите дату для удаления:", reply_markup=reply_markup)
    return


# --- Основная функция ---
def main():
    bot_token = os.getenv("BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_date), group=1)
    dispatcher.add_handler(CallbackQueryHandler(button), group=0)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

