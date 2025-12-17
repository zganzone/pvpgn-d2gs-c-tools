#!/bin/bash


python3 /home/support/scripts-tools/d2cpp/pvpgnjsonstat/01.server_status_json.py
sleep 1
python3 /home/support/scripts-tools/d2cpp/pvpgnjsonstat/02.reportsscJSON.py
sleep 1
bash /home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/00.start.sh
