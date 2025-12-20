# log_parser_focused_v2.py
import re
import os
import json
from datetime import datetime
from glob import glob

# --- Конфигурация ---
# Файлове, които скриптът ще търси
LOG_FILES = [
    'bnetd.log',
    'd2cs.log'
]
OUTPUT_FILE = 'log_events_focused.json' # Може да използвате същото име

# Извлечени ключови функции, върху които да се фокусираме
FOCUSED_KEYS = {
    'd2cs_conn_create:', 'd2cs_conn_destroy:', 'd2cs_game_create:', 'd2ladder_readladder:',
    'game_add_character:', 'game_del_character:', 'game_destroy:', 'on_bnetd_accountloginreply:',
    'on_bnetd_charloginreply:', 'on_client_charloginreq:', 'on_client_creategamereq:',
    'on_client_joingamereq:', 'on_client_loginreq:', 'on_d2cs_initconn:', 'on_d2gs_creategamereply:',
    'on_d2gs_joingamereply:', 'server_accept:',
    
    'anongame_infos_load:', 'client_tag', 'game_create:', 'game_destroy:', 'game_report:', 'got',
    
    '_client_motdw3:', 'conn_set_playerinfo:', 'conn_shutdown:', 'customicons_load:',
}

# КОРИГИРАН РЕГУЛЯРЕН ИЗРАЗ:
# Добавихме \s* (нула или повече празни места) преди затварящата скоба (\]) 
# и преди функцията на лога, за да се справим с вариациите в лог формата.
LOG_LINE_REGEX = re.compile(
    r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\[(info|debug|warn|error|trace)\s*\]\s*([^:]+):\s+(.*)$"
)

def to_iso_date(date_str):
    """
    Преобразува лог timestamp (напр. "Dec 20 09:36:44") в ISO 8601 формат.
    """
    try:
        current_year = datetime.now().year
        dt = datetime.strptime(f"{date_str} {current_year}", "%b %d %H:%M:%S %Y")
        return dt.isoformat()
    except ValueError:
        return date_str

def parse_log_file_focused(file_path):
    """
    Обработва лог файл, фокусирайки се само върху редове, съдържащи FOCUSED_KEYS.
    """
    print(f"Processing file: {os.path.basename(file_path)}")
    parsed_events = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                match = LOG_LINE_REGEX.match(line)
                
                if not match:
                    continue

                # Групите: 1:Дата, 2:Ниво, 3:Източник/Функция, 4:Съобщение
                date_str, level, source_func, message = match.groups()
                
                # Проверка дали съобщението или функцията съдържа някоя от ключовите функции
                for key in FOCUSED_KEYS:
                    # Проверяваме дали ключовата дума е в началото на съобщението 
                    # или е цялата функция (source_func)
                    if key.strip(':') in source_func or message.startswith(key):
                        
                        parsed_events.append({
                            'timestamp': to_iso_date(date_str),
                            'level': level.strip(), 
                            'source_file': os.path.basename(file_path),
                            'event_type': key.strip(':'), 
                            'details': {'full_message': message}
                        })
                        break
                        
    except FileNotFoundError:
        print(f"WARNING: Log file not found: {file_path}")
    except Exception as e:
        print(f"ERROR: Failed to read or parse file {file_path}: {e}")
        
    return parsed_events


def main():
    """
    Основна функция, която управлява сканирането и записа.
    """
    all_events = []
    
    found_files = [f for f in LOG_FILES if os.path.exists(f)]

    if not found_files:
        print(f"No specified log files found in the current directory: {', '.join(LOG_FILES)}. Exiting.")
        return
        
    for log_file in found_files:
        events = parse_log_file_focused(log_file)
        all_events.extend(events)

    all_events.sort(key=lambda x: x['timestamp'])

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, indent=2, ensure_ascii=False)
        
        print("\n--- Success ---")
        print(f"{len(all_events)} events parsed from {len(found_files)} files.")
        print(f"Output written to: {OUTPUT_FILE}")
        print("---------------")

    except Exception as e:
        print(f"ERROR: Failed to write output JSON file: {e}")

if __name__ == '__main__':
    main()
