import telebot
import os
import json
import time
from curl_cffi import requests
from curl_cffi.requests import BrowserType

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Сессия с постоянными куками
session = None

def get_session():
    global session
    if session is None:
        # Создаём сессию с полной имитацией браузера
        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Google Chrome";v="120", "Not?A_Brand";v="8"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
        })
    return session

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🎮 **SWGOH Player Bot**\n\n"
        "Команда: `/player 431294714`\n"
        "Получает данные с обходом Cloudflare",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['player'])
def get_player_info(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Укажите код: `/player 431294714`", parse_mode='Markdown')
        return
    
    ally_code = parts[1]
    
    if not ally_code.isdigit():
        bot.reply_to(message, "❌ Код должен состоять из цифр")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Пробуем разные подходы
    result = fetch_with_fallback(ally_code)
    
    if result["success"]:
        data = result["data"]
        response_text = (
            f"🎮 **{data.get('name', '?')}**\n"
            f"📊 Уровень: {data.get('level', '?')}\n"
            f"🔢 Код: {data.get('ally_code', ally_code)}\n"
            f"🏛️ Гильдия: {data.get('guild_name', '-')}"
        )
        bot.reply_to(message, response_text, parse_mode='Markdown')
    else:
        bot.reply_to(
            message,
            f"❌ Ошибка {result['error']}\n\n"
            f"💡 Профиль: https://swgoh.gg/p/{ally_code}/",
            disable_web_page_preview=True
        )

def fetch_with_fallback(ally_code):
    """Пробуем разные браузеры и подходы"""
    
    url = f"https://swgoh.gg/api/player/{ally_code}"
    
    # Список имитаций для перебора
    impersonates = [
        "chrome120",
        "chrome110", 
        "safari15_5",
        "edge101",
        "firefox110",
    ]
    
    for impersonate in impersonates:
        try:
            print(f"Пробуем {impersonate}...")
            
            response = requests.get(
                url,
                impersonate=impersonate,
                timeout=45,
                verify=True,
            )
            
            print(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            elif response.status_code == 403:
                continue  # Пробуем следующий браузер
            elif response.status_code == 404:
                return {"success": False, "error": "Игрок не найден"}
            else:
                continue
                
        except Exception as e:
            print(f"Ошибка с {impersonate}: {e}")
            continue
    
    # Если всё перепробовали
    return {"success": False, "error": "Cloudflare блокирует (403)"}

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Нет токена!")
        exit(1)
    
    print("🚀 Бот запущен с усиленным обходом")
    print("🔄 Будут перебраны 5 имитаций браузеров")
    
    try:
        bot.infinity_polling(timeout=60)
    except Exception as e:
        print(f"Ошибка: {e}")
