import telebot
import cloudscraper
import pandas as pd
import os

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("❌ Токен не найден!")
    exit()

bot = telebot.TeleBot(TOKEN)
scraper = cloudscraper.create_scraper()

# Загружаем базу контр-пиков
print("📚 Загрузка базы контр-пиков...")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'swgoh_counters_5v5_all.csv')
df = pd.read_csv(CSV_PATH, sep=';')
print(f"   Загружено {len(df)} контр-пиков")

BABY_YODA_STICKER = "CAACAgIAAxkBAAFLZAFqH9yQ3u_cEJspnqed1pFf-FRnnQAChwIAAladvQpC7XQrQFfQkDsE"

def get_player_units(allycode):
    """Получает список base_id юнитов игрока"""
    url = f"https://swgoh.gg/api/player/{allycode}/"
    resp = scraper.get(url)
    if resp.status_code != 200:
        return None, None
    
    data = resp.json()
    player_name = data.get('data', {}).get('name', 'Игрок')
    units = set()
    
    for unit in data.get('units', []):
        base_id = unit.get('data', {}).get('base_id', '')
        if base_id:
            units.add(base_id)
    
    return player_name, units

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, BABY_YODA_STICKER)
    bot.send_message(
        message.chat.id,
        "🎯 *SWGOH Counter Bot*\n\nОтправь свой код союзника:",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit() and len(m.text.strip()) == 9)
def handle_allycode(message):
    allycode = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Ищу игрока {allycode}...")
    
    player_name, player_units = get_player_units(allycode)
    
    if not player_units:
        bot.send_message(message.chat.id, "❌ Игрок не найден или API недоступен")
        return
    
    bot.send_message(
        message.chat.id,
        f"👤 *{player_name}*\n📦 Юнитов: {len(player_units)}",
        parse_mode="Markdown"
    )
    
    best_teams = []
    for _, row in df.iterrows():
        attacker_ids = [
            str(row.get('Атакующий_1_ID', '')).strip(),
            str(row.get('Атакующий_2_ID', '')).strip(),
            str(row.get('Атакующий_3_ID', '')).strip(),
            str(row.get('Атакующий_4_ID', '')).strip(),
            str(row.get('Атакующий_5_ID', '')).strip()
        ]
        
        owned = [uid for uid in attacker_ids if uid in player_units]
        
        if len(owned) >= 3:
            best_teams.append({
                'owned': len(owned),
                'missing': [uid for uid in attacker_ids if uid not in player_units],
                'winrate': int(row.get('Винрейт_%', 0)),
                'defender': str(row.get('Лидер_Защиты_Name', '')),
                'season': str(row.get('Сезон', ''))
            })
    
    best_teams.sort(key=lambda x: (-x['owned'], -x['winrate']))
    
    if best_teams:
        response = "🎯 *ЛУЧШИЕ ПАЧКИ:*\n\n"
        shown = 0
        
        for t in best_teams:
            if t['owned'] >= 4 and shown < 5:
                status = "✅" if t['owned'] == 5 else "🟡"
                response += f"{status} *[{t['winrate']}%]* Против: {t['defender']}\n"
                if t['missing']:
                    response += f"   Не хватает: {t['missing'][0]}\n"
                response += f"   {t['owned']}/5 | {t['season']}\n\n"
                shown += 1
        
        if shown < 5:
            for t in best_teams:
                if t['owned'] == 3 and shown < 5:
                    response += f"🔴 *[{t['winrate']}%]* Против: {t['defender']}\n"
                    response += f"   Не хватает: {', '.join(t['missing'][:2])}\n"
                    response += f"   3/5 | {t['season']}\n\n"
                    shown += 1
        
        response += "💎 *Больше пачек в MiniApp!*"
    else:
        response = "😔 Не нашлось подходящих пачек"
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def other(message):
    bot.send_message(message.chat.id, "Отправь 9-значный код союзника")

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.polling(none_stop=True)
