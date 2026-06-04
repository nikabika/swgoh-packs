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

print("📚 Загрузка базы...")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'swgoh_counters_5v5_all.csv')
df = pd.read_csv(CSV_PATH, sep=';')
print(f"✅ {len(df)} контр-пиков загружено")

BABY_YODA_STICKER = "CAACAgIAAxkBAAFLZAFqH9yQ3u_cEJspnqed1pFf-FRnnQAChwIAAladvQpC7XQrQFfQkDsE"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, BABY_YODA_STICKER)
    bot.send_message(message.chat.id, "🎯 *SWGOH Counter Bot*\n\nОтправь свой код союзника:", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and len(m.text.strip()) == 9 and m.text.strip().isdigit())
def handle_allycode(message):
    allycode = message.text.strip()
    bot.send_message(message.chat.id, "🔍 Ищу игрока...")
    
    try:
        url = f"https://swgoh.gg/api/player/{allycode}/"
        resp = scraper.get(url)
        
        if resp.status_code != 200:
            bot.send_message(message.chat.id, "❌ Игрок не найден")
            return
        
        data = resp.json()
        player_name = data.get("data", {}).get("name", "Игрок")
        player_units = set()
        
        for unit in data.get("units", []):
            uid = unit.get("data", {}).get("base_id", "")
            if uid:
                player_units.add(uid)
        
        if not player_units:
            bot.send_message(message.chat.id, "❌ Нет юнитов")
            return
        
        bot.send_message(message.chat.id, f"👤 *{player_name}*\n📦 Юнитов: {len(player_units)}", parse_mode="Markdown")
        
        teams = []
        for _, row in df.iterrows():
            ids = [
                str(row["Атакующий_1_ID"]).strip(),
                str(row["Атакующий_2_ID"]).strip(),
                str(row["Атакующий_3_ID"]).strip(),
                str(row["Атакующий_4_ID"]).strip(),
                str(row["Атакующий_5_ID"]).strip()
            ]
            owned = [x for x in ids if x in player_units]
            missing = [x for x in ids if x not in player_units]
            
            if len(owned) >= 3:
                teams.append({
                    "owned": len(owned),
                    "missing": missing,
                    "winrate": int(row["Винрейт_%"]),
                    "defender": str(row["Лидер_Защиты_Name"]),
                    "season": str(row["Сезон"])
                })
        
        teams.sort(key=lambda x: (-x["owned"], -x["winrate"]))
        
        if not teams:
            bot.send_message(message.chat.id, "😔 Не нашлось пачек")
            return
        
        text = "🎯 *ЛУЧШИЕ ПАЧКИ:*\n\n"
        shown = 0
        
        for t in teams:
            if t["owned"] >= 4 and shown < 5:
                s = "✅" if t["owned"] == 5 else "🟡"
                text += f"{s} *[{t['winrate']}%]* Против: {t['defender']}\n"
                if t["missing"]:
                    text += f"   Не хватает: {t['missing'][0]}\n"
                text += f"   {t['owned']}/5 | {t['season']}\n\n"
                shown += 1
        
        for t in teams:
            if t["owned"] == 3 and shown < 5:
                text += f"🔴 *[{t['winrate']}%]* Против: {t['defender']}\n"
                text += f"   Не хватает: {', '.join(t['missing'][:2])}\n"
                text += f"   3/5 | {t['season']}\n\n"
                shown += 1
        
        text += "💎 *Больше пачек в MiniApp!*"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(func=lambda m: True)
def other(message):
    bot.send_message(message.chat.id, "Отправь 9-значный код союзника")

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.polling(none_stop=True)
