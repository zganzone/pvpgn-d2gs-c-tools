#!/bin/bash -x
WORKDIR="/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs"
WEBDIR="/var/www/html/pvpjsonstat/jsons"
rm $WORKDIR/logs/cl_output/* -f
rm $WORKDIR/logs/* -f

cp /usr/local/pvpgn/var/pvpgn/logs/games.txt $WEBDIR/games.txt

cp /usr/local/pvpgn/var/pvpgn/ladders/d2ladder.xml $WEBDIR/
sleep 1
$WORKDIR/01.d2gs_get_gl.exp
sleep 1
$WORKDIR/02.bashawksed.sh
sleep 1
$WORKDIR/03.d2gs_cl_runner.sh
sleep 1
python3 $WORKDIR/05.gameinfo2json.py
sleep 1
python3 $WORKDIR/06_build_ladder.py
sleep 1
python3 $WORKDIR/07.generate_items_json.py
sleep 0.5
python3 $WORKDIR/06.generate_rune_json.py
sleep 0.5
python3 $WORKDIR/08.d2gs_time_ands_status_json.py
#$WORKDIR/cronfile.sh
sleep 1
#python3 $WORKDIR/10.charitemstat.py
#$WORKDIR/07.char2json -o /var/www/html/data/
#python3 $WORKDIR/05.gameinfo2json.py

##
# external  http://darkpsy.space:8998/test4.html
#
#python3 /home/support/scripts-tools/d2cpp/pvpgn_stats.py
