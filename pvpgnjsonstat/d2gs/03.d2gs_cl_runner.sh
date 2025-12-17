#!/bin/bash
WORKDIR="/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs"

ID_FILE="$WORKDIR/logs/game_ready_ids.txt"
EXPECT_CL_SCRIPT="$WORKDIR/04_d2gs_get_cl.exp"

# Даване на права за изпълнение на Expect скрипта
chmod +x $EXPECT_CL_SCRIPT

echo "Starting character list extraction for all games..."

# Четене на всеки ред от файла с ID-та
while IFS= read -r GAME_ID
do
    # Премахване на всички празни места и нови редове от ID
    CLEAN_ID=$(echo "$GAME_ID" | tr -d '[:space:]')
    
    if [ ! -z "$CLEAN_ID" ]; then
        echo "Processing Game ID: $CLEAN_ID"
        # Изпълнява Expect скрипта с ID-то
        $EXPECT_CL_SCRIPT "$CLEAN_ID"
    fi
done < "$ID_FILE"

echo "Character list extraction complete."
