import os
import re
import datetime

# --- КОНФИГУРАЦИЯ ---
USERS_DIR = "/usr/local/pvpgn/var/pvpgn/users"
OUTPUT_HTML = "/var/www/html/test5.html" 

# Дефиниции на платформи
PLATFORM_INFO = {
    # Търсим W3XP ключове, както ги добавихте във файла.
    'W3XP': {'name': 'Warcraft III: The Frozen Throne', 'color': '#17a2b8', 'key_prefix': 'BNET\\stat\\w3xp_'}, 
    
    # 🎯 КОРЕКЦИЯ: Търсим SEXP Слот 0 (Normal/Melee), където са вашите данни
    'SEXP_NML': {'name': 'StarCraft: Brood War (Normal)', 'color': '#008080', 'key_prefix': 'Record\\SEXP\\0\\'},
    
    # Търсим D2XP Softcore Expansion (Slot 3) - Ключовете са добавени ръчно, но може да липсват данни
    'D2XP': {'name': 'Diablo II: LOD (Softcore Exp)', 'color': '#800080', 'key_prefix': 'Record\\D2XP\\3\\'},
}


# --- ФУНКЦИИ ЗА ПАРСВАНЕ ---

def parse_user_file_stats(file_path):
    all_stats = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None

    username_match = re.search(r'"BNET\\acct\\username"="(.*?)"', content)
    username = username_match.group(1) if username_match else os.path.basename(file_path)

    for tag, info in PLATFORM_INFO.items():
        prefix = info['key_prefix']
        
        stats = {
            'username': username,
            'platform': info['name'],
            'rating': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0
        }

        # Рейтинг (Рейтингът може да липсва в Normal/Slot 0)
        # Ако има ключ 'rating', го взимаме.
        rating_key = prefix + 'rating'
        rating_match = re.search(fr'"{re.escape(rating_key)}"="(\d+)"', content)
        stats['rating'] = int(rating_match.group(1)) if rating_match else 0

        # Победи
        wins_key = prefix + 'wins'
        wins_match = re.search(fr'"{re.escape(wins_key)}"="(\d+)"', content)
        stats['wins'] = int(wins_match.group(1)) if wins_match else 0
        
        # Загуби
        losses_key = prefix + 'losses'
        losses_match = re.search(fr'"{re.escape(losses_key)}"="(\d+)"', content)
        stats['losses'] = int(losses_match.group(1)) if losses_match else 0
        
        # Равенства (Ако са налични)
        draws_key = prefix + 'draws'
        draws_match = re.search(fr'"{re.escape(draws_key)}"="(\d+)"', content)
        stats['draws'] = int(draws_match.group(1)) if draws_match else 0


        # *** КЛЮЧОВА ПРОМЯНА: Включваме потребителя, ако има изиграни игри,
        # *** дори ако рейтингът му е 0 (за SEXP Slot 0)
        
        if stats['rating'] > 0 or stats['wins'] + stats['losses'] + stats['draws'] > 0:
            all_stats[tag] = stats
            
    return all_stats

# (Останалата част от функциите: get_multi_ladder, generate_ladder_table, generate_full_html и main са същите като в предишния скрипт)

def get_multi_ladder(users_dir):
    multi_ladder_data = {tag: [] for tag in PLATFORM_INFO.keys()}
    try:
        user_files = [f for f in os.listdir(users_dir) if os.path.isfile(os.path.join(users_dir, f))]
        for filename in user_files:
            file_path = os.path.join(users_dir, filename)
            data = parse_user_file_stats(file_path)
            if data:
                for tag, stats in data.items():
                    multi_ladder_data[tag].append(stats)
    except Exception as e:
        print(f"Грешка при сканиране на директорията: {e}")
        
    for tag in multi_ladder_data:
        # Сортираме по рейтинг, но ако рейтингът е 0, сортираме по W/L Ratio или WINS
        if tag == 'SEXP_NML': # За Normal игри без рейтинг, сортираме по Победи
            multi_ladder_data[tag].sort(key=lambda x: x['wins'], reverse=True)
        else: # За всички останали, сортираме по рейтинг
            multi_ladder_data[tag].sort(key=lambda x: x['rating'], reverse=True)
        
    return multi_ladder_data

def generate_ladder_table(platform_tag, ladder_data):
    info = PLATFORM_INFO[platform_tag]
    rows_html = ""
    
    # ... (HTML генерирането е същото, включително W/L/D и W/L Ratio) ...
    # (Тук само добавям заглушка, за да не повтарям целия код, но трябва да използвате пълната версия от предния пост)
    
    if ladder_data:
        for i, player in enumerate(ladder_data):
            
            total_games = player['wins'] + player['losses'] + player['draws']
            
            if player['losses'] > 0:
                wl_ratio = f"{(player['wins'] / player['losses']):.2f}"
            elif player['wins'] > 0:
                wl_ratio = "∞"
            else:
                wl_ratio = "0.00"

            wld_display = f"{player['wins']} / {player['losses']}"
            if player['draws'] > 0:
                 wld_display += f" / {player['draws']}"

            rows_html += f"""
            <tr>
                <td>{i + 1}</td>
                <td><strong>{player['username']}</strong></td>
                <td>{player['rating']}</td>
                <td>{wld_display}</td>
                <td>{total_games}</td>
                <td>{wl_ratio}</td>
            </tr>
            """
    else:
        rows_html = f'<tr><td colspan="6">Няма намерена активна статистика за {info["name"]}.</td></tr>'

    return f"""
    <h2 style="color: {info['color']}; border-bottom: 2px solid {info['color']};">{info['name']}</h2>
    <table>
        <thead>
            <tr>
                <th>Ранк</th>
                <th>Потребител</th>
                <th>Рейтинг</th>
                <th>W / L (/ D)</th>
                <th>Общо Игри</th>
                <th>W/L Съотношение</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

def generate_full_html(multi_ladder_data):
    all_tables_html = ""
    for tag in PLATFORM_INFO.keys():
        all_tables_html += generate_ladder_table(tag, multi_ladder_data[tag])
    
    html_content = f"""
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PVPGN Мултиплатформен Ладър</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 20px; }}
        .container {{ max-width: 1000px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #007bff; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: var(--table-header-bg, #007bff); color: white; }}
        .w3xp th {{ background-color: {PLATFORM_INFO['W3XP']['color']}; }}
        .sexp_nml th {{ background-color: {PLATFORM_INFO['SEXP_NML']['color']}; }}
        .d2xp th {{ background-color: {PLATFORM_INFO['D2XP']['color']}; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🏆 PVPGN Мултиплатформен Ладър</h1>
    <p>Този панел показва класирането по рейтинг (W/L) за всички активни платформи.</p>
    
    {all_tables_html}

    <p style="text-align: center; font-size: small; color: #6c757d; margin-top: 40px;">
        Последно генерирано: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </p>
</div>
</body>
</html>
    """
    return html_content

def main():
    multi_ladder_data = get_multi_ladder(USERS_DIR)
    
    if not multi_ladder_data or all(not data for data in multi_ladder_data.values()):
        print("Неуспешно извличане на Ладър данни за нито една платформа.")
        html_output = "<html><body><h1>Не бяха намерени Ладър данни за нито една платформа.</h1></body></html>"
    else:
        html_output = generate_full_html(multi_ladder_data)

    try:
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Успешно генериран и записан Мултиплатформен Ладър на: {OUTPUT_HTML}")
        total_players = sum(len(data) for data in multi_ladder_data.values())
        print(f"Общо играчи с активен рейтинг: {total_players}")
        
    except Exception as e:
        print(f"Грешка при записване на HTML файла на {OUTPUT_HTML}: {e}")

if __name__ == "__main__":
    main()
