import json

# Загружаем игрока
with open(r'D:\Пользователи\Artem\Downloads\player.json', 'r', encoding='utf-8') as f:
    player_data = json.load(f)

# Все base_id игрока
player_units = set()
for unit in player_data.get('units', []):
    base_id = unit.get('data', {}).get('base_id', '')
    if base_id:
        player_units.add(base_id)

player_name = player_data.get('data', {}).get('name', 'Игрок')
print(f"👤 {player_name}")
print(f"📦 Юнитов: {len(player_units)}")
print(f"Примеры: {list(player_units)[:10]}")

# Загружаем базу контр-пиков
import pandas as pd
try:
    df = pd.read_csv('swgoh_counters_5v5_all.csv', sep=';')
    print(f"\n📚 Контр-пиков в базе: {len(df)}")
except:
    print("❌ Файл с контр-пиками не найден!")
    exit()

# Ищем подходящие пачки
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
    missing = [uid for uid in attacker_ids if uid not in player_units]
    
    if len(owned) >= 3:
        best_teams.append({
            'ids': attacker_ids,
            'owned': len(owned),
            'missing': missing,
            'winrate': row.get('Винрейт_%', 0),
            'defender': row.get('Лидер_Защиты_Name', ''),
            'season': row.get('Сезон', '')
        })

best_teams.sort(key=lambda x: (-x['owned'], -x['winrate']))

print(f"\n🎯 НАЙДЕНО ПАЧЕК: {len(best_teams)}")
print(f"\nТОП-5:")
for i, t in enumerate(best_teams[:5]):
    s = "✅" if t['owned'] == 5 else "🟡" if t['owned'] == 4 else "🔴"
    print(f"{s} {i+1}. [{t['winrate']}%] Против: {t['defender']}")
    print(f"   {t['owned']}/5 | {t['season']}")
    if t['missing']:
        print(f"   Не хватает: {', '.join(t['missing'][:3])}")
