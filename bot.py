import telebot
import requests
import pandas as pd

TOKEN = "8799271286:AAG_QttfVMa2bdtVuV6tbo39PLsKIzzh3GA"
bot = telebot.TeleBot(TOKEN)

# Загружаем базу контр-пиков
print("📚 Загрузка базы контр-пиков...")
try:
    df_counters = pd.read_csv('swgoh_counters_5v5_all.csv', sep=';')
    print(f"   Загружено {len(df_counters)} контр-пиков")
except Exception as e:
    df_counters = pd.DataFrame()
    print(f"   ⚠️ Файл не найден: {e}")

# Стикер Baby Yoda
BABY_YODA_STICKER = "CAACAgIAAxkBAAFLZAFqH9yQ3u_cEJspnqed1pFf-FRnnQAChwIAAladvQpC7XQrQFfQkDsE"

# Заголовки как у браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://swgoh.gg/',
    'Origin': 'https://swgoh.gg',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, BABY_YODA_STICKER)
    bot.send_message(
        message.chat.id,
        "🎯 *SWGOH Counter Bot*\n\n"
        "Найди лучшие контр-пики под твой ростер!\n\n"
        "Отправь свой код союзника:",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit() and len(m.text.strip()) == 9)
def handle_allycode(message):
    allycode = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Ищу игрока {allycode}...")
    
    try:
        # Пробуем с разными URL
        urls_to_try = [
            f"https://swgoh.gg/api/player/{allycode}/",
            f"https://swgoh.gg/api/player/{allycode}/?format=json",
        ]
        
        data = None
        for url in urls_to_try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    break
                except:
                    continue
        
        if not data:
            bot.send_message(message.chat.id, "❌ Не удалось получить данные игрока. Попробуй позже.")
            return
        
        # Извлекаем base_id всех юнитов
        player_units = set()
        player_name = data.get('data', {}).get('name', 'Игрок')
        
        for unit in data.get('data', {}).get('units', []):
            base_id = unit.get('data', {}).get('base_id', '')
            if base_id:
                player_units.add(base_id)
        
        bot.send_message(
            message.chat.id,
            f"👤 *{player_name}*\n📦 Найдено юнитов: {len(player_units)}",
            parse_mode="Markdown"
        )
        
        if df_counters.empty:
            bot.send_message(message.chat.id, "❌ База контр-пиков не загружена!")
            return
        
        # Ищем подходящие пачки
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
                    'owned': len(owned),
                    'missing': missing,
                    'winrate': row.get('Винрейт_%', 0),
                    'defender': row.get('Лидер_Защиты_Name', ''),
                    'season': row.get('Сезон', '')
                })
        
        best_teams.sort(key=lambda x: (-x['owned'], -x['winrate']))
        
        if best_teams:
            response = "🎯 *ЛУЧШИЕ ПАЧКИ ДЛЯ ТЕБЯ:*\n\n"
            
            for i, team in enumerate(best_teams[:5]):
                status = "✅" if team['owned'] == 5 else "🟡" if team['owned'] == 4 else "🔴"
                response += f"{status} *{i+1}. [{team['winrate']}%]*\n"
                response += f"   Против: {team['defender']}\n"
                response += f"   {team['owned']}/5 юнитов | {team['season']}\n\n"
            
            response += "💎 *Хочешь больше?* Открывай MiniApp!"
        else:
            response = "😔 Не нашлось подходящих пачек."
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:150]}")

@bot.message_handler(func=lambda m: True)
def other_messages(message):
    bot.send_message(message.chat.id, "Отправь свой 9-значный код союзника")

print("🤖 Бот запущен!")
bot.polling(none_stop=True)
