#!/usr/bin/env python3
import json
import re
import os

# Paths
ids_file = "logs/game_ready_ids.txt"
logs_dir = "logs/cl_output"

all_games = []

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
            if line.startswith("+---") or line.strip() == "":
                continue
            if line.startswith("|"):
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
        all_games.append(game_json)
    else:
        print(f"Warning: file {filepath} not found")

# Output combined JSON
with open("logs/all_games.json", "w") as f:
    json.dump(all_games, f, indent=2)

with open("/var/www/html/d2console/all_games.json", "w") as f:
    json.dump(all_games, f, indent=2)


print(f"Processed {len(all_games)} games, output saved to logs/all_games.json")
print(f"Processed {len(all_games)} games, output saved to /var/www/html/d2console/all_games.json")
