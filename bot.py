import os
# Импортируем особую версию requests, которая умеет косить под браузер
from curl_cffi import requests as requests_cffi
import requests
import telebot
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')

# threaded=False — критично для Vercel
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_json_direct(ally_code):
    try:
        url = f"https://swgoh.gg/api/player/{ally_code}/"
        
        # impersonate="chrome120" — заставляет библиотеку полностью скопировать
        # сетевой отпечаток (JA3/TLS) реального браузера Chrome.
        response = requests_cffi.get(url, impersonate="chrome120", timeout=9)
        
        if response.status_code == 200:
            try:
                res_json = response.json()
                return res_json, "Успешно! Cloudflare пройден напрямую с Vercel."
            except ValueError:
                bad_text = response.text[:200].replace('<', '&lt;').replace('>', '&gt;')
                return None, f"⚠️ Сервер ответил не JSON!\nОтвет:\n{bad_text}"
                
        return None, f"🛑 Ошибка сайта!\nСтатус-код: {response.status_code}\nОтвет: {response.text[:100]}"
        
    except Exception as e:
        return None, f"Критическая ошибка curl_cffi:\n{str(e)}"

@app.route('/')
def index():
    # Используем обычный requests для телеграма, там блокировок нет
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://swgoh-packs.vercel.app/{TOKEN}"
    try:
        res = requests.get(webhook_url, timeout=5)
        return f"Статус вебхука: {res.text}"
    except Exception as e:
        return f"Ошибка установки вебхука: {e}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне код союзника, я достану инфу напрямую через curl_cffi.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    clean_text = message.text.strip().replace('-', '').replace(' ', '')
    
    if clean_text.isdigit() and len(clean_text) == 9:
        bot.send_message(message.chat.id, "⏳ Маскируюсь под Chrome и иду на swgoh.gg...")
        
        data, debug_info = get_json_direct(clean_text)
        
        bot.send_message(message.chat.id, f"⚙️ Лог отладки:\n{debug_info}")
        
        if data:
            player_data = data.get('data', {})
            name = player_data.get('name', 'Неизвестный')
            gp = player_data.get('galactic_power', 0)
            
            bot.send_message(
                message.chat.id, 
                f"🏆 **Данные игрока**\n\nНик: `{name}`\nГалактическая мощь: `{gp:,}`"
            )
        else:
            bot.send_message(message.chat.id, "❌ Не удалось распарсить данные.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введи корректный код союзника (9 цифр).")
