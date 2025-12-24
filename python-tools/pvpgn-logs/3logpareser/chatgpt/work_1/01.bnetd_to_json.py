#!/usr/bin/env python3
import re
import json
from datetime import datetime

BNETD_LOG = "/usr/local/pvpgn/var/pvpgn/logs/bnetd.log"

# regex-и
LOGIN_RE = re.compile(r'_client_loginreq2: \[(\d+)\] "([^"]+)" logged in')
LOGOUT_RE = re.compile(r'conn_destroy: \[(\d+)\] "([^"]+)" logged out')
JOIN_GAME_RE = re.compile(r'_client_joingame: \[(\d+)\] "([^"]+)" joined game "([^"]+)"')
CREATE_GAME_RE = re.compile(r'game_create: game "([^"]+)" .* created')

# timestamp regex
TS_RE = re.compile(r'^(\w+ \d+ \d+:\d+:\d+)')

YEAR = 2025  # може да се дефинира горе

sessions = {}

def parse_ts(ts_str):
    return datetime.strptime(f"{YEAR} {ts_str}", "%Y %b %d %H:%M:%S")

with open(BNETD_LOG, "r") as f:
    for line in f:
        ts_match = TS_RE.match(line)
        if not ts_match:
            continue
        ts = parse_ts(ts_match.group(1))

        # login
        m = LOGIN_RE.search(line)
        if m:
            session_id, account = m.groups()
            session_uid = f"bnet_{session_id}_{ts.strftime('%Y-%m-%dT%H_%M_%S')}"
            sessions[session_uid] = {
                "session_uid": session_uid,
                "account": account,
                "client": None,
                "realm": None,
                "ip": None,
                "login_time": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "logout_time": None,
                "is_ghost": False,
                "games": []
            }
            continue

        # logout
        m = LOGOUT_RE.search(line)
        if m:
            session_id, account = m.groups()
            # намери сесията
            for s in sessions.values():
                if s["account"] == account and s["logout_time"] is None:
                    s["logout_time"] = ts.strftime("%Y-%m-%d %H:%M:%S")
            continue

        # join game
        m = JOIN_GAME_RE.search(line)
        if m:
            session_id, account, game_name = m.groups()
            for s in sessions.values():
                if s["account"] == account:
                    s["games"].append({
                        "game_name": game_name,
                        "join_time": ts.strftime("%Y-%m-%d %H:%M:%S")
                    })
            continue

# изход
output = {"BNETD": {"sessions": list(sessions.values())}}

print(json.dumps(output, indent=2))
