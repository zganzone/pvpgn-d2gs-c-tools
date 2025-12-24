#!/usr/bin/env python3
import os, json, re
from datetime import datetime, timedelta

# === CONFIG ===
YEAR = datetime.now().year
MIN_DURATION = 30  # seconds
WORK_DIR = "/home/support/scripts-tools/d2cpp/python-tools/pvpgn-logs/v_2"
LOG_D2CS = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"

HISTORY_DIR = os.path.join(WORK_DIR, "history")
GAMES_DIR = os.path.join(HISTORY_DIR, "games")
INDEX_FILE = os.path.join(HISTORY_DIR, "index.json")

os.makedirs(GAMES_DIR, exist_ok=True)

# === REGEX ===
re_create = re.compile(r"d2cs_game_create: game (\S+)")
re_add = re.compile(r"game_add_character: added character (\S+) to game (\S+)")
re_del = re.compile(r"game_del_character: removed character (\S+) from game (\S+)")
re_destroy = re.compile(r"game_destroy: game (\S+) removed")

# === PARSE TIME ===
def parse_ts(line):
    dt = datetime.strptime(line[:15], "%b %d %H:%M:%S")
    return dt.replace(year=YEAR)

# === IN-MEMORY DATA ===
games = {}

with open(LOG_D2CS, "r", errors="ignore") as f:
    for line in f:
        ts = parse_ts(line)

        if m := re_create.search(line):
            game_name = m.group(1)
            game_uid = f"{ts.strftime('%Y%m%d%H%M%S')}_{game_name}"
            games[game_name] = {
                "game_uid": game_uid,
                "created_at": ts,
                "destroyed_at": None,
                "players": {}
            }

        elif m := re_add.search(line):
            char, game_name = m.group(1), m.group(2)
            if game_name in games:
                if char not in games[game_name]["players"]:
                    games[game_name]["players"][char] = {"sessions": []}
                games[game_name]["players"][char]["sessions"].append({"join": ts, "leave": None})

        elif m := re_del.search(line):
            char, game_name = m.group(1), m.group(2)
            if game_name in games and char in games[game_name]["players"]:
                # close last session
                for sess in reversed(games[game_name]["players"][char]["sessions"]):
                    if sess["leave"] is None:
                        sess["leave"] = ts
                        break

        elif m := re_destroy.search(line):
            game_name = m.group(1)
            if game_name in games:
                games[game_name]["destroyed_at"] = ts

# === FILTER + AGGREGATE ===
final_index = {"total_games": 0, "games": []}

for game_name, gdata in games.items():
    if not gdata["destroyed_at"]:
        continue
    if not gdata["players"]:
        continue
    duration = (gdata["destroyed_at"] - gdata["created_at"]).total_seconds()
    if duration < MIN_DURATION:
        continue

    # aggregate per player
    for char, pdata in gdata["players"].items():
        join_count = len(pdata["sessions"])
        total_time = sum(
            (sess["leave"] - sess["join"]).total_seconds() if sess["leave"] else 0
            for sess in pdata["sessions"]
        )
        max_session = max(
            ((sess["leave"] - sess["join"]).total_seconds() if sess["leave"] else 0)
            for sess in pdata["sessions"]
        )
        pdata["join_count"] = join_count
        pdata["total_time_sec"] = int(total_time)
        pdata["max_session_sec"] = int(max_session)
        # optional: convert session timestamps to ISO
        for sess in pdata["sessions"]:
            sess["join"] = sess["join"].isoformat()
            sess["leave"] = sess["leave"].isoformat() if sess["leave"] else None

    # convert game timestamps to ISO
    gdata["created_at"] = gdata["created_at"].isoformat()
    gdata["destroyed_at"] = gdata["destroyed_at"].isoformat()
    gdata["duration_sec"] = int(duration)

    # write per-game JSON
    game_file = os.path.join(GAMES_DIR, f"{gdata['game_uid']}.json")
    with open(game_file, "w") as f:
        json.dump(gdata, f, indent=2)

    # update index
    final_index["games"].append({
        "game_uid": gdata["game_uid"],
        "game_name": game_name,
        "players": len(gdata["players"]),
        "duration_sec": int(duration)
    })

final_index["total_games"] = len(final_index["games"])

# sort index by game name
final_index["games"].sort(key=lambda x: x["game_name"])

with open(INDEX_FILE, "w") as f:
    json.dump(final_index, f, indent=2)

print(f"[OK] Processed {len(final_index['games'])} games. JSON files in {GAMES_DIR}")
