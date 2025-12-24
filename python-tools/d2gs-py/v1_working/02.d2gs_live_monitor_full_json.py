#!/usr/bin/env python3
import re
import sys
import argparse
import json
import datetime
import telnetlib
from pathlib import Path

# --- CONFIG ---
HOST = "127.0.0.1"
PORT = 8888
PASSWORD = "abcd123"

# Нов път по подразбиране за JSON експорт
DEFAULT_JSON_PATH = Path("/var/www/html/pvpjsonstat/jsons/d2gs_server_status.json")

# --- CLASS TRANSLATION ---
CLASS_MAP = {
    "Nec": "Necromancer",
    "Sor": "Sorceress",
    "Pal": "Paladin",
    "Amaz": "Amazon",
    "Barb": "Barbarian",
    "Ass": "Assassin",
    "Dru": "Druid",
}

# --- UTILITIES ---
def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- TELNET HELPER ---
def run_telnet_command(command):
    try:
        tn = telnetlib.Telnet(HOST, PORT, timeout=10)
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode("ascii") + b"\n")
        tn.read_until(b"D2GS> ")
        tn.write(command.encode("ascii") + b"\n")
        # Прочитане до следващия промпт или таймаут
        output = tn.read_until(b"D2GS> ", timeout=5).decode("utf-8")
        tn.write(b"exit\n")
        tn.close()
        # Премахва входния промпт и командата, връща само чистия изход
        # Може да има вариации в промпта, така че използваме split, за да вземем последния блок
        output_parts = output.split(f"\n{command}\n", 1)
        if len(output_parts) > 1:
            return output_parts[-1].strip()
        else:
            return output.strip()
    except Exception as e:
        print(f"Telnet connection failed for command '{command}': {e}", file=sys.stderr)
        return ""

# --- PARSERS ---

# (Останалите парсър функции: parse_status, parse_connections, parse_network_stats, parse_gl, parse_cl - са непроменени)

def parse_status(raw_status):
    status = {
        "current_running_games": None,
        "current_users": None,
        "max_prefer_users": None,
        "max_game_life_years": None,
        "physical_mem_used_mb": None,
        "physical_mem_total_mb": None,
        "virtual_mem_used_mb": None,
        "virtual_mem_total_mb": None,
        "kernel_cpu_percent": None,
        "user_cpu_percent": None
    }
    # Current games/users
    m = re.search(r"Current running game:\s*(\d+)", raw_status)
    if m: status["current_running_games"] = int(m.group(1))
    m = re.search(r"Current users in game:\s*(\d+)", raw_status)
    if m: status["current_users"] = int(m.group(1))
    m = re.search(r"Maximum prefer users:\s*(\d+)", raw_status)
    if m: status["max_prefer_users"] = int(m.group(1))
    # Game life in years
    m = re.search(r"Maximum game life:\s*(\d+)", raw_status)
    if m: status["max_game_life_years"] = int(m.group(1)) / (365*24*60*60)
    # Memory
    m = re.search(r"Physical memory usage:\s*([\d\.]+)MB/\s*([\d\.]+)MB", raw_status)
    if m:
        status["physical_mem_used_mb"] = float(m.group(1))
        status["physical_mem_total_mb"] = float(m.group(2))
    m = re.search(r"Virtual memory usage:\s*([\d\.]+)MB/\s*([\d\.]+)MB", raw_status)
    if m:
        status["virtual_mem_used_mb"] = float(m.group(1))
        status["virtual_mem_total_mb"] = float(m.group(2))
    # CPU
    m = re.search(r"Kernel CPU usage:\s*([\d\.]+)%", raw_status)
    if m: status["kernel_cpu_percent"] = float(m.group(1))
    m = re.search(r"User CPU usage:\s*([\d\.]+)%", raw_status)
    if m: status["user_cpu_percent"] = float(m.group(1))
    return status

def parse_connections(raw_status):
    connections = {}
    for line in raw_status.splitlines():
        m = re.match(r"Connetion to (\w+).*?\(([\d\.]+)\): (\w+)", line)
        if m:
            name, ip, state = m.groups()
            connections[name] = {"ip": ip, "status": state}
    return connections

def parse_network_stats(raw_status):
    network = {}
    lines = [l for l in raw_status.splitlines() if re.match(r"^(D2CS|D2DBS)\s", l.strip())]
    if len(lines) < 4: return network
    # Packets/bytes
    for l in lines[:2]:
        cols = re.split(r'\s+', l.strip())
        name = cols[0]
        network[name] = {
            "recv_pkts": int(cols[1]),
            "recv_bytes": int(cols[2]),
            "send_pkts": int(cols[3]),
            "send_bytes": int(cols[4])
        }
    # Rates
    for l in lines[2:4]:
        cols = re.split(r'\s+', l.strip())
        name = cols[0]
        if name in network:
            network[name].update({
                "recv_rate": float(cols[1]),
                "peak_recv_rate": float(cols[2]),
                "send_rate": float(cols[3]),
                "peak_send_rate": float(cols[4])
            })
    return network

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

def parse_cl(raw_cl):
    chars = []
    for line in raw_cl.splitlines():
        if not line.startswith("|") or "No." in line: continue
        # Подобрено разделяне на колони, за да се справя с по-сложни случаи на разстояния
        cols = [c.strip() for c in re.split(r'\s{2,}', line.strip())]
        
        # Проверка за минимален брой колони (No. | Account | Char Name | IP | Class | Level | Enter Time)
        if len(cols) < 7: continue 
        
        class_trans = CLASS_MAP.get(cols[4], cols[4])
        
        # Индекси: 1=Account, 2=Char Name, 3=IP, 4=Class, 5=Level, 6=Enter Time
        try:
             chars.append({
                "account": cols[1],
                "char_name": cols[2],
                "ip": cols[3],
                "class": class_trans,
                "level": int(cols[5]),
                "enter_time": cols[6]
            })
        except ValueError:
            # Пропускане на редове, където level не е число
            continue
    return chars

# --- МОДИФИЦИРАНА ФУНКЦИЯ ---
def parse_uptime(raw_uptime):
    """Извлича времето на стартиране и продължителността на работа от изхода на 'uptime'."""
    start_time = "Unknown"
    uptime_duration = "Unknown"

    # 1. Извличане на времето на стартиране: The game server started at 12-19 13:25:48
    m_start = re.search(r"The game server started at\s+(.*)", raw_uptime)
    if m_start:
        # Извлича само датата и часа
        start_time = m_start.group(1).strip()
    
    # 2. Извличане на продължителността на работа: uptime 0 days 21 hours 58 minutes 19 seconds
    m_uptime = re.search(r"uptime\s+(.*)", raw_uptime, re.IGNORECASE)
    if m_uptime:
        uptime_duration = m_uptime.group(1).strip()
        
    return {
        "start_time": start_time,
        "uptime_duration": uptime_duration
    }

# --- HELPER FUNCTION FOR JSON WRITING ---
def write_json(data, json_path):
    """Помагателна функция за записване на JSON изхода."""
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True) # Създава директорията, ако не съществува
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"JSON written to {json_path}")

# --- MAIN ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--debug", action="store_true", help="Print debug output")
    # Променено: -J сега приема опционален път, по подразбиране е /var/www/html/d2gs_status.json
    parser.add_argument("-J", "--json", nargs='?', const=str(DEFAULT_JSON_PATH), default=None, help=f"Generate JSON file. Optional path (default: {DEFAULT_JSON_PATH})")
    args = parser.parse_args()
    
    json_path = args.json
    
    # Ако няма подадени аргументи, по подразбиране експортира JSON
    if not args.debug and not args.json:
        json_path = DEFAULT_JSON_PATH

    timestamp_now = timestamp()
    
    # --- STATUS ---
    raw_status = run_telnet_command("status")
    server_status = parse_status(raw_status)
    connections = parse_connections(raw_status)
    network = parse_network_stats(raw_status)

    # --- GL/CL ---
    raw_gl = run_telnet_command("gl")
    games = parse_gl(raw_gl)
    characters = {}
    for g in games:
        raw_cl = run_telnet_command(f"cl {g['game_id']}")
        characters[g['game_id']] = parse_cl(raw_cl)

    # --- UPTIME --- 
    raw_uptime = run_telnet_command("uptime")
    uptime_data = parse_uptime(raw_uptime) # Връща dict с двата елемента

    output = {
        "timestamp": timestamp_now,
        "server_status": server_status,
        "connections": connections,
        "network": network,
        "games": games,
        "characters": characters,
        "uptime_duration": uptime_data["uptime_duration"], # Новият ключ за визуализация
        "start_time": uptime_data["start_time"]          # Новият ключ за анализ
    }

    if args.debug:
        print(json.dumps(output, indent=2))
        
    if json_path: # Проверява дали трябва да експортира JSON
        write_json(output, json_path)


if __name__ == "__main__":
    main()
