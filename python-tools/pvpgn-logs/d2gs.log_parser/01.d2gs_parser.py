import os
import re
import json
from datetime import datetime
from dateutil.parser import isoparse
import sys

# ==================== КОНФИГУРАЦИЯ ====================
START_YEAR = 2025
# Коренна директория, където Docker/Snap съхранява overlay2
OVERLAY_ROOT = "/var/snap/docker/common/var-lib-docker/overlay2"

# ==================== ФУНКЦИЯ ЗА НАМИРАНЕ НА ЛОГ ФАЙЛА ====================
def find_d2gs_log(root=OVERLAY_ROOT):
    """
    Търси d2gs.log във всички поддиректории на Docker's overlay2.
    """
    print(f"--> Търсене на d2gs.log под {root}...")
    # Използваме sys.stderr, за да не замърсяваме stdout, ако ще го пренасочвате
    
    # Добавена е проверка дали директорията съществува
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Коренната директория {root} не съществува или е недостъпна.")

    for dirpath, _, filenames in os.walk(root):
        if "d2gs.log" in filenames:
            log_path = os.path.join(dirpath, "d2gs.log")
            print(f"*** Намерен d2gs.log: {log_path}", file=sys.stderr)
            return log_path
    raise FileNotFoundError("d2gs.log не е намерен в overlay2 структурите. Проверете OVERLAY_ROOT.")

# ==================== ФУНКЦИИ ЗА ПАРСВАНЕ НА СЪДЪРЖАНИЕТО ====================

def parse_d2gs_log_entry(log_line, year):
    """Парсва една линия от лога и извлича дата, време, функция и съобщение."""
    log_pattern = re.compile(
        r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})\s+"
        r"(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})\.(?P<millisecond>\d{3})\s+"
        r"(?P<function>\w+):\s*(?P<message>.*)$"
    )

    match = log_pattern.match(log_line.strip())
    if not match:
        return None

    data = match.groupdict()

    # Създаване на пълен ISO времеви печат (timestamp)
    try:
        dt_str = (
            f"{year}-{data['month']}-{data['day']} "
            f"{data['hour']}:{data['minute']}:{data['second']}.{data['millisecond']}"
        )
        data['timestamp'] = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f").isoformat()
    except ValueError:
        return None

    del data['month'], data['day'], data['hour'], data['minute'], data['second'], data['millisecond']
    return data

def parse_d2gs_game_cycle(log_content, year=START_YEAR):
    """
    Парсва целия лог и групира събитията в обобщен формат Игра -> Играчи.
    """
    log_lines = log_content.splitlines()
    game_data = {}

    for line in log_lines:
        parsed_line = parse_d2gs_log_entry(line, year)
        if not parsed_line:
            continue

        function = parsed_line['function']
        message = parsed_line['message']
        timestamp = parsed_line['timestamp']

        current_game_id = None
        # КОРИГИРАН РЕГЕКС: Обединяване на 'game list' и 'game' в една именувана група
        game_name_match = re.search(r"(?:game list|game) '(?P<game_name>[^']+)'", message)

        if game_name_match:
            game_name = game_name_match.group('game_name')
            
            # Логика за намиране на текущата активна игра по име
            unique_game_id_found = None
            for uid, data in game_data.items():
                # Търси се най-новата активна игра с това име
                if data["game_name"] == game_name and data.get("destroyed_at") is None:
                    unique_game_id_found = uid
                    break
            
            # 1. СЪЗДАВАНЕ НА ИГРА (Game Creation - Start of Cycle)
            if function in ("D2GSGameListInsert", "D2CSCreateEmptyGame"):
                # Уникално ID на играта: game_name_YYYYMMDDHHMMSS
                ctime_suffix = timestamp.replace('-', '').replace('T', '').replace(':', '').split('.')[0]
                unique_game_id = f"{game_name}_{ctime_suffix}"
                current_game_id = unique_game_id
                
                # Инициализиране на обекта за играта
                game_data[unique_game_id] = {
                    "game_id": unique_game_id,
                    "game_name": game_name,
                    "created_at": timestamp,
                    "destroyed_at": None,
                    "difficulty": None,
                    "hardcore": None,
                    "ladder": None,
                    "incomplete": True,
                    "players": {}
                }

                if function == "D2CSCreateEmptyGame":
                    # Извличане на параметрите на играта (Type, Difficulty, Mode/Hardcore, Ladder)
                    details_match = re.search(
                        r"Created game '[^']+', \d+,(?P<type>[^,]+),(?P<difficulty>[^,]+),(?P<mode>[^,]+),(?P<ladder>[^,]+), seqno=\d+", 
                        message
                    )
                    if details_match:
                        details = details_match.groupdict()
                        game_data[unique_game_id]["difficulty"] = details.get('difficulty')
                        # 'softcore' или 'hardcore' е в 'mode' полето
                        game_data[unique_game_id]["hardcore"] = (details.get('mode') == 'hardcore')
                        game_data[unique_game_id]["ladder"] = (details.get('ladder') == 'ladder')
            
            # 2. СЪБИТИЯ С ИГРАЧИ (Player Events)
            elif unique_game_id_found:
                current_game_id = unique_game_id_found

                # D2GSCBEnterGame: Влизане на играч
                if function == "D2GSCBEnterGame":
                    # Регекс за име на герой (CharName) (*Account) [L=Level,C=Class]@IP
                    match = re.search(r"(?P<char_name>\S+)\(\*(?P<account>[^)]+)\)\[L=(?P<level>\d+),C=(?P<class>[^\]]+)\]@(?P<ip>\S+) enter game", message)
                    if match:
                        details = match.groupdict()
                        char_name = details['char_name'].strip()
                        
                        # Инициализиране на записа за играча
                        game_data[current_game_id]['players'][char_name] = {
                            "account": details['account'],
                            "level": int(details['level']),
                            "class": details['class'],
                            "ip": details['ip'],
                            "enter": timestamp,
                            "leave": None,
                            "duration_sec": 0
                        }

                # D2GSCBLeaveGame: Излизане на играч
                elif function == "D2GSCBLeaveGame":
                    # Регекс за CharName(*Account) [L=Level,C=Class] leave game
                    match = re.search(r"(?P<char_name>\S+)\(\*(?P<account>[^)]+)\)\[L=\d+,C=[^\]]+\] leave game", message)
                    if match:
                        char_name = match.group('char_name').strip()
                        
                        if char_name in game_data[current_game_id]['players']:
                            player_record = game_data[current_game_id]['players'][char_name]
                            player_record['leave'] = timestamp
                            
                            # Изчисляване на продължителността
                            try:
                                enter_dt = isoparse(player_record['enter'])
                                leave_dt = isoparse(timestamp)
                                duration = (leave_dt - enter_dt).total_seconds()
                                player_record['duration_sec'] = round(duration)
                            except:
                                player_record['duration_sec'] = -1
                            
                            # Маркиране на края на играта (ако няма други играчи в лога, които влизат/излизат)
                            # Това е евристично, но обикновено последното напускане сигнализира за край
                            if "leave game" in message: 
                                game_data[current_game_id]["destroyed_at"] = timestamp
                                game_data[current_game_id]["incomplete"] = False

    # Връща всички намерени игри (за да видим и незавършените)
    return list(game_data.values())

# ==================== ГЛАВНА ФУНКЦИЯ ====================
if __name__ == "__main__":
    try:
        # Проверка за инсталирана библиотека
        if 'isoparse' not in globals():
            print("!!! ГРЕШКА: Моля, инсталирайте необходимата библиотека:", file=sys.stderr)
            print("!!! pip install python-dateutil", file=sys.stderr)
            sys.exit(1)
            
        # 1. Намиране на пътя до лога
        log_file_path = find_d2gs_log()
        
        # 2. Четене на лога
        with open(log_file_path, 'r', encoding='utf-8') as f:
            full_log_content = f.read()
            print(f"--> Прочетен лог с обем: {len(full_log_content)} байта.", file=sys.stderr)

        # 3. Парсване на съдържанието
        parsed_games = parse_d2gs_game_cycle(full_log_content)
        
        # 4. Запис на резултата във файл
        output_filename = "parsed_d2gs_games_output.json"
        
        if parsed_games:
            # Извеждане на резултата в stdout (за да може да се пренасочва)
            # Всички съобщения се извеждат в stderr
            json.dump(parsed_games, sys.stdout, indent=4, ensure_ascii=False)
            
            print(f"\n*** Парсването приключи успешно. Намерени са {len(parsed_games)} цикъла на игри.", file=sys.stderr)
            print(f"*** JSON резултатът беше изведен в stdout.", file=sys.stderr)
        else:
            print("\n!!! Парсването приключи, но не бяха намерени цикли на игри.", file=sys.stderr)

    except FileNotFoundError as e:
        print(f"\nГрешка: {e}", file=sys.stderr)
    except PermissionError:
        print(f"\nГрешка: Нямате нужните права за четене на {log_file_path}. Може да се наложи да пуснете скрипта като root (sudo).", file=sys.stderr)
    except Exception as e:
        print(f"\nВъзникна непредвидена грешка: {e}", file=sys.stderr)
