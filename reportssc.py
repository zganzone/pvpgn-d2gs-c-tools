import os
import re
import datetime

# --- КОНФИГУРАЦИЯ ---
REPORTS_DIR = "/usr/local/pvpgn/var/pvpgn/reports"
OUTPUT_HTML = "/var/www/html/test5.html"

# Лимит за обработка на файлове (за бързина)
MAX_REPORTS_TO_PROCESS = 20

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
        game_data['id'] = header_match.group(2)
        game_data['platform'] = PLATFORM_MAP.get(header_match.group(3), header_match.group(3))
        game_data['type'] = header_match.group(4)
        
    # Регулярен израз за извличане на времената
    time_match = re.search(r'created="([^"]+)" started="([^"]+)" ended="([^"]+)"', content)
    if time_match:
        game_data['created'] = time_match.group(1)
        game_data['ended'] = time_match.group(3)
        # Изчисляване на продължителността
        duration_match = re.search(r'This game lasted (\d+) minutes \(elapsed\)\.', content)
        game_data['duration'] = f"{duration_match.group(1)} минути" if duration_match else "N/A"

    # 2. Парсване на Резултатите (текст и XML-подобни секции)
    
    # Резултат (Победа/Загуба/Равен)
    result_match = re.search(r'(\w+)\s+(WIN|LOSS|DRAW)', content)
    if result_match:
        game_data['player_name'] = result_match.group(1).strip()
        game_data['result'] = result_match.group(2)
    else:
        game_data['player_name'] = "N/A"
        game_data['result'] = "N/A"
        
    # Раса (XML-подобно)
    race_match = re.search(r'<race>([^<]+)</race>', content)
    game_data['race'] = race_match.group(1) if race_match else "N/A"

    # Основна статистика (Общ резултат, Resources)
    score_match = re.search(r'<score overall="(\d+)" units="(\d+)" structures="(\d+)" resources="(\d+)"', content)
    game_data['overall_score'] = score_match.group(1) if score_match else "N/A"
    game_data['resources_score'] = score_match.group(4) if score_match else "N/A"
    
    # Детайлна статистика (Units Killed/Lost)
    units_match = re.search(r'<units score="\d+" produced="\d+" killed="(\d+)" lost="(\d+)"', content)
    game_data['units_killed'] = units_match.group(1) if units_match else "N/A"
    game_data['units_lost'] = units_match.group(2) if units_match else "N/A"

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


# --- ФУНКЦИИ ЗА ГЕНЕРИРАНЕ НА HTML ---

def generate_history_html(history_data):
    """Генерира HTML съдържание от историята на игрите."""
    
    rows_html = ""
    if history_data:
        for game in history_data:
            # Цвят на резултата
            color = 'green' if game['result'] == 'WIN' else ('red' if game['result'] == 'LOSS' else 'gray')
            
            rows_html += f"""
            <tr>
                <td>{game.get('platform', 'N/A')}</td>
                <td>{game.get('name', 'N/A')} ({game.get('id', '')})</td>
                <td style="color: {color}; font-weight: bold;">{game.get('result', 'N/A')}</td>
                <td>{game.get('player_name', 'N/A')} / {game.get('race', 'N/A')}</td>
                <td>{game.get('units_killed', 'N/A')} / {game.get('units_lost', 'N/A')}</td>
                <td>{game.get('duration', 'N/A')}</td>
                <td>{game.get('ended', 'N/A')}</td>
            </tr>
            """
    else:
        rows_html = '<tr><td colspan="7">Няма намерени отчети за игри.</td></tr>'

    
    html_content = f"""
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PVPGN История на Игрите</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; }}
        .container {{ max-width: 1200px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #dc3545; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #dc3545; color: white; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📜 История на Последните {MAX_REPORTS_TO_PROCESS} Игри</h1>
    <p>Този списък е генериран от подробните отчети за приключили игри ({REPORTS_DIR}).</p>
    <table>
        <thead>
            <tr>
                <th>Платформа</th>
                <th>Име на Играта (ID)</th>
                <th>Резултат</th>
                <th>Играч / Раса</th>
                <th>Убити / Загубени Единици</th>
                <th>Продължителност</th>
                <th>Приключена на</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    
    <p style="text-align: center; font-size: small; color: #6c757d;">
        Последно генерирано: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </p>
</div>
</body>
</html>
    """
    return html_content

# --- ГЛАВНА ФУНКЦИЯ (MAIN) ---

def main():
    """Основна функция за изпълнение на скрипта."""
    
    # 1. Извличане на данни от лог файловете
    game_history = get_game_history(REPORTS_DIR)
    
    if not game_history:
        print("Неуспешно извличане на историята на игрите.")
        # Генерираме HTML с грешка
        html_output = "<html><body><h1>Не бяха намерени или парснати отчети за игри.</h1></body></html>"
    else:
        # 2. Генериране на HTML
        html_output = generate_history_html(game_history)

    # 3. Записване на HTML файла
    try:
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Успешно генериран и записан HTML файл на: {OUTPUT_HTML}")
        print(f"Обработени отчети: {len(game_history)}")
    except Exception as e:
        print(f"Грешка при записване на HTML файла на {OUTPUT_HTML}: {e}")

if __name__ == "__main__":
    main()
