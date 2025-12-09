
gcc char2json.c -o char2json
gcc allchar2json.c -o allchar2json

##
# прави отделен json за всички герой и акаунти 
./char2json -o /var/www/html/d2stats

##
# прави голям json за всички герой и акаунти 
/allchar2json -o /var/www/html/d2stats

