#!/bin/bash

/usr/bin/python3 /home/support/scripts-tools/d2cpp/python-tools/d2gs-py/01.pvpgn_json_portal.py
sleep 0.5
/usr/bin/python3 /home/support/scripts-tools/d2cpp/python-tools/d2gs-py/02.d2gs_live_monitor_full_json.py
sleep 0.5
#/usr/bin/python3 /home/support/scripts-tools/d2cpp/python-tools/d2gs-py/03.pvpgn_log_json.py > /var/www/html/pvpjsonstat/logs/games.json

