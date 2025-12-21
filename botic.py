from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, CommandHandler
from datetime import datetime, timedelta
import json
import os
FILENAME = "users.json"

# --- Армейские даты ---
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
    109: "30% — 109 дпп",
    100: "100 дней после призыва",
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

# Добавляем недели (1–52)
for i in range(1, 53):
    day = i * 7
    if day not in army_dates:
        army_dates[day] = f"{i} неделя 💜"
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

# --- Старт ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет 👋\n"
        "Введите дату конца службы в формате ДД.ММ.ГГГГ\n"
        "Например: 15.11.2026"
    )

# --- Сохранение даты ---
def save_date(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    text = update.message.text

    # --- Добавление пользовательской даты ---
    if context.user_data.get('adding_custom'):
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

            # Если название есть в скрытых, удаляем
            if name in user_dates[chat_id]['hidden_dates']:
                user_dates[chat_id]['hidden_dates'].remove(name)

            # Сортировка пользовательских дат по дате
            user_dates[chat_id]['custom_dates'] = dict(
                sorted(user_dates[chat_id]['custom_dates'].items(), key=lambda x: x[1])
            )

            # Сохраняем изменения
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
                'hidden_dates': set()
            }
        else:
            user_dates[chat_id]['end_date'] = end_date
            if 'custom_dates' not in user_dates[chat_id]:
                user_dates[chat_id]['custom_dates'] = {}
            if 'hidden_dates' not in user_dates[chat_id]:
                user_dates[chat_id]['hidden_dates'] = set()

        save_users(user_dates)

        today = datetime.now()
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
                InlineKeyboardButton("Информация", callback_data='info'),
                InlineKeyboardButton("Все даты", callback_data='all')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"Дата сохранена ✅\n"
            f"Сегодня: {today.strftime('%d.%m.%Y')}\n"
            f"До дембеля: {days_text}\n"
            f"Ближайшее событие: {upcoming_event}\n"
            f"Выберите действие:",
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
    start_date = end_date - timedelta(days=365)
    today = datetime.now()
    # --- Проценты ---
    total_seconds = (end_date - start_date).total_seconds()
    passed_seconds = (today - start_date).total_seconds()
    percent = (passed_seconds / total_seconds) * 100
    percent_bar = "🔵" * int(percent // 10) + "⚪️" * (10 - int(percent // 10))

    # --- Недели ---
    total_weeks = 52
    passed_weeks_exact = (today - start_date).days / 7
    passed_weeks = int(passed_weeks_exact)
    remaining_weeks = total_weeks - passed_weeks
    weeks_bar = "🔵" * min(7, int((passed_weeks / total_weeks) * 7)) + "⚪️" * (
                7 - min(7, int((passed_weeks / total_weeks) * 7)))

    # --- Месяцы ---
    total_months = 12
    passed_months_exact = (today - start_date).days / 30
    passed_months = int(passed_months_exact)
    remaining_months = total_months - passed_months
    months_bar = "🔵" * min(12, int((passed_months / total_months) * 12)) + "⚪️" * (
                12 - min(12, int((passed_months / total_months) * 12)))
    hidden = user_dates[chat_id].get('hidden_dates', set())

    # --- Информация ---
    if query.data == 'info':
        today = datetime.now()
        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']

        # --- Прошло и осталось ---
        passed = today - start_date
        remaining = end_date - today
        passed_sec = int(passed.total_seconds())
        remaining_sec = int(remaining.total_seconds())
        passed_days = passed_sec // 86400
        passed_hours = (passed_sec % 86400) // 3600
        passed_minutes = (passed_sec % 3600) // 60
        passed_seconds = passed_sec % 60
        remaining_days = remaining_sec // 86400
        remaining_hours = (remaining_sec % 86400) // 3600
        remaining_minutes = (remaining_sec % 3600) // 60
        remaining_seconds = remaining_sec % 60

        # --- Ближайшее событие ---
        start_date_calc = end_date - timedelta(days=365)
        upcoming_event = None
        min_days = None
        hidden = user_dates[chat_id].get('hidden_dates', set())

        for day, event in sorted(army_dates.items()):
            if event in hidden:
                continue
            event_date = start_date_calc + timedelta(days=int(day))
            days_until_event = (event_date - today).days
            if days_until_event >= 0:
                upcoming_event = f"{event} — {'завтра' if days_until_event == 0 else f'через {days_until_event} дн'} ({event_date.strftime('%d.%m.%Y')})"
                min_days = days_until_event
                break

        for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
            if name in hidden:
                continue
            days_until_event = (dt - today).days
            if days_until_event >= 0 and (min_days is None or days_until_event < min_days):
                upcoming_event = f"{name} — {'завтра' if days_until_event == 0 else f'через {days_until_event} дн'} ({dt.strftime('%d.%m.%Y')})"
                min_days = days_until_event

        if not upcoming_event:
            upcoming_event = "Все события уже прошли."

        # --- Кнопки выбора вида прогресса ---
        keyboard = [
            [InlineKeyboardButton("Проценты", callback_data='info_percent')],
            [InlineKeyboardButton("Недели", callback_data='info_weeks')],
            [InlineKeyboardButton("Месяцы", callback_data='info_months')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # --- Сообщение с информацией ---
        text = (
            f"📅 Сегодня: {today.strftime('%d.%m.%Y')}\n"
            f"Ближайшее событие: {upcoming_event}\n\n"
            f"Прошло: {passed_days} дн, {passed_hours} ч, {passed_minutes} мин, {passed_seconds} сек\n"
            f"Осталось: {remaining_days} дн, {remaining_hours} ч, {remaining_minutes} мин, {remaining_seconds} сек\n\n"
            "Выберите вид прогресса:"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    # --- Обработка нажатий на подменю информации ---
    elif query.data == 'info_percent':
        today = datetime.now()
        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']

        total_seconds = (end_date - start_date).total_seconds()
        passed_seconds = (today - start_date).total_seconds()
        percent = (passed_seconds / total_seconds) * 100
        percent_bar = "🔵" * int(percent // 10) + "⚪" * (10 - int(percent // 10))

        keyboard = [[InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(f"Прогресс службы: {percent:.6f}%\n{percent_bar}", reply_markup=reply_markup)

    elif query.data == 'info_weeks':
        today = datetime.now()
        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']

        passed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        total_weeks = 52
        passed_weeks = int(passed_days / 7)
        remaining_weeks = total_weeks - passed_weeks
        weeks_bar = "🔵" * min(7, int((passed_weeks / total_weeks) * 7)) + "⚪" * (
                    7 - min(7, int((passed_weeks / total_weeks) * 7)))

        keyboard = [[InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"Прошло: {passed_weeks} недель, {passed_days - passed_weeks * 7} дн\n"
            f"Осталось: {remaining_weeks} недель, {remaining_days % 7} дн\n"
            f"{weeks_bar}"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    elif query.data == 'info_months':
        today = datetime.now()
        start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)
        end_date = user_dates[chat_id]['end_date']

        passed_days = (today - start_date).days
        remaining_days = (end_date - today).days
        total_months = 12
        passed_months = int(passed_days / 30)
        remaining_months = total_months - passed_months
        months_bar = "🔵" * min(12, int((passed_months / total_months) * 12)) + "⚪" * (
                    12 - min(12, int((passed_months / total_months) * 12)))

        keyboard = [[InlineKeyboardButton("Назад", callback_data='info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"Прошло: {passed_months} месяцев, {passed_days - passed_months * 30} дн\n"
            f"Осталось: {remaining_months} месяцев, {remaining_days % 30} дн\n"
            f"{months_bar}"
        )
        query.edit_message_text(text, reply_markup=reply_markup)

    # --- Все даты с двумя кнопками ---
    elif query.data == 'all':
        try:
            chat_id = str(query.message.chat_id)
            today = datetime.now()
            hidden = user_dates[chat_id].get('hidden_dates', set())

            all_events = []
            start_date = user_dates[chat_id]['end_date'] - timedelta(days=365)

            # --- Армейские даты ---
            for day, event in sorted(army_dates.items()):
                if event in hidden:
                    continue
                event_date = start_date + timedelta(days=int(day))
                if event_date < today:
                    event_text = f"✅ {event}"  # прошедшее событие с галочкой
                else:
                    event_text = event  # будущие события без галочки
                all_events.append((event_date, f"{event_date.strftime('%d.%m.%Y')} — {event}"))

            # --- Пользовательские даты ---
            for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
                if name in hidden:
                    continue
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
                [InlineKeyboardButton("Добавить свою дату", callback_data='add_custom')],
                [InlineKeyboardButton("Удалить дату", callback_data='delete_custom')],
                [InlineKeyboardButton("Назад", callback_data='back')]
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
        keyboard = []
        for day, event in sorted(army_dates.items()):
            event_date = start_date + timedelta(days=int(day))
            keyboard.append([InlineKeyboardButton(f"{event} ({event_date.strftime('%d.%m.%Y')})", callback_data=f"del|army|{day}")])
        for name, dt in user_dates[chat_id].get('custom_dates', {}).items():
            keyboard.append([InlineKeyboardButton(f"{name} ({dt.strftime('%d.%m.%Y')})", callback_data=f"del|custom|{name}")])
        keyboard.append([InlineKeyboardButton("Назад", callback_data='all')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Выберите дату для удаления:", reply_markup=reply_markup)

        # --- Удаление конкретной даты ---
    elif query.data.startswith('del|'):
        _, typ, key = query.data.split('|', 2)
        if 'hidden_dates' not in user_dates[chat_id]:
            user_dates[chat_id]['hidden_dates'] = set()
        if typ == 'custom':
            user_dates[chat_id]['hidden_dates'].add(key)
        elif typ == 'army':
            user_dates[chat_id]['hidden_dates'].add(army_dates[int(key)])
        save_users(user_dates)
        query.answer("✅ Дата скрыта")
        query.edit_message_text("Обновите список дат", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Назад", callback_data='all')]]))

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


# --- Основная функция ---
def main():
    bot_token = os.getenv("BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_date))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()



