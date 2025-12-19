
gcc char2json.c -o char2json
gcc allchar2json.c -o allchar2json

##
# прави отделен json за всички герой и акаунти 
./char2json -o /var/www/html/d2stats

##
# прави голям json за всички герой и акаунти 
/allchar2json -o /var/www/html/d2stats


##
# scanner for binari markers on hero
#Намерен маркер 'JM' на бинарен отместване (offset): 2033
#Намерен маркер 'JM' на бинарен отместване (offset): 2063
#Намерен маркер 'JM' на бинарен отместване (offset): 2069
#Намерен маркер 'JM' на бинарен отместване (offset): 2073
#Намерен маркер 'JM' на бинарен отместване (offset): 2098
#Намерен маркер 'JM' на бинарен отместване (offset): 2146
#Намерен маркер 'JM' на бинарен отместване (offset): 2175

./scanner  /usr/local/pvpgn/var/pvpgn/charsave/tesla


##
# parsin char file to json
/d2parser   -c sorsi -a zgan -pvpdir=/usr/local/pvpgn/var/pvpgn/charsave -json -f /tmp/sorsi.json
readfile() Error: Cannot open file '/usr/local/pvpgn/var/pvpgn/charsave/zgan/sorsi': No such file or directory
{
  "character_info": {
    "name": "sorsi",
    "account_name": "zgan",
    "level": 86,
    "class": "Sorceress"
  },
  "item_stats": {
    "total_items": 35,
    "low_quality": 0,
    "normal": 12,
    "high_quality": 0,
    "magic": 6,
    "set": 7,
    "rare": 0,
    "unique": 9,
    "crafted": 0,
    "soj_count": 0
  }
}
