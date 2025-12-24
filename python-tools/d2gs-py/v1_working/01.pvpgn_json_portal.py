#!/usr/bin/env python3
import subprocess
import xml.etree.ElementTree as ET
import json
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

# PvPGN XML paths (от parseradb.py)
PVPSTATUS_FILE = Path("/usr/local/pvpgn/var/pvpgn/logs/pvpgnstatus.xml")
SERVER_STATUS_FILE = Path("/usr/local/pvpgn/var/pvpgn/status/server.xml")

# Client tag mapping (от parseradb.py)
CLIENT_MAP = {
    "SEXP": "StarCraft: Brood War",
    "W3XP": "Warcraft III: Frozen Throne",
    "D2XP": "Diablo II: Lord of Destruction",
}

# Network ports to monitor (от parseradb.py)
NETWORK_PORTS = {
    6112: "bnet",
    6113: "d2cs",
    6114: "d2dbs",
    4000: "d2gs",
    6200: "warcraft3_router",
}

# Database path (от 01.pvpgnDBINSERT.py) - запазен за опцията --database
# Предполага се, че базата данни не е нужна за JSON експорта, но я запазваме като опция
BASE_DIR = Path("/home/support/scripts-tools/pvpgn-sqlite/chatgpt/backend/")
DB_PATH = BASE_DIR / "pvpgn.sqlite"

# JSON output path - НОВ ПЪТ ПО ПОДРАЗБИРАНЕ
DEFAULT_JSON_PATH = Path("/var/www/html/pvpjsonstat/jsons/pvpgn_server_status.json")


# -------------------- Функции за Събиране на Данни (от parseradb.py) --------------------

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_uptime():
    with open("/proc/uptime", "r") as f:
        seconds = int(float(f.read().split()[0]))
    return seconds


def get_load_average():
    with open("/proc/loadavg", "r") as f:
        parts = f.read().split()
    return {
        "1m": float(parts[0]),
        "5m": float(parts[1]),
        "15m": float(parts[2]),
    }


def get_cpu_cores():
    count = 0
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line.startswith("processor"):
                count += 1
    return count


def get_memory():
    meminfo = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0])

    total_mb = meminfo.get("MemTotal", 0) // 1024
    available_mb = meminfo.get("MemAvailable", 0) // 1024

    return {
        "total_mb": total_mb,
        "available_mb": available_mb,
        "used_mb": total_mb - available_mb,
    }


def get_disk_root():
    output = subprocess.check_output(
        ["df", "-h", "/"], text=True
    ).strip().splitlines()

    _, size, used, avail, use_percent, _ = output[1].split()

    return {
        "total": size,
        "available": avail,
        "used_percent": use_percent,
    }


def count_connections(port):
    try:
        output = subprocess.check_output(
            ["ss", "-tn", "state", "all", f"sport = :{port}"],
            text=True
        )
        return max(0, len(output.strip().splitlines()) - 1)
    except subprocess.CalledProcessError:
        return 0


def get_network_connections():
    data = {}
    for port, service in NETWORK_PORTS.items():
        data[str(port)] = {
            "service": service,
            "connections": count_connections(port)
        }
    return data


def parse_pvpgn_summary():
    # За да не гърми, ако файлът липсва (което е възможно в не-PvPGN среда)
    if not PVPSTATUS_FILE.exists():
        return {"uptime": 0, "users_online": 0, "games_online": 0}
        
    tree = ET.parse(PVPSTATUS_FILE)
    root = tree.getroot()

    return {
        "uptime": int(root.findtext("uptime", 0)),
        "users_online": int(root.findtext("users", 0)),
        "games_online": int(root.findtext("games", 0)),
    }


def parse_pvpgn_details():
    # За да не гърми, ако файлът липсва
    if not SERVER_STATUS_FILE.exists():
        return [], []

    tree = ET.parse(SERVER_STATUS_FILE)
    root = tree.getroot()

    users = []
    games = []

    users_node = root.find("Users")
    if users_node is not None:
        for u in users_node.findall("user"):
            users.append({
                "name": u.findtext("name"),
                "client_tag": u.findtext("clienttag"),
                "client_name": CLIENT_MAP.get(u.findtext("clienttag"), "Unknown"),
                "version": u.findtext("version"),
                "country": u.findtext("country"),
                "game_id": int(u.findtext("gameid", 0)),
            })

    games_node = root.find("Games")
    if games_node is not None:
        for g in games_node.findall("game"):
            games.append({
                "id": int(g.findtext("id", 0)),
                "name": g.findtext("name"),
                "client_tag": g.findtext("clienttag"),
                "client_name": CLIENT_MAP.get(g.findtext("clienttag"), "Unknown"),
            })

    return users, games


def collect_all():
    users, games = parse_pvpgn_details()

    return {
        "timestamp": get_timestamp(),

        "server": {
            "uptime_seconds": get_uptime(),
            "load_average": get_load_average(),
            "cpu_cores": get_cpu_cores(),
            "memory": get_memory(),
            "disk": get_disk_root(),
        },

        "network": {
            "connections": get_network_connections()
        },

        "pvpgn": parse_pvpgn_summary(),

        "users": users,
        "games": games,
    }


# -------------------- Функции за Изход (от 01.pvpgnDBINSERT.py) --------------------

def print_console(data):
    print(f"\nTimestamp: {data['timestamp']}\n")

    server = data["server"]
    print("=== Server Metrics ===")
    print(f"Uptime seconds: {server['uptime_seconds']}")
    print(f"Load average: {server['load_average']}")
    print(f"CPU cores: {server['cpu_cores']}")
    mem = server["memory"]
    print(f"Memory: {mem['used_mb']}/{mem['total_mb']} MB used")
    disk = server["disk"]
    print(f"Disk /: {disk['used_percent']} used ({disk['available']}/{disk['total']})\n")

    print("=== PvPGN ===")
    pvpgn = data["pvpgn"]
    print(f"Users online: {pvpgn['users_online']}")
    print(f"Games online: {pvpgn['games_online']}\n")

    print("=== Network Connections ===")
    for port, info in data["network"]["connections"].items():
        print(f"{port} ({info['service']}): {info['connections']} connections")
    print()

    print("=== Users ===")
    for u in data["users"]:
        print(f"{u['name']} | {u['client_name']} | GameID: {u['game_id']} | {u['version']} | {u['country']}")
    print()

    print("=== Games ===")
    for g in data["games"]:
        print(f"{g['id']} | {g['name']} | {g['client_name']} ({g['client_tag']})")
    print()


def write_json(data, json_path):
    # Създава директорията, ако не съществува
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"JSON written to {json_path}")


# Функциите за SQLite вмъкване (само за опцията --database)
def insert_snapshot(conn, data):
    # ... (съдържанието на оригиналната функция) ...
    pass # Изпусната за краткост, тъй като не е основна цел

def insert_users(conn, users, timestamp):
    # ... (съдържанието на оригиналната функция) ...
    pass # Изпусната за краткост, тъй като не е основна цел

def insert_games(conn, games, timestamp):
    # ... (съдържанието на оригиналната функция) ...
    pass # Изпусната за краткост, тъй като не е основна цел


# -------------------- MAIN --------------------

def main():
    parser_arg = argparse.ArgumentParser(description="PvPGN monitoring script")
    parser_arg.add_argument("-D", "--debug", action="store_true", help="Print debug output to console")
    parser_arg.add_argument("-J", "--json", nargs='?', const=str(DEFAULT_JSON_PATH), default=None, help=f"Write JSON output. Optional path (default: {DEFAULT_JSON_PATH})")
    parser_arg.add_argument("-DB", "--database", action="store_true", help="Insert data into SQLite database")
    args = parser_arg.parse_args()

    # Collect all data
    data = collect_all()

    if args.debug:
        print_console(data)

    if args.json:
        # Експортиране на JSON
        json_path = Path(args.json)
        write_json(data, json_path)

    if args.database:
        # Вмъкване в базата данни (трябва да се добави пълният код на insert_* функциите)
        conn = sqlite3.connect(DB_PATH)
        try:
            # Тук трябва да се извикат insert_snapshot, insert_users, insert_games
            print("Database insertion functionality requires the full content of insert_* functions.")
        finally:
            conn.close()
            
    # Ако няма подадени аргументи, по подразбиране експортира JSON
    if not args.debug and not args.json and not args.database:
        write_json(data, DEFAULT_JSON_PATH)


if __name__ == "__main__":
    main()
