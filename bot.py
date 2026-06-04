import os
import telebot
from telebot import types
import cloudscraper  # Переходим на тяжелую артиллерию для обхода Cloudflare

# Забираем токен из секретов Render
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Твой стикер из логов
STICKER_ID = "CAACAgQAAxkBAAFLabBqIBwnSUz-vGApyE_p53Tlu7tAwgAC4hIAAuddKVNvXRcxXhhEwTsE"

# Временное хранилище состояний пользователей
user_states = {}

# Создаем экземпляр скрейпера, который умеет обходить защиту Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

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

    # Очищаем строку от дефисов, пробелов и прочего мусора, оставляем только цифры
    ally_code = "".join(filter(str.isdigit, raw_text))

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
        # Делаем запрос через наш хитрый скрейпер с таймаутом
        response = scraper.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Достаем никнейм игрока из структуры JSON swgoh.gg
            player_name = "Игрок"
            if 'data' in data and isinstance(data['data'], dict):
                player_name = data['data'].get('name', 'Игрок')
            elif 'name' in data:
                player_name = data.get('name', 'Игрок')

            # Создаем инлайн-кнопки «Да» и «Нет» в один ряд
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_yes = types.InlineKeyboardButton("Да", callback_data=f"yes_{ally_code}")
            btn_no = types.InlineKeyboardButton("Нет", callback_data="no")
            markup.add(btn_yes, btn_no)

            # Переключаем текст на подтверждение
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=f"Нашел! {player_name} - это ты?",
                reply_markup=markup
            )
            user_states[chat_id] = None

        elif response.status_code == 404:
            # Код очистили корректно, но такого игрока на swgoh.gg просто нет
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=error_text,
                parse_mode="Markdown"
            )
        else:
            # Если Cloudflare все равно уперся или сервер выдал другую ошибку (например, 502)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=search_msg.message_id,
                text=f"⚠️ Сервер swgoh.gg ответил кодом {response.status_code}. Похоже, они обновляют базу. Попробуй еще раз через минуту."
            )

    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=search_msg.message_id,
            text="⚠️ Не удалось связаться с swgoh.gg. Проверь код или попробуй позже."
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
    print("Бот успешно запущен в обход блокировок...")
    bot.infinity_polling()
