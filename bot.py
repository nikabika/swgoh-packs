import os
import requests
import telebot
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')
HELP_TOKEN = os.environ.get('HELP_TOKEN')

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def parse_swgoh_data(ally_code):
    try:
        # Стучимся напрямую в официальный API swgoh.help
        url = "https://api.swgoh.help/swgoh/player"
        headers = {
            "Authorization": f"Bearer {HELP_TOKEN}",
            "Content-Type": "application/json"
        }
        # Передаем код союзника в массив (их API требует именно так)
        payload = {
            "allycodes": [int(ally_code)],
            "language": "rus",
            "enums": True
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, list) and len(res_json) > 0:
                return res_json[0], "Парсинг успешен!"
            return None, "Игрок с таким кодом не найден в базе swgoh.help."
            
        return None, f"Ошибка API! Статус: {response.status_code}. Ответ: {response.text[:50]}"
        
    except Exception as e:
        return None, f"Критическая ошибка парсера:\n{str(e)}"

@app.route('/')
def index():
    # Авто-сетап вебхука при переходе на домен бота
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{request.host}/{TOKEN}"
    try:
        res = requests.get(webhook_url, timeout=5)
        return f"Вебхук настроен! Статус: {res.text}"
    except Exception as e:
        return f"Ошибка при установке вебхука: {e}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне 9-значный код союзника, и я спаршу данные его профиля.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Убираем пробелы и дефисы, если юзер ввёл код как "123-456-789"
    clean_text = message.text.strip().replace('-', '').replace(' ', '')
    
    if clean_text.isdigit() and len(clean_text) == 9:
        bot.send_message(message.chat.id, "⏳ Паршу данные из swgoh.help...")
        
        player_data, debug_log = parse_swgoh_data(clean_text)
        
        if player_data:
            # Вытягиваем нужные поля из спарсенного JSON
            name = player_data.get('name', 'Неизвестный')
            gp = player_data.get('gp', 0)
            level = player_data.get('level', 0)
            
            bot.send_message(
                message.chat.id, 
                f"🏆 **Результат парсинга:**\n\n"
                f"👤 Ник: `{name}`\n"
                f"⭐ Уровень: `{level}`\n"
                f"💪 Галактическая мощь: `{gp:,}`\n\n"
                f"⚙️ Лог: {debug_log}"
            )
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка парсинга.\nЛог: {debug_log}")
    else:
        bot.send_message(message.chat.id, "Введи нормальный код союзника (9 цифр).")
