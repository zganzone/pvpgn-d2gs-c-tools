#!/usr/bin/env python3
"""
Rune Finder Tool (CLI) - Анализира инвентара на всички герои 
за необходимите руни чрез директно четене на D2S файлове.
"""
import os
import sys
import glob
from collections import defaultdict
from typing import List, Dict, Tuple, Any

# --- КОНФИГУРАЦИЯ И RUNEWORDS ---
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk'] # Кодове за филтриране

# RUNEWORD БАЗА ДАННИ
RUNEWORDS = {
    # 2 Руни
    "Stealth": ["Tal Rune", "Eth Rune"],
    "Leaf": ["Tir Rune", "Ral Rune"],
    "Malice": ["Ith Rune", "El Rune", "Eth Rune"],
    # 3 Руни
    "Smoke": ["Nef Rune", "Lum Rune"],
    "Lawbringer": ["Amn Rune", "Lem Rune", "Ko Rune"],
    "Enigma": ["Jah Rune", "Ith Rune", "Ber Rune"],
    "Gloom": ["Fal Rune", "Um Rune", "Pul Rune"],
    "Treachery": ["Shael Rune", "Thul Rune", "Lem Rune"],
    # 4 Руни
    "Spirit": ["Tal Rune", "Thul Rune", "Ort Rune", "Amn Rune"],
    "Insight": ["Ral Rune", "Tir Rune", "Tal Rune", "Sol Rune"],
    "Fortitude": ["El Rune", "Sol Rune", "Dol Rune", "Lo Rune"],
    "Infinity": ["Ber Rune", "Mal Rune", "Ber Rune", "Ist Rune"],
    "Flickering Flame": ["Nef Rune", "Pul Rune", "Vex Rune"],
    # 5 Руни
    "Call To Arms": ["Amn Rune", "Ral Rune", "Mal Rune", "Ist Rune", "Ohm Rune"],
    "Grief": ["Eth Rune", "Tir Rune", "Lo Rune", "Mal Rune", "Ral Rune"],
    "Obsession": ["Zod Rune", "Ist Rune", "Lem Rune", "Lum Rune", "Io Rune"],
}

# --- D2LIB ЗАРЕЖДАНЕ ---
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
try:
    # Трябва да импортираме D2SFile, за да прочетем файловете
    from d2lib.files import D2SFile
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is d2lib installed?")
    sys.exit(1)


# =======================================================
# --- ОСНОВНИ ФУНКЦИИ ---
# =======================================================

def is_valid_rune(item: Any) -> bool:
    """Проверява дали даден предмет е свободна руна."""
    code = getattr(item, 'code', '')
    if code.startswith('r') and code not in NON_RUNE_CODES:
         # Допълнителна проверка за код r01 до r33
         if len(code) == 3 and code[1:].isdigit() and 1 <= int(code[1:]) <= 33:
            # Трябва да е свободна, а не поставена в гнездо (d2lib не винаги го засича 
            # перфектно, но това е най-добрият филтър)
            if not getattr(item, 'is_socketed', False):
                 return True
    return False

def load_global_rune_inventory(char_dir: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Сканира всички D2S файлове и събира всички свободни руни.
    Връща: {'Jah Rune': [('Sorsi', 'Stash'), ('Zganvarin', 'Inventory')], ...}
    """
    global_inventory = defaultdict(list)
    char_files = glob.glob(os.path.join(char_dir, "*"))
    
    print(f"[*] Сканиране на {len(char_files)} геройски файла...")

    for path in char_files:
        try:
            d2s = D2SFile(path)
            char_name = getattr(d2s, "char_name", os.path.basename(path))
        except Exception:
            continue # Пропускаме нечетливите или невалидни файлове

        all_items = list(getattr(d2s, "items", []))
        stash_items = getattr(d2s, "stash", [])
        try: all_items.extend(list(stash_items))
        except Exception: pass
        
        # Обхождаме всички предмети и филтрираме за свободни руни
        for item in all_items:
            if is_valid_rune(item):
                rune_name = getattr(item, 'name', 'Unknown Rune')
                # Определяме локацията (проста евристика: Stash/Inventory)
                location = "Stash" if getattr(item, 'is_in_stash', False) else "Inventory"
                
                global_inventory[rune_name].append((char_name, location))
                
    print(f"[*] Сканирането приключи. Намерени {sum(len(v) for v in global_inventory.values())} свободни руни.")
    return global_inventory

def find_runeword_materials(target_runeword: str, global_inventory: Dict[str, List[Tuple[str, str]]]):
    """
    Проверява дали необходимите руни са налични.
    """
    
    # Нормализиране на името
    target_rw = target_runeword.title()
    # Специална обработка за Runewords с главни букви
    if "call to arms" in target_runeword.lower(): target_rw = "Call To Arms"
    if "flickering flame" in target_runeword.lower(): target_rw = "Flickering Flame"
        
    required_runes = RUNEWORDS.get(target_rw)

    if not required_runes:
        print(f"\n[!!!] ERROR: Runeword '{target_runeword}' не е намерен в базата данни.")
        print("Налични Runewords:", ", ".join(RUNEWORDS.keys()))
        return

    print(f"\n=======================================================")
    print(f"  АНАЛИЗ ЗА RUNEWORD: {target_rw.upper()}")
    print(f"  ИЗИСКВА: {len(required_runes)} Руни: {', '.join(required_runes)}")
    print(f"=======================================================")

    missing_runes = []
    found_runes = []
    # Създаваме копие на инвентара, за да можем да "използваме" руните
    temp_inventory = {rune: list(locations) for rune, locations in global_inventory.items()}

    # Проверка на всяка необходима руна в инвентара
    for required_rune in required_runes:
        if required_rune in temp_inventory and temp_inventory[required_rune]:
            # Взимаме първата налична руна и я премахваме от инвентара
            char_location = temp_inventory[required_rune].pop(0)
            found_runes.append((required_rune, char_location))
        else:
            missing_runes.append(required_rune)

    ### ГЕНЕРИРАНЕ НА ОТЧЕТ ###
    
    print("\n### 1. ЗАКЛЮЧЕНИЕ")
    if not missing_runes:
        print(f"  ✅ **УСПЕХ!** Всички руни за **{target_rw}** са налични.")
    else:
        print(f"  ❌ **ЛИПСВАТ РУНИ!** За завършване на **{target_rw}** Ви липсват {len(missing_runes)} руни.")

    print("\n### 2. НАЛИЧНИ РУНИ (Къде да ги намерите)")
    if found_runes:
        for rune, (char, location) in found_runes:
            print(f"  ✅ **{rune:<12}** -> Наличен при **{char}** в {location}")
    else:
        print("  (Не са намерени руни за този Runeword)")

    print("\n### 3. ЛИПСВАЩИ РУНИ")
    if missing_runes:
        for rune in missing_runes:
            # Проверяваме дали имаме по-ниски руни, които могат да бъдат ъпгрейднати (само за информация)
            # Тази проверка е сложна и ще я пропуснем за момента, за да не усложняваме.
            print(f"  ❌ **{rune}** -> Трябва да намерите.")
    else:
        print("  Няма липсващи руни.")
        
    print("\n-------------------------------------------------------")


# =======================================================
# --- ГЛАВНА ТОЧКА НА ВХОД ---
# =======================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n[!!!] ERROR: Моля, подайте името на Runeword-а като аргумент (в кавички).")
        print("Например: python3 findruneword.py \"Call To Arms\"")
        sys.exit(1)
        
    # Взимаме всички аргументи след името на скрипта и ги обединяваме
    runeword_name = " ".join(sys.argv[1:])
    
    # 1. Зареждане на глобалния инвентар
    global_rune_inventory = load_global_rune_inventory(CHAR_DIR)
    
    # 2. Търсене на Runeword
    find_runeword_materials(runeword_name, global_rune_inventory)
