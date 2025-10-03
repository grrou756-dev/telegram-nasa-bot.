import os
import requests
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv()
NASA_API_KEY = os.getenv("NASA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 📏 Описание размера
def size_description(diameter):
    if diameter < 5:
        return "как легковая машина 🚗"
    elif diameter < 20:
        return "как автобус 🚌"
    elif diameter < 50:
        return "как многоэтажный дом 🏢"
    elif diameter < 100:
        return "как футбольное поле ⚽"
    elif diameter < 300:
        return "как несколько футбольных полей 🏟️"
    else:
        return "гигантский астероид 🌌"

# 📡 Получение астероидов за дату/период
def get_asteroids(start_date, end_date=None, dangerous_only=False, min_size=None, max_size=None):
    if end_date is None:
        end_date = start_date
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={NASA_API_KEY}"
    data = requests.get(url).json()
    asteroids = []
    for day in data["near_earth_objects"]:
        for a in data["near_earth_objects"][day]:
            diameter_min = a["estimated_diameter"]["meters"]["estimated_diameter_min"]
            diameter_max = a["estimated_diameter"]["meters"]["estimated_diameter_max"]
            avg_diameter = (diameter_min + diameter_max) / 2

            # фильтрация
            if dangerous_only and not a["is_potentially_hazardous_asteroid"]:
                continue
            if min_size and avg_diameter < min_size:
                continue
            if max_size and avg_diameter > max_size:
                continue

            asteroids.append(a)
    return asteroids

# 🪐 Форматирование сообщения
def asteroid_info(a):
    name = a["name"]
    diameter_min = a["estimated_diameter"]["meters"]["estimated_diameter_min"]
    diameter_max = a["estimated_diameter"]["meters"]["estimated_diameter_max"]
    avg_diameter = (diameter_min + diameter_max) / 2

    speed = a["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]
    distance = a["close_approach_data"][0]["miss_distance"]["kilometers"]

    return (
        f"☄️ {name}\n"
        f"📏 Размер: {avg_diameter:.1f} м ({size_description(avg_diameter)})\n"
        f"🚀 Скорость: {float(speed):,.0f} км/ч\n"
        f"🌍 Расстояние: {float(distance):,.0f} км\n"
        f"⚠️ Опасный: {'Да' if a['is_potentially_hazardous_asteroid'] else 'Нет'}\n"
    )

# === КОМАНДЫ ===

def today(update: Update, context: CallbackContext):
    date = datetime.date.today().strftime("%Y-%m-%d")
    asteroids = get_asteroids(date)
    text = "\n".join([asteroid_info(a) for a in asteroids[:5]]) or "Нет данных"
    update.message.reply_text(f"Астероиды за {date}:\n\n{text}")

def tomorrow(update: Update, context: CallbackContext):
    date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    asteroids = get_asteroids(date)
    text = "\n".join([asteroid_info(a) for a in asteroids[:5]]) or "Нет данных"
    update.message.reply_text(f"Астероиды за {date}:\n\n{text}")

def yesterday(update: Update, context: CallbackContext):
    date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    asteroids = get_asteroids(date)
    text = "\n".join([asteroid_info(a) for a in asteroids[:5]]) or "Нет данных"
    update.message.reply_text(f"Астероиды за {date}:\n\n{text}")

def danger(update: Update, context: CallbackContext):
    date = datetime.date.today().strftime("%Y-%m-%d")
    asteroids = get_asteroids(date, dangerous_only=True)
    text = "\n".join([asteroid_info(a) for a in asteroids]) or "🚀 Опасных астероидов нет"
    update.message.reply_text(f"🚨 Опасные астероиды {date}:\n\n{text}")

def big(update: Update, context: CallbackContext):
    date = datetime.date.today().strftime("%Y-%m-%d")
    asteroids = get_asteroids(date, min_size=100)
    text = "\n".join([asteroid_info(a) for a in asteroids]) or "Крупных астероидов нет"
    update.message.reply_text(f"🪐 Крупные астероиды {date}:\n\n{text}")

def small(update: Update, context: CallbackContext):
    date = datetime.date.today().strftime("%Y-%m-%d")
    asteroids = get_asteroids(date, max_size=20)
    text = "\n".join([asteroid_info(a) for a in asteroids]) or "Маленьких астероидов нет"
    update.message.reply_text(f"🌑 Маленькие астероиды {date}:\n\n{text}")

def week(update: Update, context: CallbackContext):
    start = datetime.date.today()
    end = start + datetime.timedelta(days=7)
    asteroids = get_asteroids(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    text = "\n".join([asteroid_info(a) for a in asteroids[:10]]) or "Нет данных"
    update.message.reply_text(f"📅 Астероиды на неделю:\n\n{text}")

def apod(update: Update, context: CallbackContext):
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    data = requests.get(url).json()
    update.message.reply_photo(data["url"], caption=f"🌌 {data['title']}\n\n{data['explanation']}")

def chart(update: Update, context: CallbackContext):
    date = datetime.date.today().strftime("%Y-%m-%d")
    asteroids = get_asteroids(date)

    if not asteroids:
        update.message.reply_text("Нет данных для построения графика")
        return

    names = [a["name"] for a in asteroids]
    distances = [float(a["close_approach_data"][0]["miss_distance"]["kilometers"]) for a in asteroids]

    plt.figure(figsize=(8, 5))
    plt.barh(names, distances)
    plt.xlabel("Расстояние до Земли (км)")
    plt.title(f"Астероиды {date}")
    plt.tight_layout()

    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    plt.close()
    update.message.reply_photo(bio)

# === СТАРТ ===
def start(update: Update, context: CallbackContext):
    keyboard = [
        ["📅 Сегодня", "⏭ Завтра"],
        ["⏮ Вчера", "⚠️ Опасные"],
        ["🪐 Крупные", "🌑 Маленькие"],
        ["📊 График", "🌌 Фото дня"],
        ["📆 Неделя"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Привет! Я бот NASA 🚀\nВыбери команду:", reply_markup=reply_markup)

# === Хэндлер кнопок ===
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "📅 Сегодня":
        today(update, context)
    elif text == "⏭ Завтра":
        tomorrow(update, context)
    elif text == "⏮ Вчера":
        yesterday(update, context)
    elif text == "⚠️ Опасные":
        danger(update, context)
    elif text == "🪐 Крупные":
        big(update, context)
    elif text == "🌑 Маленькие":
        small(update, context)
    elif text == "📆 Неделя":
        week(update, context)
    elif text == "🌌 Фото дня":
        apod(update, context)
    elif text == "📊 График":
        chart(update, context)
    else:
        update.message.reply_text("Не понял 🤔")

# === Запуск бота ===
def main():
    print("🚀 Бот запущен...")
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("today", today))
    dp.add_handler(CommandHandler("tomorrow", tomorrow))
    dp.add_handler(CommandHandler("yesterday", yesterday))
    dp.add_handler(CommandHandler("danger", danger))
    dp.add_handler(CommandHandler("big", big))
    dp.add_handler(CommandHandler("small", small))
    dp.add_handler(CommandHandler("week", week))
    dp.add_handler(CommandHandler("apod", apod))
    dp.add_handler(CommandHandler("chart", chart))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
