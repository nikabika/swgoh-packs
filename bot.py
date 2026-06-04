import os
import requests
import telebot
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')

# threaded=False — критично для Vercel, чтобы микро-лямбда не засыпала раньше времени
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Твоя НОВАЯ ссылка на Google Apps Script
PROXY_URL = "https://script.google.com/macros/s/AKfycbzthYdqRVx3k_Jd5uFybY-OffTup5Qu4kYeG-4dDSvHepMnrCsvpPU_XS9etscixK-y/exec"

def get_json_via_proxy(ally_code):
    try:
        # Передаем код союзника в параметре ?code=...
        payload = {'code': ally_code}
        
        # Google всегда делает 302 редирект, requests обработает его сам.
        # Ставим таймаут 8 секунд, чтобы уложиться в лимиты бесплатного Vercel (10 сек).
        response = requests.get(PROXY_URL, params=payload, timeout=8)
        
        if response.status_code == 200:
            res_json = response.json()
            
            # Проверяем, не вернул ли сам гугл-скрипт ошибку (блок catch в JS)
            if isinstance(res_json, dict) and 'error' in res_json:
                return None, f"Ошибка внутри Google Script:\n{res_json['error']}"
                
            return res_json, "Успешно! Данные получены через Google-прокси."
        
        return None, f"Ошибка макроса Google!\nСтатус-код: {response.status_code}\nОтвет: {response.text[:100]}"
        
    except Exception as e:
        return None, f"Критическая ошибка при вызове прокси:\n{str(e)}"

@app.route('/')
def index():
    # Авто-сетап вебхука при заходе на главную страницу
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
        # Обрабатываем синхронно в основном потоке Flask
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Forbidden', 403

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне код союзника (9 цифр), я достану инфу из swgoh.gg через прокси.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Очищаем текст от дефисов и пробелов
    clean_text = message.text.strip().replace('-', '').replace(' ', '')
    
    if clean_text.isdigit() and len(clean_text) == 9:
        bot.send_message(message.chat.id, "⏳ Стучусь в Google Прокси...")
        
        data, debug_info = get_json_via_proxy(clean_text)
        
        # Выводим отладочный лог в чат
        bot.send_message(message.chat.id, f"⚙️ Лог отладки:\n{debug_info}")
        
        if data:
            # Парсим стандартный JSON от swgoh.gg
            player_data = data.get('data', {})
            name = player_data.get('name', 'Неизвестный')
            gp = player_data.get('galactic_power', 0)
            
            bot.send_message(
                message.chat.id, 
                f"🏆 **Данные игрока**\n\nНик: `{name}`\nГалактическая мощь: `{gp:,}`"
            )
        else:
            bot.send_message(message.chat.id, "❌ Не удалось прочитать JSON. Проверь лог отладки выше.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введи корректный код союзника (9 цифр без букв).")
