import configparser
import os
import io
import datetime

# --- КОНФИГУРАЦИЯ ---
# Пътят до PVPGN server.dat файла
PVPGN_STATUS_FILE = "/usr/local/pvpgn/var/pvpgn/status/server.dat"

# Пътят, където ще бъде записан генерираният HTML файл
# !!! ПРОМЕНЕТЕ ТОЗИ ПЪТ, АКО Е НУЖНО !!!
OUTPUT_HTML = "/var/www/html/test1.html"

# Дефиниции на платформите (за по-добро извеждане)
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
    Парсва server.dat файла, като използва configparser.
    """
    data = {}
    
    # configparser очаква секциите да са обвити в [], 
    # което съвпада с формата на PVPGN server.dat.
    
    config = configparser.ConfigParser()
    try:
        # Прочитане на файла
        config.read(file_path)
    except Exception as e:
        print(f"Грешка при четене на {file_path}: {e}")
        return None

    # Извличане на общата информация (от [STATUS] секцията)
    if 'STATUS' in config:
        data['status'] = dict(config['STATUS'])

    # Извличане на игрите (от [GAMES] секцията)
    data['games'] = []
    if 'GAMES' in config:
        for key, value in config['GAMES'].items():
            try:
                # Пример: game1=W3XP,11,lklklk
                platform, players, name = value.split(',', 2)
                data['games'].append({
                    'platform': PLATFORM_MAP.get(platform, platform),
                    'players': int(players),
                    'name': name.strip()
                })
            except ValueError:
                # Игнорираме редове с грешен формат
                pass

    # Извличане на потребителите (от [USERS] секцията)
    data['users'] = []
    if 'USERS' in config:
        for key, value in config['USERS'].items():
            try:
                # Пример: user1=W3XP,zgan4,1.26.0.1,USA,11
                platform, username, version, region, channel_id = value.split(',', 4)
                data['users'].append({
                    'platform': PLATFORM_MAP.get(platform, platform),
                    'username': username,
                    'version': version,
                    'region': region,
                    'status_id': channel_id.strip() # ID на играта/канала
                })
            except ValueError:
                # Игнорираме редове с грешен формат
                pass
                
    return data

# --- ФУНКЦИИ ЗА ГЕНЕРИРАНЕ НА HTML ---

def generate_html(data):
    """
    Генерира HTML съдържание от парсваните данни.
    (Коригирана версия за избягване на SyntaxError с f-string)
    """
    if not data:
        return "<html><body><h1>Грешка при зареждане на PVPGN данни.</h1></body></html>"
        
    status = data.get('status', {})
    games = data.get('games', [])
    users = data.get('users', [])
    
    # 1. Генериране на съдържанието на таблицата с игри
    games_html = ""
    if games:
        for game in games:
            games_html += f"""
            <tr>
                <td>{game['platform']}</td>
                <td>{game['name']}</td>
                <td>{game['players']}</td>
            </tr>
            """
    else:
        games_html = '<tr><td colspan="3">Няма активни игри в момента.</td></tr>'

    # 2. Генериране на съдържанието на таблицата с потребители
    users_html = ""
    if users:
        for user in users:
            users_html += f"""
            <tr>
                <td>{user['username']}</td>
                <td>{user['platform']}</td>
                <td>{user['region']}</td>
                <td>{user['version']}</td>
            </tr>
            """
    else:
        users_html = '<tr><td colspan="4">Няма логнати потребители в момента.</td></tr>'
    
    # Форматиране на основния HTML (използваме променливите games_html и users_html)
    html_content = f"""
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PVPGN Сървър Статистика</title>
    <meta http-equiv="refresh" content="30"> <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; }}
        .container {{ max-width: 900px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #007bff; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        .status-box {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🎮 PVPGN Сървър Статистика</h1>
    <div class="status-box">
        <strong>Обща Информация:</strong><br>
        Версия: {status.get('version', 'N/A')}<br>
        Uptime: {status.get('uptime', 'N/A')}<br>
        Онлайн Потребители: <strong>{status.get('users', '0')}</strong> | Активни Игри: <strong>{status.get('games', '0')}</strong> | Общо Акаунти: {status.get('useraccounts', 'N/A')}
    </div>

    <h2>Активни Игри ({len(games)})</h2>
    <table>
        <thead>
            <tr>
                <th>Платформа</th>
                <th>Име на Играта</th>
                <th>Играчи</th>
            </tr>
        </thead>
        <tbody>
            {games_html}
        </tbody>
    </table>

    <h2>Логнати Потребители ({len(users)})</h2>
    <table>
        <thead>
            <tr>
                <th>Потребителско Име</th>
                <th>Платформа</th>
                <th>Регион</th>
                <th>Версия</th>
            </tr>
        </thead>
        <tbody>
            {users_html}
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
    """
    Основна функция за изпълнение на скрипта.
    """
    if not os.path.exists(PVPGN_STATUS_FILE):
        print(f"ГРЕШКА: PVPGN файлът не е намерен на път: {PVPGN_STATUS_FILE}")
        # Опитваме да създадем празен HTML с грешка
        try:
            with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
                f.write(f"<html><body><h1>Грешка: Файлът {PVPGN_STATUS_FILE} не е намерен.</h1></body></html>")
            print(f"Създаден е HTML файл с грешка на {OUTPUT_HTML}")
        except Exception as e:
            print(f"Неуспешно записване на HTML файл: {e}")
        return

    # 1. Парсване на данните
    pvpgn_data = parse_server_data(PVPGN_STATUS_FILE)
    
    if pvpgn_data is None:
        print("Неуспешно парсване на PVPGN данните.")
        return

    # 2. Генериране на HTML
    html_output = generate_html(pvpgn_data)

    # 3. Записване на HTML файла
    try:
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Успешно генериран и записан HTML файл на: {OUTPUT_HTML}")
        print(f"Онлайн потребители: {len(pvpgn_data.get('users', []))}, Активни игри: {len(pvpgn_data.get('games', []))}")
    except Exception as e:
        print(f"Грешка при записване на HTML файла на {OUTPUT_HTML}: {e}")

if __name__ == "__main__":
    main()
