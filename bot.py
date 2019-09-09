import telebot
import datetime
import psycopg2
import time
import os

token = os.environ['token']
bot = telebot.TeleBot(token)

conn = psycopg2.connect(dbname=os.environ['dbname'],
                        user=os.environ['user'],
                        password=os.environ['password'],
                        host=os.environ['host'],
                        port=os.environ['port'])
cursor = conn.cursor()


def check_date(date):
    try:
        valid_date = time.strptime(str(date), "%Y-%m-%d-%H.%M")
        return True
    except ValueError:
        return False


def bot_insert_db(user_id_, note_, time_):
    values1 = ({'id': int(user_id_)})
    values2 = ({'id': int(user_id_), 'note': note_, 'time_': time_})
    id_query = 'SELECT * FROM bot.user'
    cursor.execute(id_query)
    results = cursor.fetchall()
    f = True
    for item in results:
        if item[0] == user_id_:
            f = False
    if f:
        cursor.execute("INSERT INTO bot.user (User_id) VALUES(%(id)s)", values1)

    cursor.execute("INSERT INTO bot.reminder (User_id, reminder_text, time) VALUES(%(id)s,%(note)s, %(time_)s)",
                   values2)

    conn.commit()


def bot_delete_db(user_id_, note_, time_):
    cursor.execute(
        "DELETE FROM bot.reminder WHERE User_id = %s AND Reminder_text = %s AND time= %s", (user_id_, note_, time_))
    conn.commit()


def bot_send_message():
    id_query = 'SELECT DISTINCT * FROM bot.reminder'
    cursor.execute(id_query)
    results = cursor.fetchall()
    for item in results:
        bot.send_message(item[0], "Напомню тебе " + item[1] + ' ' + item[2].strftime("%Y-%m-%d-%H.%M"))
        break

    for item in results:
        print(item)
        date = datetime.datetime.now()
        while True:
            if date < item[2]:
                date = datetime.datetime.now()
            else:
                if not item[3]:
                    bot.send_message(item[0], 'Нужно ' + item[1])
                    bot_delete_db(item[0], item[1], item[2])
                    cursor.execute(
                        "UPDATE bot.reminder SET flag=True WHERE User_id = %s AND Reminder_text = %s AND time= %s",
                        (item[0], item[1], item[2]))
                    conn.commit()
                    break
                else:
                    bot_delete_db(item[0], item[1], item[2])
                    break


def get_note_date(time_):
    h = 0
    m = 0
    s = 0
    time_text = time_.split()
    cur_number = 0
    for time_word in time_text:
        if time_word.isnumeric():
            cur_number = int(time_word)
        else:
            if time_word.startswith('час'):
                h += cur_number
            elif time_word.startswith('мин'):
                m += cur_number
            else:
                s += cur_number
    return datetime.timedelta(hours=h, minutes=m, seconds=s)


def set_remind_after_reminder(message):
    if "через" in message.text:
        user_text = message.text
        words = user_text.split()
        note_words = []
        time_words = []
        is_it_time = False
        for word in words:
            word = word.lower()
            if (word == 'напомни' or word == 'мне') and not is_it_time:
                pass
            elif word != 'через' and not is_it_time:
                note_words.append(word)
            else:
                is_it_time = True
                if word != 'через':
                    time_words.append(word)

        note = " ".join(note_words)
        time_ = " ".join(time_words)
        note_date = datetime.datetime.now() + get_note_date(time_)
        bot_insert_db(message.chat.id, note, note_date)
        bot_send_message()
        print("Пришел текст")
    else:
        bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')


def set_after_remind_reminder(message):
    if "напомни" in message.text:
        user_text = message.text
        words = user_text.split()
        note_words = []
        time_words = []
        is_not_time = True
        for word in words:
            word = word.lower()
            if (word == 'мне') and not is_not_time:
                pass
            elif word != 'через' and not is_not_time:
                note_words.append(word)
            else:
                if word == 'через':
                    pass
                if word == 'напомни':
                    is_not_time = False
                    pass
                else:
                    time_words.append(word)

        note = " ".join(note_words)
        time_ = " ".join(time_words)
        note_date = datetime.datetime.now() + get_note_date(time_)
        bot_insert_db(message.chat.id, note, note_date)
        bot_send_message()
        print("Пришел текст")
    else:
        bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')


def set_date_reminder(message):
    user_text = message.text
    words = user_text.split()
    valid_date = time.strptime(words[0], "%Y-%m-%d-%H.%M")
    time_ = datetime.datetime(year=valid_date.tm_year, month=valid_date.tm_mon, day=valid_date.tm_mday,
                              hour=valid_date.tm_hour, minute=valid_date.tm_min, second=0)
    note_words = []
    for word in words:
        word = word.lower()
        if word == words[0]:
            pass
        elif word != 'напомни' and word != 'мне':
            note_words.append(word)

    note = " ".join(note_words)
    bot_insert_db(message.chat.id, note, time_)
    bot_send_message()
    print("Пришел текст")


def set_today_reminder(message):
    if "напомни" in message.text:
        user_text = message.text
        words = user_text.split()
        note_words = []
        time_words = []
        is_not_time = True
        for word in words:
            word = word.lower()
            if (word == 'мне') and not is_not_time:
                pass
            elif word != 'сегодня' and not is_not_time:
                note_words.append(word)
            else:
                if word == 'сегодня' or word == 'в':
                    pass
                if word == 'напомни':
                    is_not_time = False
                    pass
                else:
                    time_words.append(word)

        note = " ".join(note_words)
        time_ = " ".join(time_words)

        note_date = datetime.datetime.now() - datetime.timedelta(hours=datetime.datetime.now().hour,
                                                                 minutes=datetime.datetime.now().minute,
                                                                 seconds=datetime.datetime.now().second
                                                                 ) + get_note_date(
            time_)
        bot_insert_db(message.chat.id, note, note_date)
        bot_send_message()
        print("Пришел текст")
    else:
        bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')


def set_weekday_reminder(message):
    if "напомни мне " in message.text:
        user_text = message.text
        parts = user_text.partition('напомни мне ')
        i = -1
        h = 0
        m = 0
        s = 0
        cur_number = 0
        weeks = {
            "пон": 0,
            "вт": 1,
            "ср": 2,
            "чет": 3,
            "пят": 4,
            "суб": 5,
            "вос": 6
        }
        for word in parts[0].split():
            word = word.lower()
            if word == 'в' or word == 'во':
                pass
            else:
                for key, value in weeks.items():
                    if word.startswith(key):
                        i = value
                    elif word.isnumeric():
                        cur_number = int(word)
                    elif word.startswith('час'):
                        h = cur_number
                    elif word.startswith('мин'):
                        m = cur_number
                    elif word.startswith('сек'):
                        s = cur_number
        if i == -1:
            bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')

        else:
            delta = datetime.timedelta(days=abs((7 + i - datetime.datetime.today().weekday()) % 7), hours=h, minutes=m,
                                       seconds=s)
            note_date = datetime.datetime.now() - datetime.timedelta(hours=datetime.datetime.now().hour,
                                                                     minutes=datetime.datetime.now().minute,
                                                                     seconds=datetime.datetime.now().second) + delta
            bot_insert_db(message.chat.id, str(parts[2]), note_date)
            bot_send_message()
            print("Пришел текст")
    else:
        bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')


@bot.message_handler(commands=['start'])
def handle_text(message):
    bot.send_message(message.chat.id, "Привет")
    print("Пришла комманда старт")


@bot.message_handler(commands=['help'])
def handle_text(message):
    bot.send_message(message.chat.id,
                     "У меня есть комманды:\n"
                     "1) Напомни мне <ваше действие> через "
                     "<целое число> часов <целое число> минут <целое число> секунд\n"
                     "2) Через <целое число> часов <целое число> минут <целое число> секунд "
                     "напомни мне <ваше действие>\n"
                     "3) <Ваша дата в формате YYYY-MM-DD-HH.MM> "
                     "напомни мне <ваше действие>\n"
                     "4) Сегодня в <целое число> часов <целое число> минут <целое число> секунд "
                     "напомни мне <ваше действие>\n"
                     "5) В <день недели> В <целое число> часов <целое число> минут <целое число> секунд "
                     "напомни мне <ваше действие>\n"
                     "*Полностью заполнять всё не нужно, достаточно хотя бы одно поле\n"
                     "**Будьте внимательны: Время бота по UTC"
                     )
    print("Пришла комманда помощь")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_text = message.text
    user_text = user_text.lower()
    if user_text.startswith('напомни'):
        set_remind_after_reminder(message)
    elif user_text.startswith('через'):
        set_after_remind_reminder(message)
    elif check_date(user_text.partition(' напомни')[0]):
        set_date_reminder(message)
    elif user_text.startswith('сегодня'):
        set_today_reminder(message)
    elif user_text.startswith('в'):
        set_weekday_reminder(message)
    else:
        bot.send_message(message.chat.id, 'Не знаю, что делать, попробуйте ещё раз')


bot.polling(none_stop=True, interval=0)
cursor.close()
conn.close()
