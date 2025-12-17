#!/usr/bin/env python3
import xml.etree.ElementTree as ET

XML_FILE = "/usr/local/pvpgn/var/pvpgn/ladders/d2ladder.xml"
HTML_FILE = "/var/www/html/pvpjsonstat/webladder.html"

tree = ET.parse(XML_FILE)
root = tree.getroot()

html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DarkPsy Ladder</title>
<style>
body {
    font-family: 'Garamond', 'Times New Roman', serif;
    background-color: #1c1c1c; /* dark Diablo-style */
    color: #f5d083; /* warm gold text */
    margin: 0;
    padding: 0;
}

h1, h2 {
    text-align: center;
    color: #f5d083;
    text-shadow: 2px 2px 4px #000; /* subtle shadow for depth */
}

table {
    border-collapse: collapse;
    width: 90%;
    margin: 20px auto;
    background-color: #2b2b2b; /* dark parchment feel */
    border: 2px solid #f5d083;
    box-shadow: 0 0 15px rgba(245, 208, 131, 0.5);
}

th, td {
    border: 1px solid #f5d083;
    padding: 8px 12px;
    text-align: center;
    color: #f5d083;
}

th {
    background-color: #3a2f2f; /* slightly darker header */
    text-shadow: 1px 1px 2px #000;
}

tr:nth-child(even) {
    background-color: #2e2b2b;
}

tr:hover {
    background-color: #5a3e1b; /* warm highlight on hover */
    color: #fff;
    font-weight: bold;
}
</style>
</head>
<body>
<h1>DarkPsy Ladder</h1>
"""

def get_text(elem, tag):
    child = elem.find(tag)
    if child is not None and child.text is not None:
        return child.text.strip()
    return ""

for ladder in root.findall('ladder'):
    ladder_type = get_text(ladder, 'type')

    # Only include ladder types 27-34
    try:
        if not (27 <= int(ladder_type) <= 34):
            continue
    except ValueError:
        continue

    ladder_mode = get_text(ladder, 'mode')

    html += "<table>"
    html += "<tr><th>Rank</th><th>Name</th><th>Level</th><th>Experience</th><th>Class</th><th>Prefix</th><th>Status</th></tr>"

    for char in ladder.findall('char'):
        rank = get_text(char, 'rank')
        name = get_text(char, 'name')
        level = get_text(char, 'level')
        experience = get_text(char, 'experience')
        char_class = get_text(char, 'class')
        prefix = get_text(char, 'prefix')
        status = get_text(char, 'status')

        html += f"<tr><td>{rank}</td><td>{name}</td><td>{level}</td><td>{experience}</td><td>{char_class}</td><td>{prefix}</td><td>{status}</td></tr>"

    html += "</table>"
html += "</body></html>"

with open(HTML_FILE, "w") as f:
    f.write(html)

print(f"[+] Webstat generated: {HTML_FILE}")
