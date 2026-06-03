import json
import pandas as pd
import os

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'swgoh_counters_5v5_all.csv')

# Для локального теста — игрок из файла
PLAYER_JSON = r"D:\Пользователи\Artem\Downloads\player.json"

print("=" * 60)
print("🤖 SWGOH COUNTER BOT — ТЕСТОВЫЙ ЗАПУСК")
print("=" * 60)

# 1. Загружаем игрока из JSON
print("\n📥 Загружаем данные игрока...")
with open(PLAYER_JSON, 'r', encoding='utf-8') as f:
    player_data = json.load(f)

player_units = set()
for unit in player_data.get('units', []):
    base_id = unit.get('data', {}).get('base_id', '')
    if base_id:
        player_units.add(base_id)

player_name = player_data.get('data', {}).get('name', 'Игрок')
print(f"   👤 {player_name}")
print(f"   📦 Юнитов: {len(player_units)}")

# 2. Загружаем базу контр-пиков
print(f"\n📚 Загружаем базу контр-пиков...")
if not os.path.exists(CSV_PATH):
    # Пробуем из загрузок
    CSV_PATH = r"D:\Пользователи\Artem\Downloads\swgoh_counters_5v5_all.csv"

print(f"   Путь: {CSV_PATH}")
df = pd.read_csv(CSV_PATH, sep=';')
print(f"   Загружено: {len(df)} контр-пиков")
print(f"   Колонки: {list(df.columns)}")

# 3. Ищем подходящие пачки
print(f"\n🔍 Подбираем пачки...")
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
            'winrate': int(row.get('Винрейт_%', 0)),
            'defender': str(row.get('Лидер_Защиты_Name', '')),
            'season': str(row.get('Сезон', ''))
        })

# Сортировка: сначала полные (5/5), потом по винрейту
best_teams.sort(key=lambda x: (-x['owned'], -x['winrate']))

print(f"\n✅ Найдено пачек: {len(best_teams)}")

# 4. Вывод результатов
print(f"\n{'='*60}")
print(f"🎯 ЛУЧШИЕ ПАЧКИ ДЛЯ {player_name.upper()}")
print(f"{'='*60}")

# Статистика
full = sum(1 for t in best_teams if t['owned'] == 5)
almost = sum(1 for t in best_teams if t['owned'] == 4)
in_progress = sum(1 for t in best_teams if t['owned'] == 3)

print(f"\n✅ Полные (5/5): {full}")
print(f"🟡 Почти готовы (4/5): {almost}")
print(f"🔴 В процессе (3/5): {in_progress}")

print(f"\n--- ТОП-5 ПОЛНЫХ ---")
count = 0
for t in best_teams:
    if t['owned'] == 5:
        count += 1
        print(f"{count}. [{t['winrate']}%] Против: {t['defender']}")
        print(f"   Сезон: {t['season']}")
        if count >= 5:
            break

if count == 0:
    print("   Нет полных пачек")

print(f"\n--- ТОП-5 ПОЧТИ ГОТОВЫХ (4/5) ---")
count = 0
for t in best_teams:
    if t['owned'] == 4:
        count += 1
        print(f"{count}. [{t['winrate']}%] Против: {t['defender']}")
        print(f"   Не хватает: {t['missing'][0] if t['missing'] else '?'}")
        if count >= 5:
            break

print(f"\n{'='*60}")
print("✅ ТЕСТ УСПЕШНО ЗАВЕРШЁН!")
