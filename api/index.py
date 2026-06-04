import os
from flask import Flask, request
import telebot

# Если curl_cffi всё еще нужен для твоих внутренних парсеров/запросов — раскомментируй:
# from curl_cffi import requests as requests_cffi

app = Flask(__name__)

# Токен берем из переменных окружения Vercel (в панели управления проектом)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Главная страница (просто проверить, что Flask жив)
@app.route("/", methods=["GET"])
def index():
    return "Бот успешно запущен и слушает вебхуки!", 200

# Эндпоинт, куда Telegram будет присылать сообщения
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

# ТВОИ ХЭНДЛЕРЫ И ЛОГИКА БОТА:
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Йоу! Теперь я работаю на Serverless-вебхуках и не отвалюсь через 15 секунд. 🚀")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")
