#!/usr/bin/env python3
import re
import json
import subprocess
from datetime import datetime

# ---- CONFIG ----
BNETD_LOG = "/usr/local/pvpgn/var/pvpgn/logs/bnetd.log"
D2CS_LOG  = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"
LINES = 500
TIME_FMT = "%b %d %H:%M:%S"
CURRENT_YEAR = datetime.now().year

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

# ---- OUTPUT ----
print(json.dumps({"games": games}, indent=2))
