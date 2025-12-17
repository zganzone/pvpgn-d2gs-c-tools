WORKDIR="/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs"
#WEBDIR="/var/www/html/pvpjsonstat/jsons

cat $WORKDIR/logs/d2gs_gl_raw.txt | grep -w N | sed 's/ /_/g' | sed s'/_\+/|/g' | sed 's/||/|/g' | awk -F "|" '{print $4}' > $WORKDIR/logs/game_ready_ids.txt
echo "Game id file"
echo "$WORKDIR/logs/game_ready_ids.txt"
cat $WORKDIR/logs/game_ready_ids.txt
