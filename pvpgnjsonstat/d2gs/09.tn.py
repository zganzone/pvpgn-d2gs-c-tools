import telnetlib
import re
import json
import os
import time
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
HOST = "192.168.88.41"
PORT = 8888
PASSWORD = "abcd123"

# Пътят, където Уеб сървърът чете JSON файловете (нова папка)
WEB_JSON_DIR = "/var/www/html/pvpjsonstat/new/jsons/" 

STATUS_JSON_PATH = os.path.join(WEB_JSON_DIR, "d2gs_status_data.json")
HISTORY_JSON_PATH = os.path.join(WEB_JSON_DIR, "d2gs_net_history.json") 
UPTIME_JSON_PATH = os.path.join(WEB_JSON_DIR, "d2gs_uptime_data.json") # Запазваме и този

# Интервал за четене (за custom конзолата)
UPDATE_INTERVAL_SECONDS = 10 
# Времеви прозорец за съхранение на историческите данни (10 минути)
MAX_AGE_SECONDS = 10 * 60

# --- Помощни Функции (както в 08., но пренесени) ---

def get_int_value(pattern, text, default=0):
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return default
    return default

def get_float_value(pattern, text, default=0.0):
    match = re.search(pattern, text)
    if match:
        try:
            value = match.group(1).replace('%', '').strip()
            return float(value)
        except ValueError:
            return default
    return default

def parse_memory_usage(pattern, text):
    line_match = re.search(pattern, text)
    if line_match:
        line = line_match.group(1)
        match = re.search(r"(\d+\.\d+)MB/\s*(\d+\.\d+)MB", line)
        if match:
            return {
                "used_mb": float(match.group(1)),
                "total_mb": float(match.group(2))
            }
    return {"used_mb": 0.0, "total_mb": 0.0}

def parse_net_statistics(text):
    """Парсва Game Server Net Statistic блока."""
    stats = {}
    
    # 1. Pkts и Bytes
    pkts_bytes_block = re.search(r"RecvPkts\s+RecvBytes\s+SendPkts\s+SendBytes\n(.*?)\n\s+RecvRate", text, re.DOTALL)
    if pkts_bytes_block:
        block = pkts_bytes_block.group(1).strip().split('\n')
        for line in block:
            parts = line.strip().split()
            if len(parts) == 5:
                service = parts[0].lower()
                try:
                    stats[service] = {
                        "RecvPkts": int(parts[1]),
                        "RecvBytes": int(parts[2]),
                        "SendPkts": int(parts[3]),
                        "SendBytes": int(parts[4]),
                    }
                except ValueError:
                    continue
            
    # 2. Rates
    rates_block = re.search(r"RecvRate\s+PeakRecvRate\s+SendRate\s+PeakSendRate\n(.*?)$", text, re.DOTALL)
    if rates_block:
        block = rates_block.group(1).strip().split('\n')
        for line in block:
            parts = line.strip().split()
            if len(parts) == 5:
                service = parts[0].lower()
                stats.setdefault(service, {}) # Уверете се, че service съществува
                try:
                    stats[service].update({
                        "RecvRate": float(parts[1]),
                        "PeakRecvRate": float(parts[2]),
                        "SendRate": float(parts[3]),
                        "PeakSendRate": float(parts[4]),
                    })
                except ValueError:
                    continue
    
    # Инициализация с нули за липсващи данни
    for svc in ['d2cs', 'd2dbs']:
        stats.setdefault(svc, {}).setdefault("RecvPkts", 0)
        stats[svc].setdefault("RecvBytes", 0)
        stats[svc].setdefault("SendPkts", 0)
        stats[svc].setdefault("SendBytes", 0)
        stats[svc].setdefault("RecvRate", 0.0)
        stats[svc].setdefault("PeakRecvRate", 0.0)
        stats[svc].setdefault("SendRate", 0.0)
        stats[svc].setdefault("PeakSendRate", 0.0)

    return stats


def parse_server_status_and_log_history():
    """Свързва се, парсва всички данни и записва момента и историята."""
    try:
        # 1. Telnet свързване и изпълнение на команда
        tn = telnetlib.Telnet(HOST, PORT, timeout=5)
        tn.read_until(b"Password:", timeout=1)
        tn.write(PASSWORD.encode('ascii') + b"\n")
        
        tn.read_until(b">", timeout=1) 
        tn.write(b"status\n")
        
        # Четене на целия статус изход
        status_raw = tn.read_until(b">", timeout=3).decode('ascii')
        tn.close()
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CRITICAL] Telnet error: {e}")
        return

    # --- Парсване на Uptime ---
    uptime_raw = status_raw.split("Server Status:")[0] # Взимаме само горната част
    uptime_data = {
        "uptime_total_seconds": get_int_value(r"Uptime:\s*(\d+)s", uptime_raw),
        "uptime_display": re.search(r"Uptime:\s*(\d+s)", uptime_raw) # Може да бъде по-сложен дисплей
    }
    
    # --- Парсване на Status ---
    status_data = {}
    
    # 1. Game Limits
    status_data["game_limits"] = {
        "max_games_set": get_int_value(r"Max Games:\s*(\d+)\s*\(set:\s*\d+\)", status_raw),
        "max_games_current": get_int_value(r"Max Games:\s*(\d+)\s*\(set:\s*\d+\)", status_raw), # Вероятно е едно и също число
        "max_prefer_users": get_int_value(r"Max Prefer Users:\s*(\d+)", status_raw),
        # Трябва да вземем стойността на Max Game Life, но по-безопасно е да го парснем като секунди
        "max_game_life_seconds": get_int_value(r"Max Game Life:\s*(\d+)", status_raw) * 3600, # Предполагаме, че е в часове, ако е голямо число
    }
    
    # 2. Current Activity
    status_data["current_activity"] = {
        "running_games": get_int_value(r"Running Games:\s*(\d+)", status_raw),
        "users_in_game": get_int_value(r"Users In Game:\s*(\d+)", status_raw),
    }

    # 3. Service Connections
    status_data["service_connections"] = {
        "d2cs": re.search(r"D2CS\s+:\s*([^\n]+)", status_raw).group(1).strip() if re.search(r"D2CS\s+:\s*([^\n]+)", status_raw) else "disconnected",
        "d2dbs": re.search(r"D2DBS\s+:\s*([^\n]+)", status_raw).group(1).strip() if re.search(r"D2DBS\s+:\s*([^\n]+)", status_raw) else "disconnected",
    }

    # 4. Resource Usage
    status_data["resource_usage"] = {
        "physical_memory": parse_memory_usage(r"Physical memory usage:\s*([^\n]+)", status_raw),
        "virtual_memory": parse_memory_usage(r"Virtual memory usage:\s*([^\n]+)", status_raw),
        "kernel_cpu_percent": get_float_value(r"Kernel CPU usage:\s*(\d+\.\d+)%", status_raw),
        "user_cpu_percent": get_float_value(r"User CPU usage:\s*(\d+\.\d+)%", status_raw),
    }

    # 5. Network Statistics (Новите данни)
    net_stats = parse_net_statistics(status_raw)
    status_data["network_statistics"] = net_stats
    
    # --- Запис на Моментно Състояние (Status JSON) ---
    try:
        os.makedirs(os.path.dirname(STATUS_JSON_PATH), exist_ok=True)
        with open(STATUS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Status JSON saved.")
        
        with open(UPTIME_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(uptime_data, f, indent=4)

    except OSError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Could not write status JSON: {e}")
        return

    # --- Логика за Исторически Данни (History JSON) ---
    
    # Изчисляване на общите текущи Rate
    d2cs = net_stats.get('d2cs', {})
    d2dbs = net_stats.get('d2dbs', {})
    
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recv_rate": d2cs.get('RecvRate', 0.0) + d2dbs.get('RecvRate', 0.0),
        "send_rate": d2cs.get('SendRate', 0.0) + d2dbs.get('SendRate', 0.0),
    }

    history_data = []
    if os.path.exists(HISTORY_JSON_PATH):
        try:
            with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                if not isinstance(history_data, list): history_data = []
        except (IOError, json.JSONDecodeError):
            history_data = []

    history_data.append(new_entry)
    
    # Филтриране: Запазване само на последните 10 минути
    cutoff_time = datetime.now() - timedelta(seconds=MAX_AGE_SECONDS)
    filtered_history = []
    for entry in history_data:
        try:
            entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
            if entry_time >= cutoff_time:
                filtered_history.append(entry)
        except ValueError:
            filtered_history.append(entry) 

    # Запис на филтрираните данни
    try:
        with open(HISTORY_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(filtered_history, f, indent=4)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Logged net history. Count: {len(filtered_history)}")
    except OSError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Could not write history JSON: {e}")


# --- Цикъл за постоянно изпълнение ---
if __name__ == "__main__":
    print(f"Starting D2GS Status and History Logger. Logging every {UPDATE_INTERVAL_SECONDS}s, keeping 10 min of data.")
    while True:
        parse_server_status_and_log_history()
        time.sleep(UPDATE_INTERVAL_SECONDS)
