#!/usr/bin/env python3
import re
import json
import subprocess
import os # NEW: Added for file path operations
import sys # NEW: Added for error output
from datetime import datetime, timezone # MODIFIED: Added timezone

# ---- CONFIG ----
BNETD_LOG = "/usr/local/pvpgn/var/pvpgn/logs/bnetd.log"
D2CS_LOG  = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"
LINES = 1000
TIME_FMT = "%b %d %H:%M:%S"
CURRENT_YEAR = datetime.now().year

# --- NEW CONFIG FOR OUTPUTS ---
# !!! ADJUST THIS PATH IF YOUR LOGS ARE NOT HERE !!!
OUTPUT_DIR = "/var/www/html/pvpjsonstat/logs/"
FULL_GAMES_OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'active_games.json')
RECENT_GAMES_OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'recent_games.json')
RECENT_GAMES_COUNT = 100 # Брой последни унищожени игри за втория файл


# ---- STATE ----
games = {}
char_account = {}

# ---- HELPERS ----
def tail(file, regex):
    cmd = f"tail -n {LINES} {file} | grep -E '{regex}'"
    out = subprocess.getoutput(cmd)
    return out.splitlines() if out else []

def parse_ts(line):
    dt = datetime.strptime(line[:15], TIME_FMT)
    return dt.replace(year=CURRENT_YEAR).isoformat()

def get_game(name):
    return games.setdefault(name, {
        "state": "none",
        "players": {}
    })

# =========================
# d2cs.log  (INFO)
# ... (Останалата логика за парсване остава непроменена)
# =========================
for line in tail(D2CS_LOG, r"\[info"):
    try:
        ts = parse_ts(line)
    except Exception:
        continue

    # game create
    if "d2cs_game_create" in line:
        m = re.search(r"game\s+(\S+)", line)
        if not m:
            continue
        game = m.group(1)
        g = get_game(game)
        g["created_at"] = ts
        g["state"] = "created"

    # add character
    elif "game_add_character" in line:
        m = re.search(r"character\s+(\S+)\s+to\s+game\s+(\S+)", line)
        if not m:
            continue
        char, game = m.groups()
        g = get_game(game)
        g["state"] = "active"
        p = g["players"].setdefault(char, {})
        p["joined_at"] = ts

    # remove character
    elif "game_del_character" in line:
        m = re.search(r"character\s+(\S+)\s+from\s+game\s+(\S+)", line)
        if not m:
            continue
        char, game = m.groups()
        g = games.get(game)
        if not g:
            continue
        p = g["players"].get(char)
        if p and "joined_at" in p:
            start = datetime.fromisoformat(p["joined_at"])
            end = datetime.fromisoformat(ts)
            p["left_at"] = ts
            p["playtime_sec"] = int((end - start).total_seconds())

# =========================
# bnetd.log (INFO|DEBUG|TRACE)
# =========================
for line in tail(BNETD_LOG, r"\[(info|debug|trace)"):
    try:
        ts = parse_ts(line)
    except Exception:
        continue

    # game request
    if "game_create:" in line:
        m = re.search(r'game\s+"([^"]+)"', line)
        if not m:
            continue
        game = m.group(1)
        g = get_game(game)
        g["requested_at"] = ts
        g["state"] = "requested"

    # game started (CRITICAL)
    elif "_client_startgame4" in line:
        m = re.search(r'game\s+"([^"]+)"', line)
        if not m:
            continue
        game = m.group(1)
        g = get_game(game)
        g["started_at"] = ts
        g["state"] = "started"

    # account joined game
    elif "joined game" in line:
        m = re.search(r'"([^"]+)"\s+joined\s+game\s+"([^"]+)"', line)
        if not m:
            continue
        acc, game = m.groups()
        g = get_game(game)
        for p in g["players"].values():
            p.setdefault("account", acc)

    # character login (account correlation)
    elif "charloginreq" in line:
        m = re.search(r"character\s+(\S+)\(\*(\S+)\)", line)
        if not m:
            continue
        char, acc = m.groups()
        char_account[char] = acc

    # game destroy
    elif "game_destroy" in line:
        m = re.search(r'game\s+"([^"]+)"', line)
        if not m:
            continue
        game = m.group(1)
        g = games.get(game)
        if g:
            g["destroyed_at"] = ts
            g["state"] = "destroyed"

# =========================
# FINAL ACCOUNT CORRELATION
# =========================
for g in games.values():
    for char, p in g["players"].items():
        if "account" not in p:
            p["account"] = char_account.get(char)

# =========================
# NEW: OUTPUT TO TWO JSON FILES
# =========================
os.makedirs(OUTPUT_DIR, exist_ok=True)
current_utc_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


# --- 1. OUTPUT: Full games.json (as you had before) ---
try:
    with open(FULL_GAMES_OUTPUT_PATH, 'w') as f:
        json.dump({"games": games, "timestamp": current_utc_timestamp}, f, indent=2)
    print(f"INFO: Full games log written to {FULL_GAMES_OUTPUT_PATH}")
except Exception as e:
    print(f"ERROR: Failed to write full games log to {FULL_GAMES_OUTPUT_PATH}: {e}", file=sys.stderr)


# --- 2. OUTPUT: Recent games.json (Filtered data for web) ---

# 1. Identify and prepare destroyed games
destroyed_games_list = []
for game_name, game_data in games.items():
    if game_data.get('state') == 'destroyed' and game_data.get('destroyed_at'):
        # Копираме данните и добавяме името на играта
        game_data_copy = game_data.copy()
        game_data_copy['name'] = game_name
        destroyed_games_list.append(game_data_copy)

# 2. Sort destroyed games by 'destroyed_at' (newest first)
try:
    def get_timestamp(game):
        ts_str = game['destroyed_at']
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

    destroyed_games_list.sort(key=get_timestamp, reverse=True)
except Exception as e:
    print(f"WARNING: Failed to sort destroyed games by timestamp: {e}", file=sys.stderr)

# 3. Take the top N recent games
recent_games_list = destroyed_games_list[:RECENT_GAMES_COUNT]

# 4. Write to file
try:
    with open(RECENT_GAMES_OUTPUT_PATH, 'w') as f:
        json.dump({'recent_games': recent_games_list, 'timestamp': current_utc_timestamp}, f, indent=2)
    print(f"INFO: Written {len(recent_games_list)} recent games to {RECENT_GAMES_OUTPUT_PATH}")
except Exception as e:
    print(f"ERROR: Failed to write recent games log to {RECENT_GAMES_OUTPUT_PATH}: {e}", file=sys.stderr)
