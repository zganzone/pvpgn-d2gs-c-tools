#!/usr/bin/env python3
"""
Скрипт за откриване на руните в инвентара на 'runione', 
като показва техните свойства от хардкодна база данни.
"""
import os
import sys
from d2lib.files import D2SFile
from typing import List, Any
from collections import defaultdict

# =======================================================
# --- КОНФИГУРАЦИЯ ---
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
TARGET_CHAR_FILE_RUNIONE = "ohm"
TEST_CHAR_PATH = os.path.join("/usr/local/pvpgn/var/pvpgn/charsave", TARGET_CHAR_FILE_RUNIONE)
# =======================================================

# Известни кодове, които започват с 'r', но НЕ СА руни:
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

# --- ХАРДКОДНА БАЗА ДАННИ ЗА СВОЙСТВАТА НА РУНИТЕ (замества d2lib) ---
RUNE_STATS = {
    "El Rune": "Light Radius: +1 | Attack Rating: +50",
    "Eld Rune": "Defense: +7% (Armor/Helm) | Faster Run/Walk: +30% (Shield)",
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
}
# -------------------------------------------------------------------

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    from d2lib.files import D2SFile
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    sys.exit(1)


def find_runes_with_stats(char_path: str):
    
    if not os.path.exists(char_path):
        print(f"\n[!!!] ERROR: Character file not found at {char_path}")
        return
        
    try:
        d2s = D2SFile(char_path)
    except Exception as e:
        print(f"[!!!] ERROR: Failed to parse D2S file: {e}")
        return

    char_name = getattr(d2s, "char_name", "N/A")
    
    print(f"\n=======================================================")
    print(f"  RUNE ATTRIBUTE REPORT: {char_name.upper()} (Using Static Data)")
    print(f"=======================================================")

    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", [])
    try: all_items.extend(list(stash_items))
    except Exception: pass

    found_runes = []
    
    for item in all_items:
        code = getattr(item, 'code', '')
        
        # Надеждно филтриране по код (както в предишния успешен скрипт)
        if code.startswith('r') and code not in NON_RUNE_CODES:
            if len(code) == 3 and code[1:].isdigit() and 1 <= int(code[1:]) <= 33:
                name = getattr(item, 'name', 'Unknown Rune')
                found_runes.append(name)
        
    if not found_runes:
        print("  [---] НЕ БЯХА ОТКРИТИ РУНИ в инвентара на " + char_name)
        return

    # Групиране за по-добър изглед
    counts = defaultdict(int)
    for name in found_runes:
        counts[name] += 1
        
    total_count = sum(counts.values())
    print(f"\n  [+] Открити Руни ({total_count} total):")

    for name, count in sorted(counts.items()):
        
        stats = RUNE_STATS.get(name, "!!! Свойствата не са дефинирани в базата данни !!!")
        
        print(f"\n  > {name} ({count}x):")
        print(f"    - **Бонуси:** {stats}")
        
    print("\n=======================================================\n")

if __name__ == "__main__":
    find_runes_with_stats(TEST_CHAR_PATH)
