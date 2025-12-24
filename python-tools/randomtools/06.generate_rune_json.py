#!/usr/bin/env python3
"""
Скрипт за сканиране на всички герои, събиране на руните и генериране на
един JSON файл с цялата информация.
"""
import os
import sys
import json
from d2lib.files import D2SFile
from typing import List, Dict, Any
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
CHAR_SAVE_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
# WEBROOT & OUTPUT PATH
WEBROOT = "/var/www/html/pvpjsonstat/"
OUTPUT_JSON_PATH = os.path.join(WEBROOT, "jsons", "rune_inventory.json")
# =======================================================

# Известни кодове, които започват с 'r', но НЕ СА руни:
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

# --- БАЗА ДАННИ ЗА СВОЙСТВАТА НА РУНИТЕ (Трябва да е пълна!) ---
# Включете тук всичките 33 руни
RUNE_STATS = {
    "El Rune": "Light Radius: +1 | Attack Rating: +50", "Eld Rune": "Defense: +7% (Armor/Helm) | Faster Run/Walk: +30% (Shield)",
    "Tir Rune": "Replenish Mana: +2", "Nef Rune": "Knockback (Weapon) | Defense vs. Missile: +30 (Armor/Helm)",
    "Eth Rune": "Monster Defense per Hit: -25% (Weapon) | Regenerate Mana: +15% (Armor/Helm)",
    "Ith Rune": "Magic Damage Reduced: 7", "Ral Rune": "Fire Resistance: +30% (Armor/Helm) | Fire Resist: +35% (Shield)",
    "Ort Rune": "Lightning Resistance: +30% (Armor/Helm) | Lightning Resist: +35% (Shield)",
    "Tal Rune": "Poison Resistance: +30% (Armor/Helm) | Poison Resist: +35% (Shield)",
    "Thul Rune": "Cold Resistance: +30% (Armor/Helm) | Cold Resist: +35% (Shield)",
    "Amn Rune": "Life Stolen per Hit: 7% (Weapon)", "Sol Rune": "Damage Reduced: 7 (Armor/Helm/Shield)",
    "Shael Rune": "Attack Speed: +20% (Weapon) | Faster Hit Recovery: +20% (Armor/Helm) | Faster Block Rate: +20% (Shield)",
    "Dol Rune": "Hit Causes Monster to Flee 25% (Weapon) | Stamina: +7 (Armor/Helm)",
    "Io Rune": "Vitality: +10", "Lum Rune": "Energy: +10", "Ko Rune": "Dexterity: +10", "Fal Rune": "Strength: +10",
    "Lem Rune": "Extra Gold: +50% (Armor/Helm)", "Pul Rune": "Defense: +30% (Armor/Helm) | Resist All: +15 (Shield)",
    "Um Rune": "Resist All: +15 (Armor/Helm) | Resist All: +22 (Shield)",
    "Mal Rune": "Magic Damage Reduced: 7 (Armor/Helm/Shield)", "Ist Rune": "Magic Find: +30% (Weapon) | Magic Find: +25% (Armor/Helm)",
    "Gul Rune": "Attack Rating: +20% (Weapon) | Resist All: +5 (Armor/Helm/Shield)",
    "Vex Rune": "Mana Stolen per Hit: 7% (Weapon) | Half Freeze Duration (Armor/Helm/Shield)",
    "Ohm Rune": "Enhanced Damage: +50% (Weapon) | Defense: +50% (Armor/Helm) | Resist All: +5 (Shield)",
    "Lo Rune": "Deadly Strike: +20% (Weapon) | Resist All: +5 (Armor/Helm/Shield)",
    "Sur Rune": "Maximum Mana: +5% (Armor/Helm) | Mana: +20% (Shield)", "Ber Rune": "Damage Reduced: 8% (Armor/Helm/Shield)",
    "Jah Rune": "Maximum Life: +5% (Armor/Helm) | Life: +20% (Shield)", "Cham Rune": "Cannot be Frozen",
    "Zod Rune": "Indestructible (Weapon/Armor/Helm/Shield)"
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
    total_rune_inventory = defaultdict(lambda: defaultdict(int))
    
    if not os.path.isdir(char_dir):
        print(f"[!!!] ERROR: Директорията за запазване на герои не е намерена: {char_dir}")
        return total_rune_inventory

    for filename in os.listdir(char_dir):
        char_path = os.path.join(char_dir, filename)
        if os.path.isdir(char_path): continue
            
        try:
            d2s = D2SFile(char_path)
            char_name = filename
        except Exception:
            continue

        all_items = list(getattr(d2s, "items", []))
        try: all_items.extend(list(getattr(d2s, "stash", [])))
        except Exception: pass
        
        for item in all_items:
            code = getattr(item, 'code', '')
            if code.startswith('r') and code not in NON_RUNE_CODES:
                if len(code) == 3 and code[1:].isdigit() and 1 <= int(code[1:]) <= 33:
                    name = getattr(item, 'name', 'Unknown Rune')
                    total_rune_inventory[name][char_name] += 1
    return total_rune_inventory


def generate_json_report(inventory: Dict[str, Dict[str, int]], output_path: str):
    """
    Генерира структуриран JSON от инвентара и го записва.
    """
    # 1. Форматиране на данните в списък от обекти за лесно парсване в JS
    json_data = []
    
    for rune_name, char_counts in sorted(inventory.items()):
        total_count = sum(char_counts.values())
        
        # Преобразуване на char_counts от defaultdict в обикновен dict
        # за да бъде коректно сериализиран в JSON
        char_info = dict(char_counts) 
        
        json_data.append({
            "name": rune_name,
            "total_count": total_count,
            "stats": RUNE_STATS.get(rune_name, "Свойствата не са дефинирани"),
            "holders": char_info 
        })
        
    # 2. Проверка и създаване на директорията, ако не съществува
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 3. Записване на JSON файла
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print(f"\n[+] Успешно генериран JSON файл:")
        print(f"    Път: {output_path}")
        print(f"    Общ брой рунически видове: {len(json_data)}")
    except Exception as e:
        print(f"[!!!] ГРЕШКА при записване на JSON: {e}")

if __name__ == "__main__":
    # 1. Изпълнение на сканирането
    all_rune_data = gather_all_runes_detailed(CHAR_SAVE_DIR)
    
    # 2. Генериране на JSON
    generate_json_report(all_rune_data, OUTPUT_JSON_PATH)
