#!/usr/bin/env python3

import json
import re
from datetime import datetime

D2CS_LOG = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"
OUT = "history_games.json"

YEAR = datetime.now().year
MIN_DURATION = 30  # секунди

def parse_ts(line):
    dt = datetime.strptime(line[:15], "%b %d %H:%M:%S")
    return dt.replace(year=YEAR)

games = {}

re_create = re.compile(r"d2cs_game_create: game (\S+)")
re_add = re.compile(r"game_add_character: added character (\S+) to game (\S+)")
re_del = re.compile(r"game_del_character: removed character (\S+) from game (\S+)")
re_destroy = re.compile(r"game_destroy: game (\S+) removed")

with open(D2CS_LOG, "r", errors="ignore") as f:
    for line in f:
        ts = parse_ts(line)

        if m := re_create.search(line):
            game = m.group(1)
            games[game] = {
                "created_at": ts,
                "destroyed_at": None,
                "players": {}
            }

        elif m := re_add.search(line):
            char, game = m.group(1), m.group(2)
            if game in games:
                games[game]["players"][char] = {
                    "joined_at": ts,
                    "left_at": None
                }

        elif m := re_del.search(line):
            char, game = m.group(1), m.group(2)
            if game in games and char in games[game]["players"]:
                games[game]["players"][char]["left_at"] = ts

        elif m := re_destroy.search(line):
            game = m.group(1)
            if game in games:
                games[game]["destroyed_at"] = ts

# 🧹 филтриране на ghost games
final = {}

for game, data in games.items():
    if not data["destroyed_at"]:
        continue

    if not data["players"]:
        continue

    duration = (data["destroyed_at"] - data["created_at"]).total_seconds()
    if duration < MIN_DURATION:
        continue

    final[game] = {
        "created_at": data["created_at"].isoformat(),
        "destroyed_at": data["destroyed_at"].isoformat(),
        "duration_sec": int(duration),
        "players": {}
    }

    for char, pdata in data["players"].items():
        final[game]["players"][char] = {
            "joined_at": pdata["joined_at"].isoformat(),
            "left_at": pdata["left_at"].isoformat() if pdata["left_at"] else None
        }

with open(OUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"[OK] History written to {OUT} ({len(final)} games)")
