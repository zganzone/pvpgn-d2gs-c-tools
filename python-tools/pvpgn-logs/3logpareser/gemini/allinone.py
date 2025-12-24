import re
import json
from datetime import datetime, timedelta
from collections import defaultdict

# --- КОНФИГУРАЦИЯ И КОНСТАНТИ ---
OUTPUT_FILE = "/var/www/html/pvpjsonstat/new/testalllogs.json"
BNETD_LOG_PATH = "/usr/local/pvpgn/var/pvpgn/logs/bnetd.log"
D2GS_LOG_PATH = "/var/snap/docker/common/var-lib-docker/overlay2/e1efc394f148bc384bd68e45a1be13c240d75d8f3b64445962438720d6d0346e/diff/root/.wine/drive_c/d2gs/d2gs.log" 
D2CS_LOG_PATH = "/usr/local/pvpgn/var/pvpgn/logs/d2cs.log"


YEAR = 2025 
DATE_FORMAT_BNETD = "%b %d %H:%M:%S"
DATE_FORMAT_D2GS = "%m/%d %H:%M:%S.%f"
GHOST_TIMEOUT = timedelta(hours=6)

# Платформа/Тип Клиент
CLIENT_MAPPING = {
    "D2XP_114D": "Diablo II: LoD (D2XP)",
    "D2DV_114D": "Diablo II: Classic (D2DV)",
    # Добавете други версии/игри, ако са налични в лога
}

# Пълни имена на класовете (Изискване)
CLASS_MAPPING = {
    "Ass": "Assassin",
    "Bar": "Barbarian",
    "Dru": "Druid",
    "Nec": "Necromancer",
    "Pal": "Paladin",
    "Sor": "Sorceress",
    "Ama": "Amazon",
    "MFamazon": "Amazon (MF)"
}

# --- СТРУКТУРИ ЗА ДАННИ ---
parsed_data = {
    "summary_stats": {},
    "games": {},
    "characters": {},
    "game_events": []
}

game_name_counts = defaultdict(int)
active_games = {} # Key: game_name, Value: unique_game_id

# --- ПОМОЩНИ ФУНКЦИИ ---

def parse_bnetd_timestamp(ts_str):
    try:
        dt_obj_no_year = datetime.strptime(ts_str, DATE_FORMAT_BNETD)
        return dt_obj_no_year.replace(year=YEAR)
    except ValueError:
        return None

def parse_d2gs_timestamp(ts_str):
    try:
        dt_obj_no_year = datetime.strptime(ts_str, DATE_FORMAT_D2GS)
        return dt_obj_no_year.replace(year=YEAR)
    except ValueError:
        return None

def get_unique_game_id(game_name, create=False):
    if create:
        game_name_counts[game_name] += 1
        return f"{game_name}_{game_name_counts[game_name]}"
    
    return f"{game_name}_{game_name_counts[game_name]}" if game_name in game_name_counts and game_name_counts[game_name] > 0 else None

def get_platform_from_line(line):
    """Извлича платформата от BNETD лог реда."""
    match = re.search(r'versiontag "([^"]+)"', line)
    if match:
        version_tag = match.group(1)
        return CLIENT_MAPPING.get(version_tag, version_tag)
    
    # Резервен вариант от game_create
    match = re.search(r'type \d+\((.*?)\)', line)
    if match:
        return match.group(1).strip()
    return "Unknown/N/A"

# --- ПАРСЕРИ ---

def parse_bnetd_log(file_path):
    RE_CREATE = re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*game_create: game \"(.*?)\" \(pass \"(.*?)\"\).*type (\d+).*created")
    RE_DESTROY = re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*game_destroy: game deleted")
    
    current_game_name = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                match_date = re.match(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", line)
                if not match_date: continue
                timestamp = parse_bnetd_timestamp(match_date.group(1))
                if not timestamp: continue

                match = RE_CREATE.search(line)
                if match:
                    game_name = match.group(2)
                    game_id = get_unique_game_id(game_name, create=True)
                    current_game_name = game_name
                    
                    parsed_data["games"][game_id] = {
                        "game_id": game_id,
                        "name": game_name,
                        "length_chars": len(game_name),
                        "platform_type": get_platform_from_line(line), # НОВО: Платформа/Тип
                        "game_type": int(match.group(4)),
                        "start_ts": timestamp.timestamp(),
                        "end_ts": None,
                        "duration_secs": None,
                        "is_active": True, # НОВО: Активна по дефиниция
                        "source_logs": ["bnetd"]
                    }
                    active_games[game_name] = game_id

                match = RE_DESTROY.search(line)
                if match and current_game_name in active_games:
                    game_id = active_games[current_game_name]
                    game = parsed_data["games"][game_id]
                    
                    if game["end_ts"] is None:
                        game["end_ts"] = timestamp.timestamp()
                        duration = game["end_ts"] - game["start_ts"]
                        game["duration_secs"] = round(duration, 2)
                        game["is_active"] = False
                        
                    del active_games[current_game_name]
                    current_game_name = None
                    
    except FileNotFoundError:
        print(f"Грешка: BNETD лог файлът не беше намерен на {file_path}")
    except Exception as e:
        print(f"Грешка при парсване на BNETD лога: {e}")


def parse_d2cs_log(file_path):
    # D2CS логиката за CREAT/DESTROY не се променя, но добавя source_logs и is_active=False
    RE_CREATE = re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*d2cs_game_create: game (\S+).*created")
    RE_DESTROY = re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*game_destroy: game (\S+) removed from game list")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                match_date = re.match(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", line)
                if not match_date: continue
                timestamp = parse_bnetd_timestamp(match_date.group(1))
                if not timestamp: continue
                
                # 1. СЪЗДАВАНЕ НА ИГРА (D2CS)
                match = RE_CREATE.search(line)
                if match:
                    game_name = match.group(2)
                    game_id = get_unique_game_id(game_name, create=True)
                    
                    if game_id not in parsed_data["games"]:
                        parsed_data["games"][game_id] = {
                            "game_id": game_id,
                            "name": game_name,
                            "length_chars": len(game_name),
                            "platform_type": "Unknown/D2CS",
                            "game_type": None,
                            "start_ts": timestamp.timestamp(),
                            "end_ts": None,
                            "duration_secs": None,
                            "is_active": True,
                            "source_logs": ["d2cs"]
                        }
                    elif "d2cs" not in parsed_data["games"][game_id]["source_logs"]:
                        parsed_data["games"][game_id]["source_logs"].append("d2cs")


                # 2. УНИЩОЖАВАНЕ НА ИГРА (D2CS)
                match = RE_DESTROY.search(line)
                if match:
                    game_name = match.group(2)
                    game_id = get_unique_game_id(game_name, create=False)
                    
                    if game_id in parsed_data["games"]:
                        game = parsed_data["games"][game_id]
                        if "d2cs" not in game["source_logs"]:
                            game["source_logs"].append("d2cs")

                        if game["end_ts"] is None:
                            game["end_ts"] = timestamp.timestamp()
                            duration = game["end_ts"] - game["start_ts"]
                            game["duration_secs"] = round(duration, 2)
                            game["is_active"] = False
                    
    except FileNotFoundError:
        print(f"Грешка: D2CS лог файлът не беше намерен на {file_path}")
    except Exception as e:
        print(f"Грешка при парсване на D2CS лога: {e}")


def parse_d2gs_log(file_path):
    """
    Парсира D2GS лога за данни за героите и събитията.
    КОРЕКЦИЯ: Имплементира пълните имена на класовете.
    """
    
    RE_CHAR_EVENT = re.compile(
        r"(?P<ts>\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}).*?"
        r"D2GSCB(?P<event>EnterGame|LeaveGame|SaveDatabaseCharacter|UpdateCharacterLadder|CloseGame):\s*"
        r"(?P<charname>\w+)\s*"
        r"(?:\(\*(?P<account>\w+)\))?"
        r".*?"
        r"(?:\[L=(?P<level>\d+),C=(?P<class>\w+)\])?"
        r".*?"
        r"game\s*'(?P<gamename>\S+)',\s*id=(?P<gameid>\d+)"
    )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                match = RE_CHAR_EVENT.search(line)
                if match:
                    groups = match.groupdict()
                    timestamp = parse_d2gs_timestamp(groups['ts'])
                    if not timestamp: continue
                        
                    event_type_raw = groups['event']
                    char_name = groups['charname']
                    char_class_abbr = groups['class']
                    
                    # Пълно име на класа
                    full_class_name = CLASS_MAPPING.get(char_class_abbr, char_class_abbr)

                    # 1. Актуализиране на данните за героя
                    if char_name:
                        char_data = parsed_data["characters"].setdefault(char_name, {
                            "char_name": char_name,
                            "account": groups.get('account', "zliazub"),
                            "class": full_class_name, # НОВО: Пълно име
                            "level": int(groups['level']) if groups['level'] else None,
                            "total_saves": 0,
                            "total_ladder_updates": 0,
                            "first_seen_ts": timestamp.timestamp(),
                            "last_seen_ts": 0,
                            "games_played_count": 0
                        })

                        char_data["last_seen_ts"] = timestamp.timestamp()
                        
                        # Актуализиране на ниво и клас, ако са налични
                        if groups['level']: char_data["level"] = int(groups['level'])
                        if full_class_name: char_data["class"] = full_class_name
                        
                        # Увеличаване на броячи
                        if event_type_raw == "SaveDatabaseCharacter":
                            char_data["total_saves"] += 1
                        elif event_type_raw == "UpdateCharacterLadder":
                            char_data["total_ladder_updates"] += 1
                        elif event_type_raw == "EnterGame":
                            char_data["games_played_count"] += 1

                    # 2. Добавяне на събитие към масива game_events
                    unique_game_id = get_unique_game_id(groups['gamename'], create=False)
                    
                    if char_name:
                        parsed_data["game_events"].append({
                            "ts": timestamp.timestamp(), 
                            "char_name": char_name,
                            "event_type": event_type_raw,
                            "game_name": groups['gamename'],
                            "unique_game_id": unique_game_id,
                            "game_server_id": int(groups['gameid'])
                        })
                    
    except FileNotFoundError:
        print(f"Грешка: D2GS лог файлът не беше намерен на {file_path}")
    except Exception as e:
        print(f"Грешка при парсване на D2GS лога: {e}")


def calculate_summary_stats():
    """Изчислява финалните статистики и добавя Топ 20 списъци."""
    
    games = list(parsed_data["games"].values())
    characters = list(parsed_data["characters"].values())
    
    # Сортиране за Топ 20
    top_20_longest_games = sorted(
        [g for g in games if g['duration_secs'] is not None], 
        key=lambda x: x['duration_secs'], reverse=True
    )[:20]
    
    top_20_most_active_chars = sorted(
        characters, 
        key=lambda x: x['games_played_count'], reverse=True
    )[:20]

    top_20_most_saves_chars = sorted(
        characters, 
        key=lambda x: x['total_saves'], reverse=True
    )[:20]

    top_20_longest_names = sorted(
        games,
        key=lambda x: x['length_chars'], reverse=True
    )[:20]
    
    # ... Изчисляване на общите статистики (както преди) ...
    durations = [data['duration_secs'] for data in games if data['duration_secs'] is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0
    max_duration = max(durations, default=0)
    min_duration = min(durations, default=0)
    
    # Записване на обобщените данни, включително Top 20 списъците
    parsed_data["summary_stats"] = {
        "total_unique_games": len(games),
        "duration_stats_seconds": {
            "average_duration": round(avg_duration, 2),
            "maximum_duration": max_duration,
            "minimum_duration": min_duration,
        },
        "character_activity_stats": {
            "total_unique_characters": len(characters),
            "total_char_saves": sum(char['total_saves'] for char in characters),
        },
        "top_lists": { # НОВО: Топ 20 списъци
            "longest_games": [{"game_id": g['game_id'], "duration_secs": g['duration_secs'], "name": g['name']} for g in top_20_longest_games],
            "most_active_characters": [{"char_name": c['char_name'], "count": c['games_played_count'], "class": c['class']} for c in top_20_most_active_chars],
            "most_saves_characters": [{"char_name": c['char_name'], "count": c['total_saves'], "class": c['class']} for c in top_20_most_saves_chars],
            "longest_game_names": [{"name": g['name'], "length": g['length_chars']} for g in top_20_longest_names],
        }
    }


def finalize_data():
    """Приключва Ghost игри и преобразува речниците в масиви."""
    
    # Приключване на "Ghost" игри (които не са били унищожени в лога)
    for game_id, game in parsed_data["games"].items():
        if game["end_ts"] is None:
            start_dt = datetime.fromtimestamp(game["start_ts"])
            end_dt = start_dt + GHOST_TIMEOUT
            
            game["end_ts"] = end_dt.timestamp()
            game["duration_secs"] = GHOST_TIMEOUT.total_seconds()
            game["is_active"] = False
            game["source_logs"].append("ghost_closed")
            
    # Изчисляване на обобщени статистики и Топ 20
    calculate_summary_stats()
    
    # Конвертиране на речниците в масиви
    parsed_data["games"] = list(parsed_data["games"].values())
    parsed_data["characters"] = list(parsed_data["characters"].values())

# --- ОСНОВНА ФУНКЦИЯ ---

def main():
    print("--- 🚀 Стартиране на Интегрирания Парсинг Скрипт (ФИНАЛНА ВЕРСИЯ) ---")
    
    parse_bnetd_log(BNETD_LOG_PATH)
    parse_d2cs_log(D2CS_LOG_PATH)
    parse_d2gs_log(D2GS_LOG_PATH)
    
    finalize_data()
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2) 
        
        print(f"\n✅ Успешно създаден JSON файл на: {OUTPUT_FILE}")
        print(f"   * Общо Игри: {len(parsed_data['games'])}")
        print(f"   * Общо Герои: {len(parsed_data['characters'])}")

    except Exception as e:
        print(f"\n❌ Грешка при записване на JSON файла: {e}")

if __name__ == "__main__":
    main()
