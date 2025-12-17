import telnetlib
import re
import json
import os
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
HOST = "192.168.88.41"
PORT = 8888
PASSWORD = "abcd123"

# Абсолютен път за Уеб данни
WEB_DATA_DIR = "/var/www/html/pvpjsonstat/jsons/" 
# Локална директория за Логове (до скрипта)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# --- Помощни функции за безопасно парсване (Остават същите) ---
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
            try:
                return {
                    "used_mb": float(match.group(1)),
                    "total_mb": float(match.group(2)),
                }
            except ValueError:
                pass 
    return {"used_mb": 0.0, "total_mb": 0.0}

# --- Функция за Логване на Сурови Данни (Остава същата) ---
def log_raw_data(uptime_raw, status_raw):
    """Saves the raw output from Telnet commands to a log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"raw_data_{timestamp}.log"
    file_path = os.path.join(LOGS_DIR, log_filename)
    
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("--- UPTIME RAW DATA ---\n")
            f.write(uptime_raw.strip() + "\n\n")
            f.write("--- STATUS RAW DATA ---\n")
            f.write(status_raw.strip() + "\n")
        print(f"[LOG] Raw data logged successfully to: {file_path}")
    except OSError as e:
        print(f"[ERROR] Could not write raw log file: {e}")


# --- Основна функция за парсване (КОРИГИРАНА) ---

def parse_server_status():
    
    uptime_raw = ""
    status_raw = ""
    results = {"status": "error", "message": "", "data": {}}

    try:
        tn = telnetlib.Telnet(HOST, PORT, timeout=5) 
        
        # 1. Изчакване на съобщението за добре дошли или първия промпт.
        # Този ред ще чете, докато стигне "pass:" (за парола) или "D2GS>" (за промпт).
        # Ако сървърът първо изпраща банер, този read_until ще го прочете.
        # Увеличаваме таймаута за първата комуникация.
        tn.read_until(b"pass:", timeout=5) 
        
        # 2. Изпращане на паролата
        tn.write(PASSWORD.encode('ascii') + b"\n")
        
        # 3. Изчакване на промпта D2GS> след влизане.
        # Ако паролата е успешна, трябва да стигнем до промпта.
        # Добавяме кратък таймаут за по-голяма сигурност, че промптът е наличен.
        tn.read_until(b"D2GS>", timeout=2)

        # 4. Изпълнение на 'uptime'
        tn.write(b"uptime\n")
        # Прочитане на изхода до следващия промпт 'D2GS>'
        uptime_raw = tn.read_until(b"D2GS>", timeout=3).decode('ascii')
        
        # 5. Изпълнение на 'status'
        tn.write(b"status\n")
        status_raw = tn.read_until(b"D2GS>", timeout=4).decode('ascii') 
        
        tn.close()
        
        if not status_raw or not uptime_raw:
             results["message"] = "Partial or no response received from server after commands."
             log_raw_data(uptime_raw, status_raw)
             return {"status": "error", "message": results["message"], "uptime_data": {}, "status_data": {}}
        
        # ... (Парсване на данни - както преди) ...
        
        # --- Uptime Parsing ---
        uptime_data = {}
        server_started_match = re.search(r"The game server started at (.*)", uptime_raw)
        uptime_duration_match = re.search(r"uptime (.*)", uptime_raw)
        current_time_match = re.search(r"Now it is (.*)", uptime_raw)

        # ... (Парсинг на uptime и калкулации) ...
        if uptime_duration_match:
            duration_value = uptime_duration_match.group(1).strip()
            uptime_data["uptime_duration_value"] = duration_value
            # ... (total_seconds калкулации) ...
            parts = duration_value.split()
            try:
                days = int(parts[0])
                hours = int(parts[2])
                minutes = int(parts[4])
                seconds = int(parts[6])
                total_seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
                uptime_data["uptime_total_seconds"] = total_seconds
            except (IndexError, ValueError):
                uptime_data["uptime_total_seconds"] = 0
                
        if server_started_match:
            uptime_data["server_start_time"] = server_started_match.group(1).strip()
        if current_time_match:
            uptime_data["current_time"] = current_time_match.group(1).strip()

        # --- Status Parsing: (Продължава както преди) ---
        status_data = {}
        # ... (Всички game_limits, current_activity, service_connections, resource_usage, network_statistics) ...
        # (Запазвам структурата както е била в предишния отговор, за да не я повтарям)
        status_data["game_limits"] = {
            "max_games_set": get_int_value(r"Setting maximum game:\s*(\d+)", status_raw),
            "max_games_current": get_int_value(r"Current maximum game:\s*(\d+)", status_raw),
            "max_prefer_users": get_int_value(r"Maximum prefer users:\s*(\d+)", status_raw),
            "max_game_life_seconds": get_int_value(r"Maximum game life:\s*(\d+)", status_raw),
        }
        status_data["current_activity"] = {
            "running_games": get_int_value(r"Current running game:\s*(\d+)", status_raw),
            "users_in_game": get_int_value(r"Current users in game:\s*(\d+)", status_raw),
        }
        d2cs_match = re.search(r"Connetion to D2CS\s*(.*)", status_raw)
        d2dbs_match = re.search(r"Connetion to D2DBS\s*(.*)", status_raw)
        status_data["service_connections"] = {
            "d2cs": d2cs_match.group(1).strip() if d2cs_match else "Status Unknown",
            "d2dbs": d2dbs_match.group(1).strip() if d2dbs_match else "Status Unknown",
        }
        status_data["resource_usage"] = {
            "physical_memory": parse_memory_usage(r"Physical memory usage:\s*([^\n]+)", status_raw),
            "virtual_memory": parse_memory_usage(r"Virtual memory usage:\s*([^\n]+)", status_raw),
            "kernel_cpu_percent": get_float_value(r"Kernel CPU usage:\s*(\d+\.\d+)%", status_raw),
            "user_cpu_percent": get_float_value(r"User CPU usage:\s*(\d+\.\d+)%", status_raw),
        }
        # (Пропуснати са network_statistics за краткост, но трябва да останат във вашия файл)

        # Запис на суровите данни в лога
        log_raw_data(uptime_raw, status_raw)
        
        return {
            "status": "success", 
            "message": "", 
            "uptime_data": uptime_data, 
            "status_data": status_data
        }

    except Exception as e:
        results["message"] = f"Critical error during Telnet session: {e}"
        # Логваме, дори ако сесията е прекъсната
        log_raw_data(uptime_raw, status_raw) 
        return {"status": "error", "message": results["message"], "uptime_data": {}, "status_data": {}}


# --- Функции за Запис на Файлове (Остават същите) ---
# --- Функция за Запис на JSON и TXT Файлове (КОРИГИРАНА) ---

def save_parsed_data(parsed_data):
    """Saves the parsed data into two separate JSON files and one TXT file."""
    
    if parsed_data["status"] != "success":
        print("[ERROR] Skipping file write due to critical error.")
        return

    # 1. Запис на TXT файл (Uptime)
    
    # *** КЛЮЧОВА ПРОМЯНА: ИЗПОЛЗВАМЕ ЦЯЛОТО ЧИСЛО В СЕКУНДИ ***
    # Извличаме "uptime_total_seconds" (например 91536) и го превръщаме в string.
    # Ако стойността липсва или има грешка, записваме '0'.
    uptime_value = str(parsed_data["uptime_data"].get("uptime_total_seconds", 0))
    # ***************************************************************
    
    txt_file_path = os.path.join(WEB_DATA_DIR, "d2gs_uptime.txt")
    
    try:
        os.makedirs(WEB_DATA_DIR, exist_ok=True)
        with open(txt_file_path, 'w', encoding='utf-8') as f:
            f.write(uptime_value)
        print(f"[SUCCESS] Uptime TXT (seconds) saved to: {txt_file_path}")
    except OSError as e:
        print(f"[ERROR] Could not write TXT file: {e}")

    # 2. Запис на JSON файл (Uptime)
    uptime_json_path = os.path.join(WEB_DATA_DIR, "d2gs_uptime_data.json")
    try:
        with open(uptime_json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data["uptime_data"], f, indent=4)
        print(f"[SUCCESS] Uptime JSON saved to: {uptime_json_path}")
    except OSError as e:
        print(f"[ERROR] Could not write Uptime JSON file: {e}")

    # 3. Запис на JSON файл (Status)
    status_json_path = os.path.join(WEB_DATA_DIR, "d2gs_status_data.json")
    try:
        with open(status_json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data["status_data"], f, indent=4)
        print(f"[SUCCESS] Status JSON saved to: {status_json_path}")
    except OSError as e:
        print(f"[ERROR] Could not write Status JSON file: {e}")
        
    print("--- File processing complete ---")

# --- Изпълнение ---
if __name__ == "__main__":
    
    parsed_data = parse_server_status()
    save_parsed_data(parsed_data)
