#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path

PVPSTATUS_FILE = "/usr/local/pvpgn/var/pvpgn/logs/pvpgnstatus.xml"
SERVER_STATUS_FILE = "/usr/local/pvpgn/var/pvpgn/status/server.xml"


def read_pvpgn_status():
    print("Reading PvPGN server summary status...")

    tree = ET.parse(PVPSTATUS_FILE)
    root = tree.getroot()

    data = {
        "address": root.findtext("address"),
        "port": root.findtext("port"),
        "location": root.findtext("location"),
        "software": root.findtext("software"),
        "version": root.findtext("version"),
        "users": root.findtext("users"),
        "games": root.findtext("games"),
        "uptime": root.findtext("uptime"),
    }

    print("Server Information:")
    for key, value in data.items():
        print(f"  {key.capitalize()}: {value}")

    print()
    return data


def read_server_status():
    print("Reading detailed server status...")

    tree = ET.parse(SERVER_STATUS_FILE)
    root = tree.getroot()

    uptime = root.find("Uptime")
    print("Uptime:")
    print(
        f"  {uptime.findtext('Days')} days, "
        f"{uptime.findtext('Hours')} hours, "
        f"{uptime.findtext('Minutes')} minutes, "
        f"{uptime.findtext('Seconds')} seconds"
    )

    users = root.find("Users")
    print(f"\nOnline Users: {users.findtext('Number')}")

    for user in users.findall("user"):
        print(
            f"  User: {user.findtext('name')} | "
            f"Game: {user.findtext('clienttag')} | "
            f"Version: {user.findtext('version')} | "
            f"Country: {user.findtext('country')}"
        )

    games = root.find("Games")
    if games is not None:
        print(f"\nActive Games: {games.findtext('Number')}")
        for game in games.findall("game"):
            print(
                f"  Game ID: {game.findtext('id')} | "
                f"Name: {game.findtext('name')} | "
                f"Client: {game.findtext('clienttag')}"
            )

    print()


def main():
    if not Path(PVPSTATUS_FILE).exists():
        print("Error: PvPGN status file not found.")
        return

    if not Path(SERVER_STATUS_FILE).exists():
        print("Error: Server status file not found.")
        return

    read_pvpgn_status()
    read_server_status()


if __name__ == "__main__":
    main()
