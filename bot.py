import os
import telebot
from telebot import types
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

STICKER_ID = "CAACAgQAAxkBAAFLabBqIBwnSUz-vGApyE_p53Tlu7tAwgAC4hIAAuddKVNvXRcxXhhEwTsE"
GAS_URL = "https://script.google.com/macros/s/AKfycbwSCwPlaeY-Gyv6L29A2uwDSFdsXeHOjp8IBYKptYwJxENA5voERRZequIDNgNvdPba/exec"
user_states = {}

def get_json(ally_code):
    try:
        response = requests.get(f"{GAS_URL}?code={ally_code}", timeout=25)
        return response.json() if response.status_code == 200 else None
    except:
        return None

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
        "Код союзника введен неверно. Посмотри его в игре:\n"
        "Профиль — внизу по центру, под сводкой арены флота.\n\n"
        "Отправь код повторно."
    )

    if not ally_code or len(ally_code) != 9:
        bot.send_message(chat_id, error_text)
        return

    search_msg = bot.send_message(chat_id, "Поиск профиля...")
    data = get_json(ally_code)
    
    if data:
        p = data.get('data', data)
        player_name = p.get('name', 'Игрок')
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_yes = types.InlineKeyboardButton("Да", callback_data=f"yes_{ally_code}")
        btn_no = types.InlineKeyboardButton("Нет", callback_data="no")
        markup.add(btn_yes, btn_no)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=search_msg.message_id,
            text=f"Нашел! {player_name} — это ты?",
            reply_markup=markup
        )
        user_states[chat_id] = None
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=search_msg.message_id,
            text="Не удалось получить данные. Проверь код или попробуй позже."
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    if call.data.startswith("yes_"):
        ally_code = call.data.split("_")[1]
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"Профиль {ally_code} успешно привязан.")
    elif call.data == "no":
        user_states[chat_id] = 'waiting_for_ally_code'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="Отправь корректный код союзника:")

@app.route('/')
def index():
    return "OK", 200

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
    bot.remove_webhook()
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
