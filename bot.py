import telebot
import os
from curl_cffi import requests

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Только Safari, разные версии и платформы
SAFARI_VARIANTS = [
    "safari15_5",   # Safari 15.5 на macOS Monterey
    "safari15_3",   # Safari 15.3 на macOS
    "safari17_0",   # Safari 17.0 на macOS Sonoma (самый новый)
    "safari_ios",   # Safari на iOS (если поддерживается)
    "safari15_2",   # Safari 15.2
]

@bot.message_handler(commands=['player'])
def get_player(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажите код: /player 431294714")
        return
    
    ally_code = parts[1]
    url = f"https://swgoh.gg/api/player/{ally_code}"
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    for safari_version in SAFARI_VARIANTS:
        try:
            print(f"Пробуем Safari: {safari_version}")
            
            response = requests.get(
                url,
                impersonate=safari_version,
                timeout=45,
                headers={
                    'User-Agent': get_safari_ua(safari_version),
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
            )
            
            print(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                bot.reply_to(
                    message,
                    f"🎮 {data.get('name')}\n📊 Уровень: {data.get('level')}\n\n✅ Обход через {safari_version}"
                )
                return
                
        except Exception as e:
            print(f"Ошибка {safari_version}: {e}")
            continue
    
    bot.reply_to(message, "❌ Все варианты Safari заблокированы")

def get_safari_ua(version):
    """User-Agent для разных версий Safari"""
    ua_map = {
        "safari15_5": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "safari17_0": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "safari15_3": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
    }
    return ua_map.get(version, ua_map["safari15_5"])

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Отправь /player 431294714")

if __name__ == "__main__":
    print("🚀 Бот с 5 вариантами Safari")
    bot.infinity_polling()
