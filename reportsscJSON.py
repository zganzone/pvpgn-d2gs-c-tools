import os
import re
import datetime
import json # Добавяме JSON модул

# --- КОНФИГУРАЦИЯ ---
REPORTS_DIR = "/usr/local/pvpgn/var/pvpgn/reports"
# Променяме изхода на JSON файл
OUTPUT_JSON = "/var/www/html/game_history.json" 

# Лимит за обработка на файлове (за бързина)
MAX_REPORTS_TO_PROCESS = 50 # Увеличаваме лимита малко

# Мапинг на платформите
PLATFORM_MAP = {
    'W3XP': 'Warcraft III: TFT',
    'D2XP': 'Diablo II: LOD',
    'SEXP': 'Starcraft: BW',
    # Добавете други, ако е необходимо
}

# --- ФУНКЦИИ ЗА ПАРСВАНЕ ---

def parse_report_file(file_path):
    """Парсва един gr_... файл и връща структурирани данни."""
    
    game_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Грешка при четене на файл {file_path}: {e}")
        return None

    # 1. Парсване на Хедъра (INI-подобен формат)
    
    # Регулярен израз за извличане на name, id, clienttag, type, option
    header_match = re.search(
        r'name="([^"]+)" id=(#\d+)\s+clienttag=(\w+) type="([^"]+)" option="([^"]+)"',
        content
    )
    if header_match:
        game_data['name'] = header_match.group(1)
        game_data['id'] = header_match.group(2).strip('#')
        game_data['platform_tag'] = header_match.group(3) # Запазваме оригиналния таг
        game_data['platform'] = PLATFORM_MAP.get(game_data['platform_tag'], game_data['platform_tag'])
        game_data['type'] = header_match.group(4)
        
    # Регулярен израз за извличане на времената
    time_match = re.search(r'created="([^"]+)" started="([^"]+)" ended="([^"]+)"', content)
    if time_match:
        game_data['created_time'] = time_match.group(1)
        game_data['ended_time'] = time_match.group(3)
        # Изчисляване на продължителността
        duration_match = re.search(r'This game lasted (\d+) minutes \(elapsed\)\.', content)
        game_data['duration_minutes'] = int(duration_match.group(1)) if duration_match else 0
        
    # 2. Парсване на Резултатите (текст и XML-подобни секции)
    
    # Резултат (Победа/Загуба/Равен)
    result_match = re.search(r'(\w+)\s+(WIN|LOSS|DRAW|DISCONNECT)', content)
    game_data['player_name'] = result_match.group(1).strip() if result_match else "N/A"
    game_data['result'] = result_match.group(2) if result_match else "N/A"
        
    # Раса (XML-подобно)
    race_match = re.search(r'<race>([^<]+)</race>', content)
    game_data['race'] = race_match.group(1) if race_match else "N/A"

    # Основна статистика (Общ резултат, Resources)
    score_match = re.search(r'<score overall="(\d+)" units="(\d+)" structures="(\d+)" resources="(\d+)"', content)
    game_data['overall_score'] = int(score_match.group(1)) if score_match else 0
    game_data['resources_score'] = int(score_match.group(4)) if score_match else 0
        
    # Детайлна статистика (Units Killed/Lost)
    units_match = re.search(r'<units score="\d+" produced="\d+" killed="(\d+)" lost="(\d+)"', content)
    game_data['units_killed'] = int(units_match.group(1)) if units_match else 0
    game_data['units_lost'] = int(units_match.group(2)) if units_match else 0

    return game_data

def get_game_history(reports_dir):
    """Сканира директорията, парсва отчетите и връща списък."""
    
    all_reports = []
    try:
        # Взимаме всички файлове, които започват с 'gr_'
        files = [f for f in os.listdir(reports_dir) if f.startswith('gr_')]
        # Сортираме ги по име (което съдържа дата и час), за да вземем най-новите
        files.sort(reverse=True)
        
        # Обработваме само първите N файла
        files_to_process = files[:MAX_REPORTS_TO_PROCESS]
        
        for filename in files_to_process:
            file_path = os.path.join(reports_dir, filename)
            data = parse_report_file(file_path)
            if data:
                all_reports.append(data)
                
    except FileNotFoundError:
        print(f"Грешка: Директорията с отчети не е намерена: {reports_dir}")
    except Exception as e:
        print(f"Обща грешка при сканиране на директорията: {e}")
        
    return all_reports


# --- ГЛАВНА ФУНКЦИЯ (MAIN) ---

def main():
    """Основна функция за изпълнение на скрипта."""
    
    # 1. Извличане на данни от лог файловете
    game_history = get_game_history(REPORTS_DIR)
    
    # 2. Подготовка на JSON обекта
    json_output = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_reports_processed": len(game_history),
        "game_history": game_history
    }
    
    # 3. Записване на JSON файла
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            # Записваме JSON с индентация за по-добра четимост
            json.dump(json_output, f, ensure_ascii=False, indent=4) 
        print(f"Успешно генериран и записан JSON файл на: {OUTPUT_JSON}")
        print(f"Обработени отчети: {len(game_history)}")
    except Exception as e:
        print(f"Грешка при записване на JSON файла на {OUTPUT_JSON}: {e}")

if __name__ == "__main__":
    main()
