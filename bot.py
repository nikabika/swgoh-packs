import telebot
import os
import json
from curl_cffi import requests

# Токен из переменных окружения Render
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Временное хранилище последних результатов (опционально)
cache = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🎮 **SWGOH Player Bot**\n\n"
        "Получай данные игроков из swgoh.gg\n\n"
        "📌 **Команды:**\n"
        "/player `код` - данные игрока\n"
        "/help - помощь\n\n"
        "📝 **Пример:** `/player 431294714`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "🔍 **Как использовать:**\n\n"
        "1. Найди код союзника в игре SWGOH\n"
        "2. Отправь команду:\n"
        "`/player 123456789`\n\n"
        "📊 **Что показывается:**\n"
        "• Имя игрока\n"
        "• Уровень\n"
        "• Код союзника\n"
        "• Гильдия (если есть)\n"
        "• Ссылка на профиль\n\n"
        "⚡ Данные берутся напрямую из API swgoh.gg",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['player'])
def get_player_info(message):
    # Проверяем аргументы
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(
            message,
            "❌ **Ошибка:** Укажите код союзника\n\n"
            "Пример: `/player 431294714`",
            parse_mode='Markdown'
        )
        return
    
    ally_code = parts[1]
    
    # Проверка формата кода
    if not ally_code.isdigit():
        bot.reply_to(
            message,
            "❌ **Ошибка:** Код должен состоять только из цифр",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем статус "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Пытаемся получить данные
    result = fetch_player_data(ally_code)
    
    if result["success"]:
        data = result["data"]
        # Формируем красивый ответ
        response_text = (
            f"🎮 **{data.get('name', 'Неизвестно')}**\n\n"
            f"📊 **Уровень:** {data.get('level', '?')}\n"
            f"🔢 **Код:** {data.get('ally_code', ally_code)}\n"
            f"🏛️ **Гильдия:** {data.get('guild_name', 'Не состоит')}\n\n"
            f"🔗 [Профиль на swgoh.gg](https://swgoh.gg/p/{ally_code}/)"
        )
        bot.reply_to(message, response_text, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.reply_to(
            message,
            f"❌ **Не удалось получить данные**\n\n"
            f"Код: `{ally_code}`\n"
            f"Ошибка: {result['error']}\n\n"
            f"💡 Проверьте код или попробуйте позже",
            parse_mode='Markdown'
        )

def fetch_player_data(ally_code):
    """Получение данных игрока с обходом Cloudflare"""
    url = f"https://swgoh.gg/api/player/{ally_code}"
    
    # Проверяем кэш (5 минут)
    if ally_code in cache and cache[ally_code]["time"] > 300:
        return {"success": True, "data": cache[ally_code]["data"]}
    
    try:
        # Имитируем разные браузеры для лучшего обхода
        # Safari 15.5 на macOS - хороший отпечаток
        response = requests.get(
            url,
            impersonate="safari15_5",
            timeout=30,
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Сохраняем в кэш
            cache[ally_code] = {
                "data": data,
                "time": 0  # Для простоты не используем таймер
            }
            return {"success": True, "data": data}
        elif response.status_code == 404:
            return {"success": False, "error": "Игрок не найден"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Таймаут. Сервер не отвечает"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Ошибка соединения"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Неверный ответ сервера"}
    except Exception as e:
        return {"success": False, "error": str(e)[:100]}

# Команда для очистки кэша (опционально)
@bot.message_handler(commands=['clear'])
def clear_cache(message):
    cache.clear()
    bot.reply_to(message, "✅ Кэш очищен")

# Запуск бота
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Переменная окружения TOKEN не установлена!")
        exit(1)
    
    print("🚀 Бот запущен!")
    print(f"📡 Имитация: Safari 15.5")
    print(f"🤖 Бот: @{bot.get_me().username}")
    print("⏳ Ожидание команд...")
    
    try:
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
