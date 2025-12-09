#!/bin/bash
rm /home/support/scripts-tools/d2cpp/d2console/logs/cl_output/* -f
rm /home/support/scripts-tools/d2cpp/d2console/logs/* -f

cp /usr/local/pvpgn/var/pvpgn/logs/games.txt /var/www/html/d2console/data/games.txt

cp /usr/local/pvpgn/var/pvpgn/ladders/d2ladder.xml /var/www/html/d2console/data/
sleep 1
/home/support/scripts-tools/d2cpp/d2console/01.d2gs_get_gl.exp
sleep 1
/home/support/scripts-tools/d2cpp/d2console/02.bashawksed.sh
sleep 1
/home/support/scripts-tools/d2cpp/d2console/03.d2gs_cl_runner.sh
sleep 1
#/home/support/scripts-tools/d2cpp/d2console/04_d2gs_get_cl.exp
python3 /home/support/scripts-tools/d2cpp/d2console/05.gameinfo2json.py
sleep 1
/home/support/scripts-tools/d2cpp/d2console/06.allchar2json -o /var/www/html/d2console/data/
sleep 1
/home/support/scripts-tools/d2cpp/d2console/07.char2json -o /var/www/html/d2console/data/
sleep 1
python3 /home/support/scripts-tools/d2cpp/d2console/z1.weball_new.py
sleep 1
python3 /home/support/scripts-tools/d2cpp/d2console/08_build_ladder.py
/home/support/scripts-tools/d2cpp/d2console/cronfile.sh
