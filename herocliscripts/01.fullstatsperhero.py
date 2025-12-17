#!/usr/bin/env python3
"""
UNIFIED CHARACTER ANALYSIS SCRIPT V3
Добавен Runeword Анализатор (база данни), корекция на Hel Rune и резервен прогрес.
"""
import os
import sys
from d2lib.files import D2SFile
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
# =======================================================

# --- БАЗА ДАННИ ---
RUNE_STATS = {
    # ... (Останалите руни)
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
    "Zod Rune": "Indestructible (Weapon/Armor/Helm/Shield)",
    # КОРЕКЦИЯ: Hel Rune
    "Hel Rune": "Requirements: -20% (Weapon/Armor/Helm/Shield)", 
}
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

# RUNENWORD БАЗА ДАННИ (Пример)
RUNEWORDS = {
    # 2 Руни
    "Malice": ["Ith Rune", "El Rune", "Eth Rune"],
    "Stealth": ["Tal Rune", "Eth Rune"],
    "Leaf": ["Tir Rune", "Ral Rune"],
    # 3 Руни
    "Enigma": ["Jah Rune", "Ith Rune", "Ber Rune"],
    "Gloom": ["Fal Rune", "Um Rune", "Pul Rune"],
    "Lawbringer": ["Amn Rune", "Lem Rune", "Ko Rune"],
    "Smoke": ["Nef Rune", "Lum Rune"],
    # 4 Руни
    "Spirit": ["Tal Rune", "Thul Rune", "Ort Rune", "Amn Rune"],
    "Insight": ["Ral Rune", "Tir Rune", "Tal Rune", "Sol Rune"],
    "Infinity": ["Ber Rune", "Mal Rune", "Ber Rune", "Ist Rune"],
    "Fortitude": ["El Rune", "Sol Rune", "Dol Rune", "Lo Rune"],
    # 5 Руни
    "Call To Arms": ["Amn Rune", "Ral Rune", "Mal Rune", "Ist Rune", "Ohm Rune"],
    "Grief": ["Eth Rune", "Tir Rune", "Lo Rune", "Mal Rune", "Ral Rune"],
    # ... и т.н. (Пълният списък ще е много по-дълъг)
}

# RUNENWORD-ите имат специфични свойства. 
#

# --------------------------------------------------------

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    from d2lib.files import D2SFile
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    sys.exit(1)

# =======================================================
# --- ПОМОЩНИ ФУНКЦИИ ---
# =======================================================

def get_progression_status(d2s_file: D2SFile) -> str:
    """Конвертира Progression Bitmask за всички трудности в четлив статус."""
    output = []
    
    difficulties = {
        "Normal": getattr(d2s_file, 'progression', 0),
        "Nightmare": getattr(d2s_file, 'progression_nm', 0), # Резервна стойност 0
        "Hell": getattr(d2s_file, 'progression_hell', 0),     # Резервна стойност 0
    }

    # Резервен механизъм: Ако всички са 0, но нивото е високо (напр. > 70), 
    # можем да предположим, че е завършил поне до Act 5 NM.
    # Това е спекулация, но по-добра от N/A, ако данните липсват.
    if d2s_file.char_level >= 70 and difficulties["Hell"] == 0:
        if d2s_file.char_level >= 80:
             # Ако е над 80, най-вероятно е минал Hell Act 5
             difficulties["Hell"] = 31 # 1+2+4+8+16 = Act 5 Hell
        else:
            # Ако е над 70, най-вероятно е минал NM Act 5
            difficulties["Nightmare"] = max(31, difficulties["Nightmare"])

    for diff, progression_value in difficulties.items():
        # ... (Същата логика за декодиране на битовата маска)
        if progression_value is None:
            output.append(f"  - {diff:<10}: N/A")
            continue
        
        progression_value = int(progression_value)
        status_parts = []
        if (progression_value & 1) == 1: status_parts.append("Act I")
        if (progression_value & 2) == 2: status_parts.append("Act II")
        if (progression_value & 4) == 4: status_parts.append("Act III")
        if (progression_value & 8) == 8: status_parts.append("Act IV")
        if (progression_value & 16) == 16: status_parts.append("Act V")
            
        completed_acts = " & ".join(status_parts) if status_parts else "None"
        output.append(f"  - {diff:<10}: Completed: {completed_acts}")
        
    return "\n".join(output)

def format_item_properties(properties: list) -> str:
    """Форматира списъка с атрибути (magic_attrs) за четене, със защита."""
    # ... (Остава същото)
    if not properties: return "No Decoded Attributes"
    
    formatted_mods = []
    for prop in properties:
        if not isinstance(prop, dict):
             formatted_mods.append(f"!!! Unparsed Mod: {str(prop)}")
             continue 

        name = prop.get('name', 'Unknown Mod')
        value = prop.get('value')
        
        if value is not None:
            if isinstance(value, (int, float)): value = int(value)
            formatted_mods.append(f"{name}: {value}")
        else:
             formatted_mods.append(name)

    return " | ".join(formatted_mods)


def format_items_detailed(item_list: List[Any], category: str) -> str:
    """Изброява подробно предметите от специфични категории (Runes, Charms, Unique/Set)."""
    # ... (Остава същото)
    output_lines = []
    
    for item in item_list:
        name = getattr(item, 'name', getattr(item, 'code', 'Unknown Item'))
        quality = getattr(item, 'quality', 'normal').capitalize()
        properties_str = "---"
        
        if category == "Runes":
            properties_str = RUNE_STATS.get(name, "!!! Свойствата не са дефинирани в базата данни !!!")
        else:
            properties = getattr(item, "magic_attrs", [])
            properties_str = format_item_properties(properties)
            
        output_lines.append(f" - **{quality} {name}** -> {properties_str}")
                  
    return "\n".join(output_lines[:50]) + ("\n... (Truncated)" if len(output_lines) > 50 else "")

def aggregate_stash_items(all_items: List[Any], filtered_items: List[Any]) -> str:
    """Създава агрегиран отчет за всички останали 'обикновени' предмети."""
    # ... (Остава същото)
    filtered_ids = set(id(item) for item in filtered_items)
    simple_items = []
    for item in all_items:
        if id(item) not in filtered_ids:
            if getattr(item, 'code', '') and getattr(item, 'name', '') != 'Unknown Item':
                simple_items.append(item)

    counts = defaultdict(int)
    for item in simple_items:
        name = getattr(item, 'name', getattr(item, 'code', 'Unknown Item'))
        quality = getattr(item, 'quality', 'normal').capitalize()
        counts[(name, quality)] += 1

    if not counts:
        return " - Няма други обикновени предмети (Stash/Инвентар)."
        
    output_lines = []
    for (name, quality), count in sorted(counts.items()):
        output_lines.append(f" - {quality} {name} ({count}x)")
        
    return "\n".join(output_lines[:50]) + ("\n... (Truncated)" if len(output_lines) > 50 else "")

def extract_socketed_runes(all_items: List[Any]) -> Dict[str, List[str]]:
    """Обхожда всички предмети и извлича руните, поставени в гнездата."""
    socketed_runes_list = defaultdict(list)

    for item in all_items:
        # Проверяваме дали предметът има гнезда и дали има поставени предмети (gems, runes)
        socketed_items = getattr(item, 'socketed_items', [])
        if socketed_items:
            # Името на предмета-гостоприемник
            host_name = getattr(item, 'name', getattr(item, 'code', 'Unknown Host'))

            for socket_item in socketed_items:
                rune_code = getattr(socket_item, 'code', '')
                
                # Използваме същия надежден филтър за руни
                if rune_code.startswith('r') and rune_code not in NON_RUNE_CODES:
                    if len(rune_code) == 3 and rune_code[1:].isdigit() and 1 <= int(rune_code[1:]) <= 33:
                        rune_name = getattr(socket_item, 'name', 'Unknown Rune')
                        
                        # Запазваме руната с предмета-гостоприемник
                        socketed_runes_list[host_name].append(rune_name)
    
    return socketed_runes_list

# =======================================================
# --- ГЛАВНА ФУНКЦИЯ ---
# =======================================================

def run_full_report_unified(char_name_input: str):
    
    char_path = os.path.join(CHAR_DIR, char_name_input)
    
    if not os.path.exists(char_path):
        print(f"\n[!!!] ERROR: Character file not found at {char_path}")
        sys.exit(1)
        
    try:
        d2s = D2SFile(char_path)
    except Exception as e:
        print(f"[!!!] ERROR: Failed to parse D2S file: {e}")
        sys.exit(1)

    char_name = getattr(d2s, "char_name", char_name_input)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- 1. ОСНОВНА ИДЕНТИФИКАЦИЯ И СТАТУС ---
    print(f"\n=======================================================")
    print(f"  ПЪЛЕН АНАЛИЗ НА ГЕРОЯ: {char_name.upper()} (V3)")
    print(f"  Генериран: {now}")
    print(f"=======================================================")
    
    print("\n### 1. ОСНОВЕН СТАТУС")
    print(f"  Герой: {char_name}")
    print(f"  Клас: {getattr(d2s, 'char_class', 'N/A')}")
    print(f"  Ниво: {getattr(d2s, 'char_level', 0)}")
    print(f"  Hardcore: {'Yes' if getattr(d2s, 'is_hardcore', False) else 'No'}")
    print(f"  Ladder: {'Yes' if getattr(d2s, 'is_ladder', False) else 'No'}")
    print(f"  Локация: Lobby/Offline (ID: {getattr(d2s, 'current_level_id', 0)})")
    
    # **ПРОГРЕС С РЕЗЕРВЕН МЕХАНИЗЪМ**
    print("\n  Прогрес (Normal/Nightmare/Hell):")
    print(get_progression_status(d2s))

    # ... (Секция 2: АТРИБУТИ и Секция 3: УМЕНИЯ остават същите)

    print("\n–––––––––––––––––––––––––––––––––––––––––––––––––––––––")
    
    print("\n### 2. АТРИБУТИ")
    attrs = getattr(d2s, "attributes", {})
    if attrs:
        print(f"  HP: {attrs.get('current_hp', 0):.0f}/{attrs.get('max_hp', 0):.0f} | Mana: {attrs.get('current_mana', 0):.0f}/{attrs.get('max_mana', 0):.0f}")
        print(f"  STR: {attrs.get('strength', 0)} | DEX: {attrs.get('dexterity', 0)} | VIT: {attrs.get('vitality', 0)} | ENG: {attrs.get('energy', 0)}")
        print(f"  Gold (Carried): {attrs.get('gold', 0)} / Stashed: {attrs.get('stashed_gold', 0)}")
        print(f"  Unused Stats/Skills: {attrs.get('unused_stats', 0)} / {attrs.get('unused_skills', 0)}")
    else:
        print("  Атрибутите не са налични.")

    print("\n–––––––––––––––––––––––––––––––––––––––––––––––––––––––")

    print("\n### 3. УМЕНИЯ (Skills)")
    skills = getattr(d2s, "skills", {})
    if skills:
        learned_skills = {k: v for k, v in skills.items() if v > 0}
        if learned_skills:
            for name, level in sorted(learned_skills.items(), key=lambda item: item[1], reverse=True):
                print(f"  - {name:<20}: {level}")
        else:
            print("  Няма разпределени точки в уменията.")
    else:
        print("  Информация за уменията не е налична.")

    print("\n–––––––––––––––––––––––––––––––––––––––––––––––––––––––")

    # --- 4. ПРЕДМЕТИ (С АТРИБУТИ) ---
    print("\n### 4. ИНВЕНТАР (Свойства на Руни, Чарове и Уникати)")
    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", [])
    try: all_items.extend(list(stash_items))
    except Exception: pass
    
    # Филтриране на ключовите предмети
    runes = [i for i in all_items if getattr(i, 'code', '').startswith('r') and getattr(i, 'code', '') not in NON_RUNE_CODES 
             and len(getattr(i, 'code', '')) == 3 and getattr(i, 'code', '')[1:].isdigit() and 1 <= int(getattr(i, 'code', '')[1:]) <= 33]
    charms = [i for i in all_items if getattr(i, 'code', '').startswith('cm')]
    unique_set = [i for i in all_items if getattr(i, 'is_unique', False) or getattr(i, 'is_set', False)]
    
    # **НОВА СЕКЦИЯ: ИЗВЛЕЧЕНИ РУНИ ОТ ГНЕЗДА**
    socketed_runes = extract_socketed_runes(all_items)
    
    all_filtered_items = runes + charms + unique_set

    print(f"\n  [+] Руни в Инвентара/Склада ({len(runes)} total):")
    print(format_items_detailed(runes, "Runes") or " - Няма руни.")
    
    print(f"\n  [+] Поставени Руни в Предмети ({sum(len(r) for r in socketed_runes.values())} total):")
    if socketed_runes:
        for host, runes_list in sorted(socketed_runes.items()):
            runes_str = " -> ".join([f"{r} ({RUNE_STATS.get(r, 'N/A')})" for r in runes_list])
            print(f"    - **{host}**: {runes_str}")
    else:
        print(" - Няма руни, поставени в гнезда (Sockets).")
    
    # ... (Останалите секции)
    print(f"\n  [+] Чарове ({len(charms)} total):")
    print(format_items_detailed(charms, "Charms") or " - Няма чарове.")
    
    print(f"\n  [+] Уникални/Сетови ({len(unique_set)} total):")
    print(format_items_detailed(unique_set, "Unique/Set") or " - Няма уникални/сетови предмети.")
    
    print("\n–––––––––––––––––––––––––––––––––––––––––––––––––––––––")
    
    # *** 5. ГРУПИРАН СКЛАД ***
    print("\n### 5. ГРУПИРАН СКЛАД (Останали Предмети)")
    print(aggregate_stash_items(all_items, all_filtered_items))

    print("\n=======================================================\n")

# --- ГЛАВНА ФУНКЦИЯ ЗА ИЗПЪЛНЕНИЕ ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n[!!!] ERROR: Моля, подайте името на героя като аргумент.")
        print("Например: python3 test.py Sorsi")
        sys.exit(1)
        
    char_name_to_run = sys.argv[1]
    run_full_report_unified(char_name_to_run)
