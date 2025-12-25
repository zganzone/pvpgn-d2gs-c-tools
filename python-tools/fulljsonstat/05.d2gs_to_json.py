#!/usr/bin/env python3
import re
import json
import os

D2GS_LOG_PATH = "/var/snap/docker/common/var-lib-docker/overlay2/e1efc394f148bc384bd68e45a1be13c240d75d8f3b64445962438720d6d0346e/diff/root/.wine/drive_c/d2gs/d2gs.log"
OUTPUT_DIR = "/var/www/html/pvpjsonstat/logs"

# Създаване на директорията, ако не съществува
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "05.d2gs_to_json.json")

games = {}

enter_game_re = re.compile(
    r"(\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+) D2GSCBEnterGame: (.+?)\(\*(.+?)\)\[L=(\d+),C=(\w+)\]@([\d\.]+) enter game '(.+?)', id=(\d+)\((.+)\)"
)

leave_game_re = re.compile(
    r"(\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+) D2GSCBLeaveGame: (.+?)\(\*(.+?)\)\[L=(\d+),C=(\w+)\] leave game '(.+?)', id=(\d+)\((.+)\)"
)

def parse_extra_info(extra_info):
    parts = extra_info.split(',')
    return {
        "expansion": "Lord of Destruction" if parts[0] == "exp" else parts[0],
        "difficulty": parts[1] if len(parts) > 1 else None,
        "mode": parts[2] if len(parts) > 2 else None,
        "ladder": parts[3] == "ladder" if len(parts) > 3 else False
    }

with open(D2GS_LOG_PATH, "r") as f:
    for line in f:
        line = line.strip()
        
        m = enter_game_re.search(line)
        if m:
            timestamp, character, account, level, char_class, ip, game_name, game_id, extra_info = m.groups()
            extra_parsed = parse_extra_info(extra_info)
            if game_id not in games:
                ts_clean = timestamp.replace("/", "").replace(" ", "").replace(":", "").replace(".", "")
                unique_id = f"{game_name}_{ts_clean}"
                games[game_id] = {
                    "unique_id": unique_id,
                    "game_name": game_name,
                    "start_time": timestamp,
                    "end_time": None,
                    "players": []
                }
            games[game_id]["players"].append({
                "character": character,
                "account": account,
                "level": int(level),
                "class": char_class,
                "ip": ip,
                "join_time": timestamp,
                "leave_time": None,
                **extra_parsed
            })
            continue
        
        m = leave_game_re.search(line)
        if m:
            timestamp, character, account, level, char_class, game_name_check, game_id, extra_info = m.groups()
            game = games.get(game_id)
            if game:
                for p in game["players"]:
                    if p["character"] == character and p["account"] == account and p["leave_time"] is None:
                        p["leave_time"] = timestamp
                        break
                game["end_time"] = timestamp
            continue

games_list = list(games.values())

# Записване на JSON файла
with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    json.dump(games_list, outfile, indent=2, ensure_ascii=False)
