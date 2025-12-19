#!/usr/bin/env python3
"""
UNIFIED CHARACTER ANALYSIS SCRIPT (FINAL)
Изпълнява пълен анализ на герой (Атрибути, Скилове, Прогрес, Руни, Чарове, Предмети)
Героят се подава като аргумент от командния ред (e.g., python3 test.py Sorsi)
"""
import os
import sys
from d2lib.files import D2SFile
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
# КЛЮЧОВИЯТ ПЪТ КЪМ TXT ФАЙЛОВЕТЕ
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
# =======================================================

# --- ХАРДКОДНА БАЗА ДАННИ ЗА СВОЙСТВАТА НА РУНИТЕ (ВСИЧКИ 33) ---
# Използва се, тъй като d2lib не декодира техните magic_attrs надеждно.
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
# Известни кодове, които започват с 'r', но НЕ СА руни:
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

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

def get_progression_status(progression_value: Optional[int]) -> str:
    """Конвертира Progression Bitmask в четлив статус (по Актов Прогрес)."""
    if progression_value is None: return "N/A"
    status_parts = []
    if (progression_value & 1) == 1: status_parts.append("Act I")
    if (progression_value & 2) == 2: status_parts.append("Act II")
    if (progression_value & 4) == 4: status_parts.append("Act III")
    if (progression_value & 8) == 8: status_parts.append("Act IV")
    if (progression_value & 16) == 16: status_parts.append("Act V")
    completed_acts = " & ".join(status_parts) if status_parts else "None"
    return f"Completed: {completed_acts}"

def format_item_properties(properties: list) -> str:
    """Форматира списъка с атрибути (magic_attrs) за четене, като се защитава срещу грешки."""
    if not properties:
        return ""
    
    formatted_mods = []
    for prop in properties:
        # **КРИТИЧНА ПРОВЕРКА: Игнорираме елементи, които не са речници (за защита от string грешка)**
        if not isinstance(prop, dict):
             formatted_mods.append(f"!!! Unparsed Mod: {str(prop)}")
             continue 

        name = prop.get('name', 'Unknown Mod')
        value = prop.get('value')
        
        if value is not None:
            if isinstance(value, (int, float)):
                 # Закръгляме до цяло число, тъй като d2lib често връща float
                 value = int(value)
            formatted_mods.append(f"{name}: {value}")
        else:
             # За модификатори без стойност (напр. socketed, Ethereal)
             formatted_mods.append(name)

    return " | ".join(formatted_mods) if formatted_mods else "No Decoded Attributes"


def format_items_detailed(item_list: List[Any], category: str) -> str:
    """Групира и форматира списък от предмети, като включва и атрибутите."""
    output_lines = []
    
    for item in item_list:
        name = getattr(item, 'name', getattr(item, 'code', 'Unknown Item'))
        quality = getattr(item, 'quality', 'normal').capitalize()
        
        properties_str = "---"
        
        if category == "Runes":
            # Използваме хардкодната база данни за руните
            properties_str = RUNE_STATS.get(name, "!!! Свойствата не са дефинирани в базата данни !!!")
        else:
            # За Чарове и Уникати използваме декодера на d2lib, със защита.
            properties = getattr(item, "magic_attrs", [])
            properties_str = format_item_properties(properties)
            
        output_lines.append(f" - **{quality} {name}** -> {properties_str}")
                  
    return "\n".join(output_lines[:50]) + ("\n... (Truncated)" if len(output_lines) > 50 else "")

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
    print(f"  ПЪЛЕН АНАЛИЗ НА ГЕРОЯ: {char_name.upper()}")
    print(f"  Генериран: {now}")
    print(f"=======================================================")
    
    print("\n### 1. ОСНОВЕН СТАТУС")
    print(f"  Герой: {char_name}")
    print(f"  Клас: {getattr(d2s, 'char_class', 'N/A')}")
    print(f"  Ниво: {getattr(d2s, 'char_level', 0)}")
    print(f"  Hardcore: {'Yes' if getattr(d2s, 'is_hardcore', False) else 'No'}")
    print(f"  Ladder: {'Yes' if getattr(d2s, 'is_ladder', False) else 'No'}")
    print(f"  Локация: Lobby/Offline (ID: {getattr(d2s, 'current_level_id', 0)})")
    print(f"  Прогрес (Normal): {get_progression_status(getattr(d2s, 'progression', None))}")

    print("\n–––––––––––––––––––––––––––––––––––––––––––––––––––––––")
    
    # --- 2. АТРИБУТИ (STATS) ---
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

    # --- 3. УМЕНИЯ (SKILLS) ---
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
    
    # ФИЛТРИРАНЕ С НАЙ-ГОЛЯМА НАДЕЖДНОСТ
    # Руни: По код
    runes = [i for i in all_items if getattr(i, 'code', '').startswith('r') and getattr(i, 'code', '') not in NON_RUNE_CODES 
             and len(getattr(i, 'code', '')) == 3 and getattr(i, 'code', '')[1:].isdigit() and 1 <= int(getattr(i, 'code', '')[1:]) <= 33]
    # Чармове: По код
    charms = [i for i in all_items if getattr(i, 'code', '').startswith('cm')]
    # Unique/Set
    unique_set = [i for i in all_items if getattr(i, 'is_unique', False) or getattr(i, 'is_set', False)]

    print(f"\n  [+] Руни ({len(runes)} total):")
    print(format_items_detailed(runes, "Runes") or " - Няма руни.")
    
    print(f"\n  [+] Чарове ({len(charms)} total):")
    print(format_items_detailed(charms, "Charms") or " - Няма чарове.")
    
    print(f"\n  [+] Уникални/Сетови ({len(unique_set)} total):")
    print(format_items_detailed(unique_set, "Unique/Set") or " - Няма уникални/сетови предмети.")
    
    print("\n=======================================================\n")

# --- ГЛАВНА ФУНКЦИЯ ЗА ИЗПЪЛНЕНИЕ ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n[!!!] ERROR: Моля, подайте името на героя като аргумент.")
        print("Например: python3 test.py Sorsi")
        sys.exit(1)
        
    char_name_to_run = sys.argv[1]
    run_full_report_unified(char_name_to_run)
