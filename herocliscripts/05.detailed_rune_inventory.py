#!/usr/bin/env python3
"""
Скрипт за сканиране на всички герои, събиране на руните и показване
кой герой колко руни има.

Използване:
python3 05.detailed_rune_inventory.py [ТЪРСЕНА_РУНА (опционално)]
Пример: python3 05.detailed_rune_inventory.py Tal
"""
import os
import sys
from d2lib.files import D2SFile
from typing import List, Dict, Any
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
CHAR_SAVE_DIR = "/usr/local/pvpgn/var/pvpgn/charsave" 
# =======================================================

# Известни кодове, които започват с 'r', но НЕ СА руни:
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

# RUNE_STATS (оставен за справка)
RUNE_STATS = {
    # ... (Всички Ваши дефиниции за руните)
    "El Rune": "Light Radius: +1 | Attack Rating: +50",
    "Eld Rune": "Defense: +7% (Armor/Helm) | Faster Run/Walk: +30% (Shield)",
    "Tal Rune": "Poison Resistance: +30% (Armor/Helm) | Poison Resist: +35% (Shield)",
    "Ral Rune": "Fire Resistance: +30% (Armor/Helm) | Fire Resist: +35% (Shield)",
    # ...
}

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    from d2lib.files import D2SFile
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    sys.exit(1)


def gather_all_runes_detailed(char_dir: str) -> Dict[str, Dict[str, int]]:
    """
    Сканира всички файлове, събира руните и проследява кой герой колко руни има.
    Връща: { 'RuneName': { 'char_name': count, ... }, ... }
    """
    # Общ речник: { Име на руна: { Име на герой: Брой } }
    total_rune_inventory = defaultdict(lambda: defaultdict(int))
    total_chars_scanned = 0
    
    if not os.path.isdir(char_dir):
        print(f"\n[!!!] ERROR: Директорията за запазване на герои не е намерена: {char_dir}")
        return total_rune_inventory
        
    print(f"[*] Сканиране на директорията: {char_dir}")

    for filename in os.listdir(char_dir):
        char_path = os.path.join(char_dir, filename)
        if os.path.isdir(char_path):
            continue
            
        try:
            d2s = D2SFile(char_path)
            total_chars_scanned += 1
            # Взимане на името на героя от файла (filename е по-надежден от d2s.char_name)
            char_name = filename 
        except Exception:
            continue

        all_items = list(getattr(d2s, "items", []))
        try: all_items.extend(list(getattr(d2s, "stash", [])))
        except Exception: pass
        
        # Обхождане на предметите
        for item in all_items:
            code = getattr(item, 'code', '')
            
            # Филтриране за руни
            if code.startswith('r') and code not in NON_RUNE_CODES:
                if len(code) == 3 and code[1:].isdigit() and 1 <= int(code[1:]) <= 33:
                    name = getattr(item, 'name', 'Unknown Rune')
                    
                    # Записване на руната под името на героя
                    total_rune_inventory[name][char_name] += 1

    print(f"[*] Сканирането приключи. Обработени герои: {total_chars_scanned}")
    return total_rune_inventory


def print_detailed_report(total_rune_inventory: Dict[str, Dict[str, int]], search_runes: List[str] = None):
    """
    Отпечатва доклад с информация за това, кой герой притежава руните.
    """
    
    # Изчисляване на общия брой
    total_count = sum(sum(counts.values()) for counts in total_rune_inventory.values())
    
    print("\n=======================================================")
    print(f"  ПОДРОБЕН ИНВЕНТАР С РУНИ ПО ГЕРОЙ ({total_count} total)")
    
    if search_runes:
        print(f"  Филтър: {', '.join(search_runes)}")
    
    print("=======================================================")

    for rune_name, char_counts in sorted(total_rune_inventory.items()):
        
        # Проверка за филтър
        if search_runes and rune_name.split()[0].upper() not in [r.upper() for r in search_runes]:
             continue
             
        # Общ брой от тази руна
        total_rune_count = sum(char_counts.values())
        
        print(f"\n> {rune_name} (Общо: {total_rune_count}x):")
        
        # Печат на героите
        for char_name, count in sorted(char_counts.items(), key=lambda item: item[1], reverse=True):
            print(f"  - {char_name}: {count}x")
            
        # Добавяне на бонусите
        stats = RUNE_STATS.get(rune_name, "!!! Свойствата не са дефинирани в базата данни !!!")
        print(f"  - Бонуси: {stats}")
        
    print("\n=======================================================\n")


if __name__ == "__main__":
    
    search_runes = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # 2. Събиране на всички руни от всички герои
    all_rune_data = gather_all_runes_detailed(CHAR_SAVE_DIR)
    
    # 3. Отпечатване на подробния доклад
    print_detailed_report(all_rune_data, search_runes)
