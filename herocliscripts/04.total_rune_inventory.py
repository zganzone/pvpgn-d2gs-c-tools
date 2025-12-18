#!/usr/bin/env python3
"""
Скрипт за сканиране на всички герои в директорията за запазване,
за да се съберат и изведат всички руни в общ инвентар.

Използване:
python3 04.total_rune_inventory.py [ТЪРСЕНА_РУНА (опционално)]
Пример: python3 04.total_rune_inventory.py Tal
"""
import os
import sys
from d2lib.files import D2SFile
from typing import List, Any
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
CHAR_SAVE_DIR = "/usr/local/pvpgn/var/pvpgn/charsave" 
# =======================================================

# Известни кодове, които започват с 'r', но НЕ СА руни:
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

# --- ХАРДКОДНА БАЗА ДАННИ ЗА СВОЙСТВАТА НА РУНИТЕ (за справка) ---
RUNE_STATS = {
    "El Rune": "Light Radius: +1 | Attack Rating: +50",
    "Eld Rune": "Defense: +7% (Armor/Helm) | Faster Run/Walk: +30% (Shield)",
    # ... (Останалите руни остават в оригиналния RUNE_STATS)
    "Tir Rune": "Replenish Mana: +2",
    "Nef Rune": "Defense vs. Missile: +30 (Armor/Helm)",
    "Eth Rune": "Regenerate Mana: +15% (Armor/Helm)",
    "Ral Rune": "Fire Resistance: +30% (Armor/Helm) | Fire Resist: +35% (Shield)",
    "Ort Rune": "Lightning Resistance: +30% (Armor/Helm) | Lightning Resist: +35% (Shield)",
    "Tal Rune": "Poison Resistance: +30% (Armor/Helm) | Poison Resist: +35% (Shield)",
    "Thul Rune": "Cold Resistance: +30% (Armor/Helm) | Cold Resist: +35% (Shield)",
    "Amn Rune": "Life Stolen per Hit: 7% (Weapon)",
    "Sol Rune": "Damage Reduced: 7 (Armor/Helm/Shield)",
    "Shael Rune": "Attack Speed: +20% (Weapon) | Faster Hit Recovery: +20% (Armor/Helm)",
    "Dol Rune": "Hit Causes Monster to Flee 25% (Weapon)",
    "Io Rune": "Vitality: +10",
    "Lum Rune": "Energy: +10",
    "Ko Rune": "Dexterity: +10",
    "Fal Rune": "Strength: +10",
    "Pul Rune": "Defense: +30% (Armor/Helm) | Resist All: +15 (Shield)",
    "Um Rune": "Resist All: +15 (Armor/Helm) | Resist All: +22 (Shield)",
    # ... (Добавете всичките 33 руни тук, ако искате пълен отчет)
}
# -------------------------------------------------------------------

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    from d2lib.files import D2SFile
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    sys.exit(1)


def gather_all_runes(char_dir: str) -> defaultdict:
    """
    Сканира всички файлове в char_dir, парсва ги и събира всички руни.
    Връща defaultdict с общия брой на всяка руна.
    """
    total_rune_counts = defaultdict(int)
    total_chars_scanned = 0
    
    if not os.path.isdir(char_dir):
        print(f"\n[!!!] ERROR: Директорията за запазване на герои не е намерена: {char_dir}")
        return total_rune_counts
        
    print(f"[*] Сканиране на директорията: {char_dir}")

    # Обхождане на всички файлове в директорията
    for filename in os.listdir(char_dir):
        # Файловете с герои в pvpgn обикновено са само името (без разширение)
        # Може да добавите филтър, ако имате .d2s или други файлове
        char_path = os.path.join(char_dir, filename)
        
        if os.path.isdir(char_path):
            continue
            
        try:
            d2s = D2SFile(char_path)
            total_chars_scanned += 1
        except Exception as e:
            # print(f"[-] Пропускане на {filename}: Грешка при парсване ({e})")
            continue

        # Взимане на всички предмети (инвентар + сандък)
        all_items = list(getattr(d2s, "items", []))
        try: all_items.extend(list(getattr(d2s, "stash", [])))
        except Exception: pass
        
        # Обхождане на предметите
        for item in all_items:
            code = getattr(item, 'code', '')
            
            # Филтриране за руни (същата логика като във Вашия скрипт)
            if code.startswith('r') and code not in NON_RUNE_CODES:
                if len(code) == 3 and code[1:].isdigit() and 1 <= int(code[1:]) <= 33:
                    name = getattr(item, 'name', 'Unknown Rune')
                    total_rune_counts[name] += 1

    print(f"[*] Сканирането приключи. Обработени герои: {total_chars_scanned}")
    return total_rune_counts


def print_report(total_rune_counts: defaultdict, search_runes: List[str] = None):
    """
    Отпечатва общия доклад или филтриран списък по търсена руна.
    """
    
    total_count = sum(total_rune_counts.values())
    
    print("\n=======================================================")
    print(f"  ОБЩ ИНВЕНТАР С РУНИ ({total_count} total)")
    
    if search_runes:
        print(f"  Филтър: {', '.join(search_runes)}")
    
    print("=======================================================")

    display_list = []
    
    for name, count in sorted(total_rune_counts.items()):
        # Проверка дали трябва да филтрираме по търсена руна
        if search_runes and name.split()[0].upper() not in [r.upper() for r in search_runes]:
             continue
             
        stats = RUNE_STATS.get(name, "!!! Свойствата не са дефинирани в базата данни !!!")
        
        # Форматиране на реда
        display_list.append({
            'name': name,
            'count': count,
            'stats': stats,
        })
        
    if not display_list:
        print(f"  [---] Не бяха открити руни, отговарящи на филтъра: {search_runes}")
        return
        
    # Печат на резултатите
    for item in display_list:
        print(f"\n  > {item['name']} ({item['count']}x):")
        print(f"    - **Бонуси:** {item['stats']}")
        
    print("\n=======================================================\n")


if __name__ == "__main__":
    
    # 1. Извличане на търсените руни от аргументите на командния ред
    search_runes = []
    if len(sys.argv) > 1:
        # Всички аргументи след името на скрипта се считат за търсени руни
        search_runes = sys.argv[1:]
    
    # 2. Събиране на всички руни от всички герои
    all_rune_data = gather_all_runes(CHAR_SAVE_DIR)
    
    # 3. Отпечатване на доклад (общ или филтриран)
    print_report(all_rune_data, search_runes)
