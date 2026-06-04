import os
import requests
import telebot
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def get_json(ally_code):
    try:
        url = f"https://swgoh.gg/api/player/{ally_code}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://swgoh.gg/'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            return response.json(), f"✅ Успешно! swgoh.gg ответил кодом 200."
        
        # Если код не 200, забираем кусок ответа для отладки
        debug_text = response.text[:200].replace('<', '&lt;').replace('>', '&gt;')
        return None, f"❌ Ошибка swgoh.gg!\nСтатус-код: {response.status_code}\nОтвет сервера: {debug_text}"
        
    except Exception as e:
        return None, f"💥 Критическая ошибка сети/кода:\n{str(e)}"

@app.route('/')
def index():
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://swgoh-packs.vercel.app/{TOKEN}"
    try:
        res = requests.get(webhook_url, timeout=10)
        return f"Ответ от Telegram: {res.text}"
    except Exception as e:
        return f"Ошибка при отправке запроса: {e}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне код союзника (9 цифр), чтобы проверить склад.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip().replace('-', '')
    
    if text.isdigit() and len(text) == 9:
        bot.send_message(message.chat.id, "🔍 Проверяю код союзника, отправляю запрос на swgoh.gg...")
        
        # Получаем и данные, и строку отладки
        data, debug_info = get_json(text)
        
        # Сразу выплёскиваем отладку в чат
        bot.send_message(message.chat.id, f"⚙️ **Лог отладки:**\n{debug_info}", parse_mode="HTML")
        
        if data:
            player_data = data.get('data', {})
            name = player_data.get('name', 'Неизвестный')
            gp = player_data.get('galactic_power', 0)
            bot.send_message(message.chat.id, f"🏆 **Данные игрока:**\nНик: {name}\nГМ: {gp:,}")
        else:
            bot.send_message(message.chat.id, "⚠️ Данные получить не удалось. Посмотри лог отладки выше, там написана причина.")
    else:
        bot.send_message(message.chat.id, "Введи корректный код союзника (9 цифр).")
