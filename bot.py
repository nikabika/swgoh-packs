import os
import telebot
from telebot import types
import cloudscraper
from flask import Flask, request

# Инициализируем Flask
app = Flask(__name__)

# Забираем токен из секретов Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Твой стикер
STICKER_ID = "CAACAgQAAxkBAAFLabBqIBwnSUz-vGApyE_p53Tlu7tAwgAC4hIAAuddKVNvXRcxXhhEwTsE"

# Временное хранилище состояний пользователей
user_states = {}

# Обход Cloudflare для swgoh.gg
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# --- ХЕНДЛЕРЫ ТЕЛЕГРАМА ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'waiting_for_ally_code'
    bot.send_sticker(chat_id, STICKER_ID)
    bot.send_message(chat_id, "Отправь мне свой код союзника")


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == 'waiting_for_ally_code')
def handle_ally_code(message):
    chat_id = message.chat.id
    raw_text = message.text

    ally_code = "".join(filter(str.isdigit, raw_text))

    error_text = (
        "Ты кажется ошибся. Код союзника можно посмотреть в игре: "
        "*профиль* —> *в центре внизу, под сводкой арены флота*\n\n"
        "После этого отправь повторно"
    )

    if not ally_code:
        bot.send_message(chat_id, error_text, parse_mode="Markdown")
        return

    search_msg = bot.send_message(chat_id, "🔍 Ищу твой профиль")
    url = f"https://swgoh.gg/api/player/{ally_code}/"

    try:
        response = scraper.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            player_name = "Игрок"
            if 'data' in data and isinstance(data['data'], dict):
                player_name = data['data'].get('name', 'Игрок')
            elif 'name' in data:
                player_name = data.get('name', 'Игрок')

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_yes = types.InlineKeyboardButton("Да", callback_data=f"yes_{ally_code}")
            btn_no = types.InlineKeyboardButton("Нет", callback_data="no")
            markup.add(btn_yes, btn_no)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=f"Нашел! {player_name} - это ты?",
                reply_markup=markup
            )
            user_states[chat_id] = None

        elif response.status_code == 404:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=error_text,
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=f"⚠️ Сервер swgoh.gg ответил кодом {response.status_code}. Попробуй позже."
            )

    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=search_msg.message_id,
            text="⚠️ Не удалось связаться с swgoh.gg. Попробуй позже."
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    if call.data.startswith("yes_"):
        ally_code = call.data.split("_")[1]
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"Отлично! Профиль {ally_code} привязан. 🚀")
    elif call.data == "no":
        user_states[chat_id] = 'waiting_for_ally_code'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="Отправь корректный код союзника:")

# --- ЛОГИКА FLASK ДЛЯ ВЕБХУКА ---

# Главная страница (просто чтобы Render видел, что сервис жив)
@app.route('/')
def index():
    return "Bot is alive!", 200

# Точка входа для обновлений от Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

if __name__ == '__main__':
    # Сбрасываем старый вебхук или активный поллинг, чистим хвосты 409 ошибки
    bot.remove_webhook()
    
    # Render автоматически подставляет URL твоего приложения в эту переменную
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
    
    if RENDER_URL:
        # Говорим Телеграму присылать данные на наш Flask
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Вебхук успешно установлен на: {RENDER_URL}/{TOKEN}")
    else:
        print("Внимание: RENDER_EXTERNAL_URL не найден. Работа локально?")

    # Запускаем Flask на порту, который выделит Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
