import os
import datetime
import xml.etree.ElementTree as ET
import json

# --- КОНФИГУРАЦИЯ ---
PVPGN_SERVER_XML = "/usr/local/pvpgn/var/pvpgn/status/server.xml"
PVPGN_STATUS_XML = "/usr/local/pvpgn/var/pvpgn/logs/pvpgnstatus.xml"

OUTPUT_JSON = "/var/www/html/pvpjsonstat/jsons/server_status.json"

PLATFORM_MAP = {
    'W3XP': 'Warcraft III: The Frozen Throne',
    'D2XP': 'Diablo II: Lord of Destruction',
    'SEXP': 'Starcraft: Brood War',
    'SSHR': 'Starcraft Shareware',
}

# --- ПАРСВАНЕ НА server.xml ---

def parse_server_xml(file_path):
    data = {
        "status": {},
        "users": [],
        "games": []
    }

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Version
    version = root.findtext("Version")
    if version:
        data["status"]["version"] = version

    # Uptime
    uptime = root.find("Uptime")
    if uptime is not None:
        data["status"]["uptime"] = {
            "days": int(uptime.findtext("Days", 0)),
            "hours": int(uptime.findtext("Hours", 0)),
            "minutes": int(uptime.findtext("Minutes", 0)),
            "seconds": int(uptime.findtext("Seconds", 0)),
        }

    # Users
    users_node = root.find("Users")
    if users_node is not None:
        for user in users_node.findall("user"):
            platform = user.findtext("clienttag")
            data["users"].append({
                "platform_tag": platform,
                "platform_name": PLATFORM_MAP.get(platform, platform),
                "username": user.findtext("name"),
                "version": user.findtext("version"),
                "region": user.findtext("country"),
                "channel_id": user.findtext("gameid")
            })

    # Games
    games_node = root.find("Games")
    if games_node is not None:
        for game in games_node.findall("game"):
            platform = game.findtext("clienttag")
            data["games"].append({
                "id": game.findtext("id"),
                "platform_tag": platform,
                "platform_name": PLATFORM_MAP.get(platform, platform),
                "players": None,
                "name": game.findtext("name")
            })

    return data

# --- ПАРСВАНЕ НА pvpgnstatus.xml ---

def parse_pvpgnstatus_xml(file_path):
    data = {}
    tree = ET.parse(file_path)
    root = tree.getroot()

    for child in root:
        if child.text:
            key = child.tag.replace('_', '')
            data[key] = child.text.strip()

    return data

# --- MAIN ---

def main():
    if not os.path.exists(PVPGN_SERVER_XML):
        print(f"Липсва файл: {PVPGN_SERVER_XML}")
        return

    if not os.path.exists(PVPGN_STATUS_XML):
        print(f"Липсва файл: {PVPGN_STATUS_XML}")
        return

    server_data = parse_server_xml(PVPGN_SERVER_XML)
    server_meta = parse_pvpgnstatus_xml(PVPGN_STATUS_XML)

    final_json_data = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_status": server_data.get("status", {}),
        "total_stats": server_meta,
        "active_users": server_data.get("users", []),
        "active_games": server_data.get("games", [])
    }

    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(final_json_data, f, ensure_ascii=False, indent=4)

        print(f"OK → JSON записан: {OUTPUT_JSON}")
        print(
            f"Потребители: {len(final_json_data['active_users'])}, "
            f"Игри: {len(final_json_data['active_games'])}"
        )

    except Exception as e:
        print(f"Грешка при запис: {e}")

if __name__ == "__main__":
    main()

