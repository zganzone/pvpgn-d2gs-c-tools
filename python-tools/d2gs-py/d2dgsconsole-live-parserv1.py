#!/usr/bin/env python3
import telnetlib
import time
import argparse
import re
from datetime import datetime
import json

# --- CONFIGURATION ---
HOST = "127.0.0.1"
PORT = 8888
PASSWORD = "abcd123"
LOOP_INTERVAL = 60  # seconds
JSON_DIR = "/home/support/scripts-tools/pvpgn-sqlite/chatgpt/backend/data/json"

# --- Class translation ---
CLASS_MAP = {
    "Nec": "Necromancer",
    "Sor": "Sorceress",
    "Pal": "Paladin",
    "Bar": "Barbarian",
    "Dru": "Druid",
    "Ass": "Assassin",
    "Ama": "Amazon",
}

# --- UTILITY FUNCTIONS ---
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_status(tn):
    tn.write(b"status\n")
    time.sleep(1)
    return tn.read_very_eager().decode("utf-8", errors="ignore")

def parse_status(raw_status):
    server = {}
    connection_status = {}
    lines = raw_status.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("Current running game:"):
            server["current_running_games"] = int(line.split(":")[1].strip())
        elif line.startswith("Current users in game:"):
            server["current_users"] = int(line.split(":")[1].strip())
        elif line.startswith("Maximum prefer users:"):
            server["max_prefer_users"] = int(line.split(":")[1].strip())
        elif line.startswith("Maximum game life:"):
            value = line.split(":")[1].strip().split()[0]
            seconds = int(value)
            server["max_game_life_years"] = round(seconds / (60*60*24*365), 2)
        elif line.startswith("Connection to") or line.startswith("Connetion to"):
            m = re.search(r'(\w+)\s*\(([\d\.]+)\):\s*(\w+)', line)
            if m:
                service, ip, status = m.groups()
                connection_status[service] = {"ip": ip, "status": status}
    return server, connection_status

def parse_network_stats(raw_status):
    network_stats = {}
    lines = raw_status.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", "|", line)
        cols = line.split("|")
        service = cols[0]
        if len(cols) < 5:
            continue
        try:
            float(cols[1])
        except ValueError:
            continue
        if service not in network_stats:
            network_stats[service] = {
                "recv_pkts": int(cols[1]),
                "recv_bytes": int(cols[2]),
                "send_pkts": int(cols[3]),
                "send_bytes": int(cols[4])
            }
        else:
            network_stats[service].update({
                "recv_rate": float(cols[1]),
                "peak_recv_rate": float(cols[2]),
                "send_rate": float(cols[3]),
                "peak_send_rate": float(cols[4])
            })
    return network_stats

# --- GL/CL ---
def fetch_gl(tn):
    tn.write(b"gl\n")
    time.sleep(1)
    return tn.read_very_eager().decode("utf-8", errors="ignore")

def parse_gl(raw_gl):
    games = []
    for line in raw_gl.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Match pattern: | №  GameName  GamePass  ID  GameVer  Type  Difficulty  Ladder  Users  CreateTime  Dis |
        m = re.match(r'\|\s*\d+\s+(\S+)\s+(.*?)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+)', line)
        if not m:
            continue
        game_name, game_pass, game_id, game_ver, gtype, difficulty, ladder, users, create_time = m.groups()
        if not game_pass.strip():
            game_pass = "none"

        game = {
            "game_id": int(game_id),
            "game_name": game_name[:15],
            "game_pass": game_pass[:31],
            "game_ver": game_ver,
            "type": gtype,
            "difficulty": difficulty,
            "ladder": ladder,
            "users": int(users),
            "create_time": create_time
        }
        games.append(game)
    return games


def fetch_cl(tn, game_id):
    tn.write(f"cl {game_id}\n".encode("ascii"))
    time.sleep(1)
    return tn.read_very_eager().decode("utf-8", errors="ignore")

def parse_cl(raw_cl):
    characters = []
    for line in raw_cl.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        line = re.sub(r"\s+", "|", line)
        cols = [c for c in line.split("|") if c]
        if len(cols) < 6:
            continue
        char = {
            "account": cols[1],
            "char_name": cols[2],
            "ip": cols[3],
            "class": CLASS_MAP.get(cols[4], cols[4]),
            "level": int(cols[5]),
            "enter_time": cols[6]
        }
        characters.append(char)
    return characters

# --- MAIN ---
def main(debug=False, json_mode=False):
    tn = telnetlib.Telnet(HOST, PORT)
    tn.read_until(b"Password: ")
    tn.write(PASSWORD.encode("ascii")+b"\n")
    tn.read_until(b"D2GS> ")

    while True:
        timestamp = get_timestamp()
        raw_status = fetch_status(tn)
        server_status, connection_status = parse_status(raw_status)
        network_stats = parse_network_stats(raw_status)
        raw_gl = fetch_gl(tn)
        games = parse_gl(raw_gl)
        all_characters = {}
        for game in games:
            raw_cl = fetch_cl(tn, game["game_id"])
            characters = parse_cl(raw_cl)
            all_characters[game["game_id"]] = characters

        if debug:
            print(f"\n--- [{timestamp}] SERVER STATUS ---")
            print(server_status)
            print(f"--- CONNECTION STATUS ---")
            print(connection_status)
            print(f"--- NETWORK STATS ---")
            print(network_stats)
            print(f"--- GAMES ---")
            for g in games:
                print(g)
            print(f"--- CHARACTERS ---")
            for gid, chars in all_characters.items():
                print(f"Game {gid}: {chars}")

        if json_mode:
            data = {
                "timestamp": timestamp,
                "server_status": server_status,
                "connection_status": connection_status,
                "network_stats": network_stats,
                "games": games,
                "characters": all_characters
            }
            filename = f"{JSON_DIR}/{timestamp.replace(' ','_').replace(':','')}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            print(f"JSON written to {filename}")

        # TODO: uncomment the following to insert into DB
        # insert_db(server_status, connection_status, network_stats, games, all_characters)

        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="D2GS full monitor with GL/CL")
    parser.add_argument("-D", "--debug", action="store_true", help="Debug mode, print to console")
    parser.add_argument("-J", "--json", action="store_true", help="JSON output mode")
    args = parser.parse_args()
    main(debug=args.debug, json_mode=args.json)
	

