#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path
import re

D2CS_LOG = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"
OUT = "/var/www/html/pvpjsonstat/logs/active/active_state.json"

YEAR = datetime.now().year

def parse_ts(line):
    dt = datetime.strptime(line[:15], "%b %d %H:%M:%S")
    return dt.replace(year=YEAR).isoformat()

games = {}
players = {}

re_game_create = re.compile(r"d2cs_game_create: game (\S+)")
re_game_add = re.compile(r"game_add_character: added character (\S+) to game (\S+)")
re_game_del = re.compile(r"game_del_character: removed character (\S+) from game (\S+)")
re_game_destroy = re.compile(r"game_destroy: game (\S+) removed")

with open(D2CS_LOG, "r", errors="ignore") as f:
    for line in f:
        ts = parse_ts(line)

        if m := re_game_create.search(line):
            game = m.group(1)
            games[game] = {
                "created_at": ts,
                "players": {}
            }

        elif m := re_game_add.search(line):
            char, game = m.group(1), m.group(2)
            if game in games:
                games[game]["players"][char] = ts
                players[char] = {"game": game}

        elif m := re_game_del.search(line):
            char, game = m.group(1), m.group(2)
            if game in games:
                games[game]["players"].pop(char, None)
            players.pop(char, None)

        elif m := re_game_destroy.search(line):
            game = m.group(1)
            if game in games:
                for char in list(games[game]["players"].keys()):
                    players.pop(char, None)
                del games[game]

state = {
    "games": games,
    "players": players
}

with open(OUT, "w") as f:
    json.dump(state, f, indent=2)

print(f"[OK] Active state written to {OUT}")
