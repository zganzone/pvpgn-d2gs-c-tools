#!/usr/bin/env python3
"""
PvPGN item report - FINAL PRODUCTION VERSION 6.0 (Aggressive Data Loading)
Този скрипт опитва всички известни методи за зареждане на D2 data files.
"""
import os
import glob, json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

# === Configuration ===
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
CHARINFO_DIR = "/usr/local/pvpgn/var/pvpgn/charinfo"
OUTPUT_ALL_ITEMS_JSON = "/var/www/html/pvpjsonstat/jsons/all_items.json" 
OUTPUT_CHARS_DIR = "/var/www/html/pvpjsonstat/jsons/chars/" 
# КЛЮЧОВИЯТ ПЪТ КЪМ TXT ФАЙЛОВЕТЕ
D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 


# --- КРИТИЧЕН БЛОК: АГРЕСИВНО ЗАРЕЖДАНЕ НА D2LIB ДАННИТЕ ---

# 1. Задаваме променлива на средата (Environment Variable)
os.environ['D2_DATA_PATH'] = D2_DATA_DIR
print(f"[*] Set environment variable D2_DATA_PATH to: {D2_DATA_DIR}")

# 2. Сега импортираме D2SFile (след като сме задали Env Var)
try:
    from d2lib.files import D2SFile
    print("[+] D2SFile imported successfully.")
except ImportError:
    print("[!!!] ERROR: Failed to import d2lib.files.D2SFile. Is the d2lib installed?")
    exit(1)
    
D2LIB_LOADED = False
print(f"[*] Attempting to force load D2 data files via static methods...")

try:
    # Опит 1: По-старият метод
    D2SFile.set_data_path(D2_DATA_DIR)
    D2LIB_LOADED = True
    print("[+] SUCCESS: Data loaded via D2SFile.set_data_path.")
except AttributeError:
    # Игнорираме, ако методът липсва (характерно за стари версии)
    pass 
except Exception as e:
    # Игнорираме други грешки
    print(f"[-] D2SFile.set_data_path failed: {e}")


if not D2LIB_LOADED:
    try:
        # Опит 2: Модерният метод
        if hasattr(D2SFile, 'load_data_files'):
            D2SFile.load_data_files(D2_DATA_DIR)
            D2LIB_LOADED = True
            print("[+] SUCCESS: Data loaded via D2SFile.load_data_files.")
    except Exception as e:
        print(f"[-] D2SFile.load_data_files failed: {e}")

if not D2LIB_LOADED:
    # Ако нищо не работи, разчитаме на това, че d2lib ще използва Env Var или вградената логика
    print("[!!!] WARNING: Explicit D2 data loading failed. Relying on Environment Variable.")

# --- КРАЙ НА БЛОКА ЗА ЗАРЕЖДАНЕ ---

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
all_characters_rows: List[Dict[str, Any]] = []


# =======================================================
# --- ХЕЛПЪР ФУНКЦИИ (Остават същите) ---
# =======================================================

CODE_TO_TYPE = {
    "amu": "amulet", "rin": "ring", "bel": "belt",
    "cm1": "charm_small", "cm2": "charm_large", "cm3": "charm_grand",
    "jew": "jewelry", "swd": "weapon", "swf": "weapon", "axe": "weapon",
    "bow": "weapon", "xbow": "weapon", "stf": "weapon", "bst": "weapon",
    "shd": "armor", "plt": "armor", "ht": "armor",
    "gem": "gem", "gld": "gold", "tkp": "token", "tbk": "book", "uap": "helmet",
}

def detect_type_from_code_and_name(code, name):
    if not code: code = ""
    if not name: name = ""
    code = code.lower()
    name = name.lower()
    
    if code in CODE_TO_TYPE: return CODE_TO_TYPE[code]
    
    if "ring" in name or "band" in name: return "ring"
    if "amulet" in name or "gorget" in name or "neck" in name: return "amulet"
    if "belt" in name: return "belt"
    if "charm" in name or "annihilus" in name or "gheed" in name: return "charm"
    if "helm" in name or "crown" in name or "mask" in name: return "helmet"
    if "shield" in name: return "shield"
    
    for kw in ("sword","axe","mace","dagger","bow","crossbow","staff","polearm","spear","hammer"):
        if kw in name: return "weapon"
        
    for kw in ("armor","plate","mail","leather","chain","robe","shield"):
        if kw in name: return "armor"
        
    return "other"

def find_account_for_character(char_filename):
    try:
        for acc in os.listdir(CHARINFO_DIR):
            p = os.path.join(CHARINFO_DIR, acc)
            if not os.path.isdir(p): continue
            try:
                if char_filename in os.listdir(p):
                    return acc
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return "Unknown"

def group_and_format_list(item_list: List[str]) -> List[str]:
    counts = defaultdict(int)
    for item in item_list:
        name = item.get('name', item) if isinstance(item, dict) else item
        counts[name] += 1
    
    formatted_list = []
    for name, count in sorted(counts.items()):
        if count > 1:
            formatted_list.append(f"{name} ({count})")
        else:
            formatted_list.append(name)
            
    return formatted_list

# =======================================================
# --- ГЛАВЕН ЦИКЪЛ ---
# =======================================================

print(f"[*] Starting item data collection from {CHAR_DIR}...")

os.makedirs(OUTPUT_CHARS_DIR, exist_ok=True)


for path in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
    try:
        d2s = D2SFile(path)
    except Exception:
        print(f"[!] Skipping unreadable file: {os.path.basename(path)}")
        continue

    char_fname = os.path.basename(path)
    
    char_name = getattr(d2s, "char_name", None) or char_fname 
    account_name = find_account_for_character(char_fname)
    
    char_attributes = getattr(d2s, "attributes", {})

    stats = {
        "level": getattr(d2s, "char_level", 0),
        "class": getattr(d2s, "char_class", "N/A"),
        "is_hc": getattr(d2s, "is_hardcore", False),
        "is_ladder": getattr(d2s, "is_ladder", False),
        "progression": getattr(d2s, "progression", None),
        "char_name_raw": char_name
    }
    stats.update(char_attributes)
    
    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", None) 
    if stash_items:
        try:
            all_items.extend(list(stash_items))
        except Exception:
            pass
            
    categorized_items = defaultdict(list)
    
    for item in all_items:
        name = getattr(item, "name", "") or ""
        code = getattr(item, "code", "") or ""
        is_unique = getattr(item, "is_unique", False)
        is_set = getattr(item, "is_set", False)
        is_rune = getattr(item, "is_rune", False)
        rid = getattr(item, "rune_id", None)
        item_properties = getattr(item, "magic_attrs", []) # ДЕКОДИРАНИ СВОЙСТВА!

        item_obj = {"name": name, "properties": item_properties}
        
        # 1. Unique/Set
        if is_unique or is_set:
            item_obj["type"] = "unique" if is_unique else "set"
            categorized_items["unique_set"].append(item_obj)
            continue
        
        # 2. Runes
        if is_rune or (rid is not None and not name):
            runes_name = name or (f"Rune ID {rid}" if rid is not None else "Rune (Unknown)")
            # За runes запазваме само името, защото атрибутите им са стандартни и не се търсят
            categorized_items["runes"].append({"name": runes_name, "properties": []}) 
            continue
            
        # 3. Charms detection
        code_l = code.lower()
        if code_l.startswith("cm"):
            if code_l.startswith("cm1"): categorized_items["charms_small"].append(item_obj)
            elif code_l.startswith("cm2"): categorized_items["charms_large"].append(item_obj)
            elif code_l.startswith("cm3"): categorized_items["charms_grand"].append(item_obj)
            else: categorized_items["charms_small"].append(item_obj)
            continue

        # 4. General item type categorization
        itype = detect_type_from_code_and_name(code, name)

        # Map to final category keys
        use_object = (item_properties and len(item_properties) > 0)
        
        # За предмети, които не са Unique/Set/Charm, запазваме обекта, само ако има атрибути, 
        # в противен случай запазваме само името (низ), за да е лек JSON-ът.
        final_item = item_obj if use_object else name 
        
        if itype == "ring": categorized_items["rings"].append(final_item)
        elif itype == "belt": categorized_items["belts"].append(final_item)
        elif itype == "amulet": categorized_items["amulets"].append(final_item)
        elif itype == "weapon": categorized_items["weapons"].append(final_item)
        elif itype in ("armor","helmet","shield"): categorized_items["armors"].append(final_item)
        else: categorized_items["other"].append(final_item)


    # --- 1. ГЕНЕРИРАНЕ НА ИНДИВИДУАЛЕН JSON (ПЪЛЕН ДОКЛАД) ---
    full_char_data = {
        "account": account_name,
        "charfile": char_fname,
        "charname": char_name,
        "generated": timestamp,
        "char_stats": stats, 
        
        "unique_set": categorized_items["unique_set"],
        "runes": categorized_items["runes"],
        "rings": categorized_items["rings"],
        "belts": categorized_items["belts"],
        "amulets": categorized_items["amulets"],
        "charms_small": categorized_items["charms_small"],
        "charms_large": categorized_items["charms_large"],
        "charms_grand": categorized_items["charms_grand"],
        "weapons": categorized_items["weapons"],
        "armors": categorized_items["armors"],
        "other": categorized_items["other"],
    }
    
    char_json_name = f"{char_name.lower().replace(' ', '_')}.json"
    char_json_path = os.path.join(OUTPUT_CHARS_DIR, char_json_name)
    try:
        with open(char_json_path, "w", encoding="utf-8") as jf:
            json.dump(full_char_data, jf, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Failed to write individual JSON file {char_json_name}: {e}")

    # --- 2. ГЕНЕРИРАНЕ НА РЕД ЗА ОБЩИЯ JSON (С АТРИБУТИ ЗА ТЪРСЕНЕ) ---
    # *ПРОМЯНА: НЕ използваме group_and_format_list за категориите с атрибути!*
    
    all_charms = categorized_items["charms_small"] + categorized_items["charms_large"] + categorized_items["charms_grand"]
    
    row_for_all_items = {
        "account": account_name,
        "charfile": char_fname,
        "charname": char_name,
        "level": stats.get("level", 0),
        "class": stats.get("class", "N/A"),
        
        # ЗАПИСВАМЕ ПЪЛНИТЕ ОБЕКТИ С АТРИБУТИ
        "unique_set": categorized_items["unique_set"],
        "runes": categorized_items["runes"],
        "charms": all_charms, # Обединените чармове

        # Връщаме групирания формат само за останалите (за да не претрупваме all_items.json)
        # Тези категории може да съдържат низ или обект
        "rings": categorized_items["rings"],
        "belts": categorized_items["belts"],
        "amulets": categorized_items["amulets"],
        "weapons": categorized_items["weapons"],
        "armors": categorized_items["armors"],
        "other": categorized_items["other"],
    }
    all_characters_rows.append(row_for_all_items)


# === Save the ALL ITEMS JSON export ===
final_json = {
    "generated": timestamp, 
    "rows": all_characters_rows
}
try:
    with open(OUTPUT_ALL_ITEMS_JSON, "w", encoding="utf-8") as jf:
        json.dump(final_json, jf, ensure_ascii=False, indent=2)
    print(f"[+] General report generated successfully: {OUTPUT_ALL_ITEMS_JSON} ({len(all_characters_rows)} characters)")
except Exception as e:
    print(f"[!] Failed to write general JSON file: {e}")
