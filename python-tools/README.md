##
# get all info requer items/*txt from original d2data.mp3

python3 01.fullstatsperhero.py  sorsi
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

##
# as above but withoit runes 
python3 01.hero2cli.py  sorsi

##
# only runes - the charecter is hardcoded in py file:

# D2_DATA_DIR = "/home/support/scripts-tools/d2cpp/pvpgnjsonstat/d2gs/items/" 
# TARGET_CHAR_FILE_RUNIONE = "runione"
# TEST_CHAR_PATH = os.path.join("/usr/local/pvpgn/var/pvpgn/charsave", TARGET_CHAR_FILE_RUNIONE)

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
python3 03.charecter_runes_with_attrs.py 

##
# find runes for runeword 

python3 04.findruneword.py "Call To Arms"


-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


##
# scan all charecters for runes
 python3 04.total_rune_inventory.py 

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

##
# as above but with but present who has the runes 
python3 05.detailed_rune_inventory.py 


-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

##
# generate json with all runes and atributes
python3 06.generate_rune_json.py 
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

##
# read pvpgn xml file for stat and build html page
# PVPGN_STATUS_FILE = "/usr/local/pvpgn/var/pvpgn/status/server.dat"
# PVPGN_GAMES_LOG = "/usr/local/pvpgn/var/pvpgn/logs/games.txt"

pvpgn-index-status.py

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

## read all statistik from repot
# /usr/local/pvpgn/var/pvpgn/reports

pvpgn_starcraft_statpage_json.py
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

## as above but build json
pvpgn_starcraft_statpage.py
