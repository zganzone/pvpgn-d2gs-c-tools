import configparser
import os
import io
import datetime
import xml.etree.ElementTree as ET
import json # Добавяме JSON модул

# --- КОНФИГУРАЦИЯ ---
PVPGN_STATUS_FILE = "/usr/local/pvpgn/var/pvpgn/status/server.dat"
PVPGN_GAMES_LOG = "/usr/local/pvpgn/var/pvpgn/logs/games.txt"

# !!! ПРОМЕНЯМЕ ИЗХОДА НА JSON ФАЙЛ !!!
OUTPUT_JSON = "/var/www/html/pvpjsonstat/jsons/server_status.json" 

# Дефиниции на платформи
PLATFORM_MAP = {
    'W3XP': 'Warcraft III: The Frozen Throne',
    'D2XP': 'Diablo II: Lord of Destruction',
    'SEXP': 'Starcraft: Brood War',
    'SSHR': 'Starcraft Shareware',
    # Добавете други платформи, ако е необходимо
}

# --- ФУНКЦИИ ЗА ПАРСВАНЕ ---

def parse_server_data(file_path):
    """
    Парсва server.dat файла (INI формат) за активни потребители/игри.
    """
    data = {}
    config = configparser.ConfigParser()
    
    # PVPGN често използва INI без хедър, но опитваме стандартния подход:
    try:
        config.read(file_path)
    except Exception as e:
        print(f"Грешка при четене на {file_path}: {e}")
        return None

    # Извличане на общата информация (от [STATUS] секцията)
    data['status'] = dict(config['STATUS']) if 'STATUS' in config else {}

    # Извличане на игрите (от [GAMES] секцията)
    data['games'] = []
    if 'GAMES' in config:
        for key, value in config['GAMES'].items():
            try:
                platform, players, name = value.split(',', 2)
                data['games'].append({
                    'id': key, # game1, game2 и т.н.
                    'platform_tag': platform,
                    'platform_name': PLATFORM_MAP.get(platform, platform),
                    'players': int(players),
                    'name': name.strip()
                })
            except ValueError:
                pass

    # Извличане на потребителите (от [USERS] секцията)
    data['users'] = []
    if 'USERS' in config:
        for key, value in config['USERS'].items():
            try:
                platform, username, version, region, channel_id = value.split(',', 4)
                data['users'].append({
                    'platform_tag': platform,
                    'platform_name': PLATFORM_MAP.get(platform, platform),
                    'username': username,
                    'version': version,
                    'region': region,
                    'channel_id': channel_id.strip()
                })
            except ValueError:
                pass
                
    return data

def parse_games_log(file_path):
    """
    Парсва games.txt файла (XML формат) за обща сървърна статистика.
    """
    try:
        # Проверка дали файлът съществува
        if not os.path.exists(file_path):
             return {}
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        data = {}
        for child in root:
            if child.text:
                # Нормализиране на ключовете (премахване на долни черти за JSON)
                key = child.tag.replace('_', '')
                data[key] = child.text.strip()
                
        return data
    except ET.ParseError as e:
        print(f"Грешка при парсване на games.txt като XML: {e}")
        return None


# --- ГЛАВНА ФУНКЦИЯ (MAIN) ---

def main():
    """
    Основна функция за изпълнение на скрипта.
    """
    # 1. Проверка на server.dat
    if not os.path.exists(PVPGN_STATUS_FILE):
        print(f"ГРЕШКА: PVPGN status файлът не е намерен: {PVPGN_STATUS_FILE}. Не мога да генерирам JSON.")
        return

    # 2. Парсване на server.dat (активни данни)
    pvpgn_data = parse_server_data(PVPGN_STATUS_FILE)
    
    if pvpgn_data is None:
        print("Неуспешно парсване на PVPGN status данните.")
        return

    # 3. Добавяне на данни от games.txt (обща статистика)
    games_log_data = parse_games_log(PVPGN_GAMES_LOG)
    pvpgn_data['server_meta'] = games_log_data if games_log_data is not None else {}
        
    # 4. Финализиране на JSON структурата
    final_json_data = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_status": pvpgn_data.get('status', {}),
        "total_stats": pvpgn_data.get('server_meta', {}),
        "active_users": pvpgn_data.get('users', []),
        "active_games": pvpgn_data.get('games', [])
    }

    # 5. Записване на JSON файла
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            # Записваме JSON с индентация за по-добра четимост
            json.dump(final_json_data, f, ensure_ascii=False, indent=4) 
        print(f"Успешно генериран и записан JSON файл на: {OUTPUT_JSON}")
        print(f"Онлайн потребители: {len(pvpgn_data.get('users', []))}, Активни игри: {len(pvpgn_data.get('games', []))}")
    except Exception as e:
        print(f"Грешка при записване на JSON файла на {OUTPUT_JSON}: {e}")

if __name__ == "__main__":
    main()
