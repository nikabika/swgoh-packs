import os
import time
import telebot
from curl_cffi import requests as requests_cffi

# Забираем токен из переменных окружения хостинга
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

def get_json_direct(ally_code):
    try:
        url = f"https://swgoh.gg/api/player/{ally_code}/"
        
        # Полная имитация TLS-отпечатка Chrome 120
        response = requests_cffi.get(url, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            try:
                return response.json(), "Успешно! Сайт пробит напрямую."
            except ValueError:
                bad_text = response.text[:150].replace('<', '&lt;').replace('>', '&gt;')
                return None, f"⚠️ Ответ не JSON:\n{bad_text}"
                
        return None, f"🛑 Ошибка сайта! Статус: {response.status_code}"
        
    except Exception as e:
        return None, f"Ошибка curl_cffi: {str(e)}"

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я работаю напрямую. Отправь мне 9 цифр кода союзника.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    clean_text = message.text.strip().replace('-', '').replace(' ', '')
    
    if clean_text.isdigit() and len(clean_text) == 9:
        bot.send_message(message.chat.id, "⏳ Пробиваю защиту swgoh.gg...")
        
        data, debug_info = get_json_direct(clean_text)
        
        bot.send_message(message.chat.id, f"⚙️ Лог:\n{debug_info}")
        
        if data:
            player_data = data.get('data', {})
            name = player_data.get('name', 'Неизвестный')
            gp = player_data.get('galactic_power', 0)
            
            bot.send_message(
                message.chat.id, 
                f"🏆 **Данные игрока**\n\nНик: `{name}`\nГМ: `{gp:,}`"
            )
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить данные.")
    else:
        bot.send_message(message.chat.id, "Введи корректный код (9 цифр).")

# Бесконечный цикл опроса Telegram (без вебхуков)
if __name__ == '__main__':
    print("Бот успешно запущен в режиме Long Polling...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка паллинга, перезапуск через 5 сек: {e}")
            time.sleep(5)
