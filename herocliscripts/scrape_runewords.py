#!/usr/bin/env python3
"""
Python Web Scraper за D2 Runewords.
Извлича Runeword-ите от d2tomb.com и генерира runewords_db.json.
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from typing import List, Dict, Any

# --- КОНФИГУРАЦИЯ ---
URL = 'https://www.d2tomb.com/rune_words.shtml'
OUTPUT_JSON_FILE = 'runewords_db.json'
# --- КРАЙ НА КОНФИГУРАЦИЯТА ---


def clean_stats_html(stats_cell: BeautifulSoup) -> str:
    """
    Почиства HTML съдържанието на клетката за статистика.
    Премахва <img> тагове и заменя <br> с нашия разделител ' | '.
    """
    
    # 1. Намираме и премахваме всички <img> тагове (иконите)
    for img in stats_cell.find_all('img'):
        img.decompose()
        
    # 2. Заменяме всички <br> тагове с нашия разделител
    for br in stats_cell.find_all('br'):
        br.replace_with(' | ')
        
    # 3. Взимаме чистия текст
    clean_text = stats_cell.get_text()
    
    # 4. Финално почистване на whitespace
    clean_text = clean_text.replace('\n', '').replace('\t', ' ').strip()
    clean_text = re.sub(r'\s{2,}', ' ', clean_text) # Премахва двойни интервали
    clean_text = re.sub(r' \| \| ', ' | ', clean_text) # Почиства излишни разделители
    clean_text = clean_text.strip(' |').strip() # Премахва водещи/крайни разделители
    
    return clean_text


def parse_runeword_table(html_content: str) -> List[Dict[str, Any]]:
    """
    Парсва HTML съдържанието, за да извлече данните за Runeword-ите.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    runewords_list = []

    # Таблицата с Runeword-ите изглежда е третата <table> на страницата
    # (може да се наложи да промените индекса [2] на [3] или [4], ако сайтът се промени)
    try:
        runeword_table = soup.find_all('table')[2] 
    except IndexError:
        print("[!!!] ERROR: Не можах да намеря таблицата с Runeword-и. Проверете индекса.")
        return []

    # Обхождаме всички редове, като пропускаме първия (header)
    for row in runeword_table.find_all('tr')[1:]:
        cells = row.find_all('td')
        
        # Проверка за пълен ред (трябва да има 3 клетки в тази таблица)
        if len(cells) < 3:
            continue 

        # --- 1. Колона (Name, Runes, Min Lvl) ---
        # Взимаме HTML, за да разделим по <br>
        col1_html = str(cells[0])
        # Разделяме по <br>
        parts = re.split(r'<br\s*/?>', col1_html)

        if len(parts) >= 3:
            # Runeword Name (в <b> таг)
            name_match = re.search(r'<b>(.*?)<\/b>', parts[0])
            name = name_match.group(1).strip() if name_match else None
            
            # Runes
            runes_text = BeautifulSoup(parts[1], 'html.parser').get_text().replace('+', ' ').strip()
            runes = [f"{r.strip()} Rune" for r in runes_text.split() if r.strip()]
            
            # Min Level
            level_match = re.search(r'Level:\s*(\d+)', parts[2])
            min_level = int(level_match.group(1)) if level_match else 0
            
            if not name or not min_level: continue


            # --- 2. Колона (Item Type, Sockets) ---
            col2_text = cells[1].get_text()
            col2_parts = col2_text.split('\n')
            
            # Item Types
            item_types_raw = col2_parts[0].strip()
            item_types = [t.strip() for t in item_types_raw.split(',') if t.strip()]

            # Sockets
            sockets_match = re.search(r'(\d+)\s+sockets', col2_parts[1])
            sockets = int(sockets_match.group(1)) if sockets_match else 0
            
            if not sockets: continue
            
            
            # --- 3. Колона (Stats) ---
            stats = clean_stats_html(cells[2])

            # Добавяне към списъка
            runewords_list.append({
                "name": name,
                "runes": runes,
                "sockets": sockets,
                "item_types": item_types,
                "min_level": min_level,
                "stats": stats,
            })
            
    return runewords_list


def main():
    print(f"[*] Извличане на данни от {URL}...")
    
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status() # Хвърля HTTPError за лоши статуси (4xx или 5xx)
    except requests.exceptions.RequestException as e:
        print(f"[!!!] Грешка при достъп до URL: {e}")
        return

    # Парсване на таблицата
    runewords = parse_runeword_table(response.text)

    if not runewords:
        print("[!] Не бяха намерени Runeword-и. Проверете дали URL или селекторът на таблицата е правилен.")
        return

    # Създаване на финалния JSON обект
    final_data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": URL,
        "total_runewords": len(runewords),
        "runewords": runewords
    }

    # Записване на JSON файла
    try:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print(f"[+] Успешно генериран JSON файл: {OUTPUT_JSON_FILE} ({len(runewords)} Runewords)")
        
        # Печатаме първите 2 Runewords за визуализация
        print("\n--- ПРИМЕРЕН ПАРСИРАН РЕЗУЛТАТ (Първите 2) ---")
        print(json.dumps(runewords[:2], indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"[!!!] Грешка при записване на JSON файл: {e}")

if __name__ == "__main__":
    main()
