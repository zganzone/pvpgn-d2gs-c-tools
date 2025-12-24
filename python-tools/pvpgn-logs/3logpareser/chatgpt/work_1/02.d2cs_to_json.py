import re
import json
from datetime import datetime, timedelta
from collections import defaultdict

D2CS_LOG = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"
YEAR = 2025
GHOST_TIMEOUT = timedelta(hours=4)

CREATE_RE = re.compile(r"d2cs_game_create: game (\S+).*created")
JOIN_RE = re.compile(r"request join game (\S+) for character (\S+)")
LEAVE_RE = re.compile(r"game_del_character: removed character (\S+) from game (\S+)")
DESTROY_RE = re.compile(r"game_destroy: game (\S+) removed from game list")
TIMESTAMP_RE = re.compile(r"^(\w+ \d+ \d+:\d+:\d+)")

def parse_timestamp(ts):
    return datetime.strptime(f"{YEAR} {ts}", "%Y %b %d %H:%M:%S")

game_sessions = {}
game_name_counts = defaultdict(int)

with open(D2CS_LOG, "r", errors="ignore") as f:
    for line in f:
        ts_match = TIMESTAMP_RE.match(line)
        if not ts_match:
            continue

        ts = parse_timestamp(ts_match.group(1))

        if m := CREATE_RE.search(line):
            game_name = m.group(1)
            game_name_counts[game_name] += 1
            game_id = f"{game_name}_{game_name_counts[game_name]}"
            game_sessions[game_id] = {
                "game_id": game_id,
                "game_name": game_name,
                "start_time": ts.isoformat(sep=" "),
                "end_time": None,
                "players": []
            }

        elif m := JOIN_RE.search(line):
            game_name, character = m.groups()
            game_id = f"{game_name}_{game_name_counts[game_name]}"
            game_sessions[game_id]["players"].append({
                "character": character,
                "join_time": ts.isoformat(sep=" "),
                "leave_time": None
            })

        elif m := LEAVE_RE.search(line):
            character, game_name = m.groups()
            game_id = f"{game_name}_{game_name_counts[game_name]}"
            for p in game_sessions[game_id]["players"]:
                if p["character"] == character and p["leave_time"] is None:
                    p["leave_time"] = ts.isoformat(sep=" ")

        elif m := DESTROY_RE.search(line):
            game_name = m.group(1)
            game_id = f"{game_name}_{game_name_counts[game_name]}"
            game_sessions[game_id]["end_time"] = ts.isoformat(sep=" ")

# ghost games
for g in game_sessions.values():
    if g["end_time"] is None:
        end = datetime.fromisoformat(g["start_time"]) + GHOST_TIMEOUT
        g["end_time"] = end.isoformat(sep=" ")

output = {
    "source": "D2CS",
    "games": list(game_sessions.values())
}

print(json.dumps(output, indent=2, ensure_ascii=False))
