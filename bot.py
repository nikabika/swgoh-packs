import os
import requests
import telebot
from telebot import types

# Забираем токен из секретов Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Твой стикер из логов
STICKER_ID = "CAACAgQAAxkBAAFLabBqIBwnSUz-vGApyE_p53Tlu7tAwgAC4hIAAuddKVNvXRcxXhhEwTsE"

# Временное хранилище состояний пользователей (в оперативной памяти)
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'waiting_for_ally_code'
    
    # 1. Отправляем стикер
    bot.send_sticker(chat_id, STICKER_ID)
    # 2. Отправляем сообщение вслед (не в ответ)
    bot.send_message(chat_id, "Отправь мне свой код союзника")


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == 'waiting_for_ally_code')
def handle_ally_code(message):
    chat_id = message.chat.id
    raw_text = message.text

    # Очищаем строку: оставляем только цифры
    ally_code = "".join(filter(str.isdigit, raw_text))

    # Текст ошибки при неверном вводе
    error_text = (
        "Ты кажется ошибся. Код союзника можно посмотреть в игре: "
        "*профиль* —> *в центре внизу, под сводкой арены флота*\n\n"
        "После этого отправь повторно"
    )

    if not ally_code:
        bot.send_message(chat_id, error_text, parse_mode="Markdown")
        return

    # Отправляем сообщение о поиске (не в ответ)
    search_msg = bot.send_message(chat_id, "🔍 Ищу твой профиль")
    
    url = f"https://swgoh.gg/api/player/{ally_code}/"

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Достаем имя игрока (в SWGOH API оно обычно сидит в data['data']['name'])
            player_name = "Игрок"
            if 'data' in data and isinstance(data['data'], dict):
                player_name = data['data'].get('name', 'Игрок')
            elif 'name' in data:
                player_name = data.get('name', 'Игрок')

            # Создаем инлайн-кнопки в один ряд
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_yes = types.InlineKeyboardButton("Да", callback_data=f"yes_{ally_code}")
            btn_no = types.InlineKeyboardButton("Нет", callback_data="no")
            markup.add(btn_yes, btn_no)

            # Меняем текст поискового сообщения на результат
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=f"Нашел! {player_name} - это ты?",
                reply_markup=markup
            )
            # Сбрасываем состояние ожидания кода
            user_states[chat_id] = None

        else:
            # Если API вернуло не 200 (например, 404 — код не найден)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=error_text,
                parse_mode="Markdown"
            )

    except Exception as e:
        # На случай если swgoh.gg прилег отдохнуть
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=search_msg.message_id,
            text="⚠️ Что-то пошло не так при запросе к swgoh.gg. Попробуй чуть позже."
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    
    if call.data.startswith("yes_"):
        ally_code = call.data.split("_")[1]
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"Отлично! Профиль {ally_code} успешно привязан. 🚀"
        )
        
    elif call.data == "no":
        user_states[chat_id] = 'waiting_for_ally_code'
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="Хм, давай попробуем еще раз. Отправь корректный код союзника:"
        )

if __name__ == '__main__':
    print("Бот успешно запущен...")
    bot.infinity_polling()
