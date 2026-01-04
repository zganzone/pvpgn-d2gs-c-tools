#!/usr/bin/env python3
import os
import re
import json
import copy
from collections import defaultdict
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
CHAR_SAVE_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
D2_DATA_DIR   = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/"
RUNEWORDS_TXT = "runewords.txt"   # смени ако е другаде
JSON_OUT_DIR  = "/var/www/html/pvpjsonstat/new"
JSON_OUT_FILE = os.path.join(JSON_OUT_DIR, "runewords.json")

NON_RUNE_CODES = ['rin', 'rvl', 'rvs', 'rsv', 'rsc', 'rpl', 'rsk']

os.environ['D2_DATA_PATH'] = D2_DATA_DIR
from d2lib.files import D2SFile

# ======================================================
# INVENTORY
# ======================================================
def gather_inventory(char_dir):
    inventory = defaultdict(lambda: defaultdict(int))

    for fname in os.listdir(char_dir):
        path = os.path.join(char_dir, fname)
        if os.path.isdir(path):
            continue
        try:
            d2s = D2SFile(path)
        except Exception:
            continue

        items = list(getattr(d2s, "items", []))
        try:
            items.extend(list(getattr(d2s, "stash", [])))
        except Exception:
            pass

        for item in items:
            code = getattr(item, "code", "")
            if not code.startswith("r") or code in NON_RUNE_CODES:
                continue
            if len(code) == 3 and code[1:].isdigit():
                n = int(code[1:])
                if 1 <= n <= 33:
                    rune = getattr(item, "name", "Unknown Rune")
                    inventory[rune][fname] += 1

    return inventory

# ======================================================
# PARSE RUNEWORDS.TXT
# ======================================================
def parse_runewords(path):
    runewords = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "(" not in line or "+" not in line:
                continue

            m = re.search(r"-\s*(.*?)\s*\((.*?)\)", line)
            if not m:
                continue

            name = m.group(1).strip()
            rune_part = m.group(2)

            runes = []
            for r in rune_part.split("+"):
                r = r.strip().capitalize()
                if not r.endswith("Rune"):
                    r += " Rune"
                runes.append(r)

            runewords[name] = runes

    return runewords

# ======================================================
# SOLVER
# ======================================================
def solve_runeword(name, required, inventory):
    temp = copy.deepcopy(inventory)
    used = defaultdict(list)
    missing = []

    for rune in required:
        found = False
        if rune in temp:
            for char, count in temp[rune].items():
                if count > 0:
                    temp[rune][char] -= 1
                    used[rune].append(char)
                    found = True
                    break
        if not found:
            missing.append(rune)

    return {
        "name": name,
        "can_build": len(missing) == 0,
        "used": dict(used),
        "missing": missing
    }

# ======================================================
# MAIN
# ======================================================
def main():
    os.makedirs(JSON_OUT_DIR, exist_ok=True)

    inventory = gather_inventory(CHAR_SAVE_DIR)
    runewords = parse_runewords(RUNEWORDS_TXT)

    results = []
    for name, runes in sorted(runewords.items()):
        result = solve_runeword(name, runes, inventory)
        results.append(result)

    output = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "inventory": inventory,
        "runewords": results
    }

    with open(JSON_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"[OK] JSON generated: {JSON_OUT_FILE}")
    print(f"[OK] Total runewords: {len(results)}")
    print(f"[OK] Craftable: {sum(1 for r in results if r['can_build'])}")

if __name__ == "__main__":
    main()
