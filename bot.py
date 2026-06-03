import os
import telebot
import requests
import pandas as pd
from telebot import apihelper

# Токен из переменной окружения Render
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("❌ Переменная TOKEN не установлена!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Прокси для России (Render в США, ему не нужен)
# Если деплоишь из РФ локально — раскомментируй:
# apihelper.proxy = {'https': 'socks5://127.0.0.1:9150'}

# Загружаем базу контр-пиков
print("📚 Загрузка базы контр-пиков...")
try:
    df_counters = pd.read_csv('swgoh_counters_5v5_all.csv', sep=';')
    print(f"   Загружено {len(df_counters)} контр-пиков")
except Exception as e:
    df_counters = pd.DataFrame()
    print(f"   ⚠️ Файл не найден: {e}")

BABY_YODA_STICKER = "CAACAgIAAxkBAAFLZAFqH9yQ3u_cEJspnqed1pFf-FRnnQAChwIAAladvQpC7XQrQFfQkDsE"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, BABY_YODA_STICKER)
    bot.send_message(message.chat.id, "🎯 *SWGOH Counter Bot*\n\nОтправь свой код союзника:", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit() and len(m.text.strip()) == 9)
def handle_allycode(message):
    allycode = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Ищу игрока {allycode}...")
    
    try:
        url = f"https://swgoh.gg/api/player/{allycode}/"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        data = resp.json()
        
        player_units = set()
        player_name = data.get('data', {}).get('name', 'Игрок')
        
        for unit in data.get('data', {}).get('units', []):
            base_id = unit.get('data', {}).get('base_id', '')
            if base_id:
                player_units.add(base_id)
        
        bot.send_message(message.chat.id, f"👤 *{player_name}*\n📦 Юнитов: {len(player_units)}", parse_mode="Markdown")
        
        if df_counters.empty:
            bot.send_message(message.chat.id, "❌ База контр-пиков не загружена!")
            return
        
        best_teams = []
        for _, row in df_counters.iterrows():
            attacker_ids = [
                str(row.get('Атакующий_1_ID', '')).strip(),
                str(row.get('Атакующий_2_ID', '')).strip(),
                str(row.get('Атакующий_3_ID', '')).strip(),
                str(row.get('Атакующий_4_ID', '')).strip(),
                str(row.get('Атакующий_5_ID', '')).strip()
            ]
            
            owned = [uid for uid in attacker_ids if uid in player_units]
            missing = [uid for uid in attacker_ids if uid not in player_units]
            
            if len(owned) >= 3:
                best_teams.append({
                    'attacker_ids': attacker_ids,
                    'owned': len(owned),
                    'missing': missing,
                    'winrate': row.get('Винрейт_%', 0),
                    'defender': row.get('Лидер_Защиты_Name', ''),
                    'season': row.get('Сезон', '')
                })
        
        best_teams.sort(key=lambda x: (-x['owned'], -x['winrate']))
        
        if best_teams:
            response = "🎯 *ЛУЧШИЕ ПАЧКИ:*\n\n"
            for i, team in enumerate(best_teams[:5]):
                status = "✅" if team['owned'] == 5 else "🟡" if team['owned'] == 4 else "🔴"
                response += f"{status} *{i+1}. [{team['winrate']}%]*\n"
                response += f"   Против: {team['defender']}\n"
                response += f"   {team['owned']}/5 | {team['season']}\n\n"
            response += "💎 *Больше в MiniApp!*"
        else:
            response = "😔 Ничего не найдено"
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:150]}")

@bot.message_handler(func=lambda m: True)
def other_messages(message):
    bot.send_message(message.chat.id, "Отправь 9-значный код союзника")

# Для Render нужен веб-сервер
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 403

# Запуск
if __name__ == '__main__':
    print("🤖 Бот запущен!")
    # Для локального теста используй polling
    # Для Render используй webhook
    import sys
    if '--local' in sys.argv:
        bot.polling(none_stop=True)
    else:
        # Render сам вызовет app.run()
        pass
