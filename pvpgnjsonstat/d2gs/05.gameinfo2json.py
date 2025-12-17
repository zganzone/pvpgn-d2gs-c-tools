#!/usr/bin/env python3
import json
import re
import os
from typing import Dict, Any

# Paths
ids_file = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/logs/game_ready_ids.txt"
logs_dir = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/logs/cl_output"

all_games = []

# === НОВА ФУНКЦИЯ: ИЗЧИСЛЯВАНЕ НА XP RATE ===
def calculate_xp_rate(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Изчислява XP Rate, базиран на броя на играчите (UserCount)
    по формулата на D2: XP Rate = (n + 1) / 2
    """
    game_info = game_data.get("GameInfo", {})
    user_count_str = game_info.get("UserCount")

    if not user_count_str:
        user_count = 0
    else:
        try:
            user_count = int(user_count_str)
        except ValueError:
            user_count = 0
            
    # XP Rate Calculation
    # Ако UserCount е 0 или 1, множителят е 1.0 (Base XP)
    if user_count >= 1:
        xp_rate = (user_count + 1) / 2
    else:
        xp_rate = 1.0

    # Добавяне на новото поле към GameInfo
    game_info["UserCount"] = user_count # Записваме го като int
    game_info["XPRateMultiplier"] = round(xp_rate, 2)
    
    # Форматиране на бонуса (напр. "+350%")
    xp_bonus_percent = (xp_rate - 1.0) * 100
    game_info["XPBonusPercent"] = f"+{round(xp_bonus_percent):.0f}%"

    game_data["GameInfo"] = game_info
    return game_data
# ============================================

def parse_game_file(filepath):
    game_info = {}
    characters = []

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Parse header info [Key : Value]
    header_pattern = re.compile(r'\[(.*?)\s*:\s*(.*?)\s*\]')
    for line in lines:
        for match in header_pattern.finditer(line):
            key = match.group(1).strip()
            val = match.group(2).strip()
            game_info[key] = val if val else None

    # Parse character table
    char_table_started = False
    for line in lines:
        if line.startswith("+-No"):
            char_table_started = True
            continue
        if char_table_started:
            # Skip separators and empty lines
            if line.startswith("+---") or line.strip() == "":
                continue
            if line.startswith("|"):
                # ... (Parses character data) ...
                no = line[2:6].strip()
                acct = line[6:22].strip()
                charname = line[22:40].strip()
                ip = line[40:58].strip()
                cls = line[58:64].strip()
                lvl = line[64:72].strip()
                time = line[72:80].strip()
                characters.append({
                    "No": no,
                    "AcctName": acct,
                    "CharName": charname,
                    "IPAddress": ip,
                    "Class": cls,
                    "Level": lvl,
                    "EnterTime": time
                })

    return {
        "GameInfo": game_info,
        "Characters": characters
    }

# Read game IDs
with open(ids_file, "r") as f:
    game_ids = [line.strip() for line in f if line.strip()]

# Parse each game's raw log
for gid in game_ids:
    filepath = os.path.join(logs_dir, f"cl_{gid}_raw.txt")
    if os.path.exists(filepath):
        game_json = parse_game_file(filepath)
        
        # === ИЗЧИСЛЯВАНЕ НА XP RATE ВЕЧЕ ТУК ===
        game_json = calculate_xp_rate(game_json)
        
        all_games.append(game_json)
    else:
        print(f"Warning: file {filepath} not found")

# Output combined JSON
with open("/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/logs/all_games_d2.json", "w") as f:
    json.dump(all_games, f, indent=2)

with open("/var/www/html/pvpjsonstat/jsons/all_games_d2.json", "w") as f:
    json.dump(all_games, f, indent=2)


print(f"Processed {len(all_games)} games, output saved to /home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/logs/all_games_d2.json")
print(f"Processed {len(all_games)} games, output saved to /var/www/html/pvpjsonstat/jsons/all_games_d2.json")
