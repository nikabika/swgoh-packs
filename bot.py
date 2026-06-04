import telebot
import csv
import os
from curl_cffi import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("❌ Токен не найден!")
    exit()

bot = telebot.TeleBot(TOKEN)

print("📚 Загрузка базы...")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'swgoh_counters_5v5_all.csv')

counters = []
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        counters.append({
            'defender': row.get('Лидер_Защиты_Name', ''),
            'a1': row.get('Атакующий_1_ID', '').strip(),
            'a2': row.get('Атакующий_2_ID', '').strip(),
            'a3': row.get('Атакующий_3_ID', '').strip(),
            'a4': row.get('Атакующий_4_ID', '').strip(),
            'a5': row.get('Атакующий_5_ID', '').strip(),
            'winrate': int(row.get('Винрейт_%', 0) or 0),
            'season': row.get('Сезон', '')
        })

print(f"✅ {len(counters)} контр-пиков")

BABY_YODA_STICKER = "CAACAgIAAxkBAAFLZAFqH9yQ3u_cEJspnqed1pFf-FRnnQAChwIAAladvQpC7XQrQFfQkDsE"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, BABY_YODA_STICKER)
    bot.send_message(
        message.chat.id,
        "🎯 *SWGOH Counter Bot*\n\n"
        "Привет! Я помогу подобрать лучшие контр-пачки для твоего ростера.\n\n"
        "📱 Отправь свой *код союзника* (9 цифр):",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and len(m.text.strip()) == 9 and m.text.strip().isdigit())
def handle_allycode(message):
    allycode = message.text.strip()
    bot.send_message(message.chat.id, "🔍 Ищу игрока...")
    
    try:
        resp = requests.get(f"https://swgoh.gg/api/player/{allycode}/", impersonate="chrome110")
        
        if resp.status_code != 200:
            bot.send_message(message.chat.id, "❌ Игрок не найден")
            return
        
        data = resp.json()
        player = data.get("data", {})
        player_name = player.get("name", "Игрок")
        player_level = player.get("level", 0)
        player_portrait = player.get("portrait_image", "")
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Да, это я", callback_data=f"yes_{allycode}"),
            InlineKeyboardButton("❌ Нет, это не я", callback_data="no")
        )
        
        if player_portrait:
            bot.send_photo(
                message.chat.id,
                player_portrait,
                caption=f"👤 *{player_name}*\n⭐ Уровень: *{player_level}*\n\nЭто вы?",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                f"👤 *{player_name}*\n⭐ Уровень: *{player_level}*\n\nЭто вы?",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:100]}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("yes_"))
def callback_yes(call):
    allycode = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "✅ Отлично! Ищу пачки...")
    bot.send_message(call.message.chat.id, f"🔄 Загружаем данные игрока {allycode}...")

@bot.callback_query_handler(func=lambda call: call.data == "no")
def callback_no(call):
    bot.answer_callback_query(call.id, "❌ Отменено")
    bot.send_message(call.message.chat.id, "Отправь правильный код союзника.")

@bot.message_handler(func=lambda m: True)
def other(message):
    bot.send_message(message.chat.id, "Отправь 9-значный код союзника")

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.polling(none_stop=True)
