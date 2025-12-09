#!/bin/bash

rsync -avr /usr/local/pvpgn/var/pvpgn/logs/games.txt /var/www/html/webportal/data/
sleep 1
/home/support/scripts-tools/d2cpp/d2console/01.d2gs_get_gl.exp
sleep 1
/home/support/scripts-tools/d2cpp/d2console/02.bashawksed.sh
sleep 1
/home/support/scripts-tools/d2cpp/d2console/03.d2gs_cl_runner.sh
sleep 1
#/home/support/scripts-tools/d2cpp/d2console/04_d2gs_get_cl.exp
/home/support/scripts-tools/d2cpp/d2console/05.gameinfo2json.py
sleep 1
/home/support/scripts-tools/d2cpp/d2console/06.allchar2json -o /var/www/html/d2console/
sleep 1
/home/support/scripts-tools/d2cpp/d2console/07.char2json -o /var/www/html/d2console/
