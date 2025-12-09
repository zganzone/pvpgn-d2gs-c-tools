#!/usr/bin/env python3
# generate_report.py
# Scans PvPGN charsaves for items and generates a single HTML report + CSV/JSON exports.
# Requires: d2lib (pip install d2lib)

from d2lib.files import D2SFile
import os, glob, html, json, csv
from datetime import datetime
from collections import defaultdict

# CONFIG
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
CHARINFO_DIR = "/usr/local/pvpgn/var/pvpgn/charinfo"
OUTPUT_HTML = "/var/www/html/index2.html"
OUTPUT_JSON = "/var/www/html/pvpgn_items.json"
OUTPUT_CSV = "/var/www/html/pvpgn_items.csv"

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Heuristic category mapping by item.code prefix or substring in name.
# Extend as you discover more base codes.
CATEGORY_MAP = {
    "amu": "Amulet",
    "ring": "Ring",
    "rin": "Ring",
    "bel": "Belt",
    "belt": "Belt",
    "cm": "Charm",     # charms often code like cm1 / cm2 / cm3 in some parsers
    "charm": "Charm",
    "wxp": "Weapon",   # placeholder
    "swd": "Weapon",
    "axe": "Weapon",
    "axe": "Weapon",
    "bow": "Weapon",
    "jew": "Jewel",
    "amu": "Amulet",
    "tkb": "Book",
    "tbk": "Book",
    "orb": "Orb",
    "shld": "Shield",
    "shm": "Shield",
    "hel": "Helmet",
    "cap": "Helmet",
    "arm": "Armor",
    "armor": "Armor",
    "glv": "Gloves",
    "gth": "Gloves",
    "boots": "Boots",
    # add more as needed
}

# Charm size mapping heuristics (you can refine)
CHARM_SIZE_MAP = {
    # these codes/names are heuristic; update when you find exact mapping
    "grand": ["Annihilus", "Gheed's Fortune"], # example uniques that are small grand? adjust as needed
    # If item.name contains "small charm" or code contains some marker, place accordingly
}

# helper: find the account owning the char by scanning charinfo folder
def find_account_for_character(char_name):
    try:
        for account in os.listdir(CHARINFO_DIR):
            acc_path = os.path.join(CHARINFO_DIR, account)
            if not os.path.isdir(acc_path):
                continue
            try:
                if char_name in os.listdir(acc_path):
                    return account
            except Exception:
                continue
    except Exception:
        pass
    return "Unknown"

# helper: determine category using item attributes + name heuristics
def determine_category(item):
    # try common attributes
    code = None
    for attr in ("code", "basecode", "base_code", "base_item", "base_item_code"):
        code = getattr(item, attr, None)
        if code:
            # ensure code is string
            code = str(code).lower()
            break

    name = getattr(item, "name", "")
    if isinstance(name, bytes):
        try:
            name = name.decode("utf-8", errors="ignore")
        except Exception:
            name = str(name)

    nlower = (name or "").lower()

    # check code-based mapping
    if code:
        for key, cat in CATEGORY_MAP.items():
            if key in code:
                return cat
    # fallback: name-based mapping
    for key, cat in CATEGORY_MAP.items():
        if key in nlower:
            return cat

    # weapons detection from name keywords
    WEAPON_KEYWORDS = ("sword", "axe", "dagger", "bow", "spear", "mace", "staff", "hammer", "flail", "bow")
    ARMOR_KEYWORDS = ("armor", "mail", "plate", "robe", "helm", "cap", "shield", "glove", "gloves", "boots", "belt", "ring", "amulet", "charm")
    for k in WEAPON_KEYWORDS:
        if k in nlower:
            return "Weapon"
    for k in ARMOR_KEYWORDS:
        if k in nlower:
            return "Armor/Accessory"

    # final fallback
    return "Misc"

# helper: detect charm size
def charm_size(item):
    name = getattr(item, "name", "")
    if not name:
        return None
    n = name.lower()
    # heuristics:
    if "grand" in n or "giant" in n:
        return "Grand"
    if "small" in n:
        return "Small"
    if "large" in n:
        return "Large"
    # unique charms (Annihilus, Gheed) treat separately as "Unique Charm"
    if "annihilus" in n or "gheed" in n:
        return "Unique"
    # fallback unknown
    return "Unknown"

# gather data rows
rows = []
accounts_seen = set()
for filepath in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
    filename = os.path.basename(filepath)
    try:
        d2s = D2SFile(filepath)
    except Exception as e:
        # skip unreadable files
        # print("skip", filepath, e)
        continue

    # character name fallback to filename
    char_name = getattr(d2s, "name", None) or filename
    account_name = find_account_for_character(filename)
    accounts_seen.add(account_name)

    # combine inventory + stash when available
    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", None)
    if stash_items:
        if isinstance(stash_items, list):
            all_items += stash_items
        else:
            try:
                all_items += list(stash_items)
            except Exception:
                pass

    # iterate items and produce a row per item for CSV/JSON
    for item in all_items:
        try:
            it_name = getattr(item, "name", None) or ""
            it_code = None
            for attr in ("code", "basecode", "base_code", "base_item", "base_item_code"):
                val = getattr(item, attr, None)
                if val:
                    it_code = str(val)
                    break
            is_unique = bool(getattr(item, "is_unique", False))
            is_set = bool(getattr(item, "is_set", False))
            is_rune = bool(getattr(item, "is_rune", False)) or (getattr(item, "rune_id", None) is not None)
            rune_id = getattr(item, "rune_id", None)
            category = determine_category(item)
            charm_sz = None
            if category == "Charm":
                charm_sz = charm_size(item)

            rows.append({
                "account": account_name,
                "character": char_name,
                "item_name": it_name,
                "item_code": it_code,
                "category": category,
                "is_unique": is_unique,
                "is_set": is_set,
                "is_rune": is_rune,
                "rune_id": rune_id,
                "charm_size": charm_sz,
            })
        except Exception:
            continue

# create JSON & CSV exports
with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
    json.dump(rows, jf, ensure_ascii=False, indent=2)

with open(OUTPUT_CSV, "w", encoding="utf-8", newline='') as cf:
    writer = csv.DictWriter(cf, fieldnames=["account","character","item_name","item_code","category","is_unique","is_set","is_rune","rune_id","charm_size"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# Group rows by account for HTML table grouping
by_account = defaultdict(list)
for r in rows:
    by_account[r["account"]].append(r)

# HTML generation
html_lines = [
    "<!DOCTYPE html>",
    "<html><head><meta charset='utf-8'><title>PvPGN Unique/Set Items Report</title>",
    "<meta charset='utf-8'/>",
    "<style>",
    "body{font-family:Arial,Helvetica,sans-serif;margin:16px;background:#f8f8f8;color:#222}",
    "h1{margin:0 0 8px 0}",
    ".meta{margin-bottom:16px;color:#444}",
    "table{width:100%;border-collapse:collapse;margin-top:12px}",
    "th, td{border:1px solid #ddd;padding:8px;vertical-align:top}",
    "th{background:#f0f0f0;text-align:left}",
    ".unique{color:orange;font-weight:bold}",
    ".set{color:green;font-weight:bold}",
    ".rune{color:blue}",
    ".account-row{cursor:pointer}",
    ".account-header{padding:10px;margin-top:10px;border-radius:6px}",
    ".controls{margin-top:10px;margin-bottom:10px}",
    ".searchbox{padding:6px;width:260px;border:1px solid #ccc;border-radius:4px}",
    ".btn{display:inline-block;padding:6px 8px;margin-left:6px;background:#2d7bf6;color:#fff;border-radius:4px;text-decoration:none}",
    ".btn.gray{background:#666}",
    ".small{font-size:0.9em;color:#666}",
    "</style>",
    # minimal client-side JS for expand/collapse, search, sorting, expand-all
    "<script>",
    "function toggleAccount(id){",
    "  var el=document.getElementById(id);",
    "  if(!el) return;",
    "  el.style.display = (el.style.display==='none') ? '' : 'none';",
    "}",
    "function expandAll(){",
    "  var lists=document.getElementsByClassName('acct-body');",
    "  for(var i=0;i<lists.length;i++) lists[i].style.display='';",
    "}",
    "function collapseAll(){",
    "  var lists=document.getElementsByClassName('acct-body');",
    "  for(var i=0;i<lists.length;i++) lists[i].style.display='none';",
    "}",
    "function searchTable(){",
    "  var q=document.getElementById('search').value.toLowerCase();",
    "  var rows=document.querySelectorAll('table.data tr.data-row');",
    "  rows.forEach(function(r){",
    "    var txt=r.textContent.toLowerCase();",
    "    r.style.display = txt.indexOf(q) !== -1 ? '' : 'none';",
    "  });",
    "}",
    # simple client-side sort by column index
    "function sortTable(colIndex){",
    "  var table=document.getElementById('main-table');",
    "  var tbody=table.tBodies[0];",
    "  var rows=Array.prototype.slice.call(tbody.querySelectorAll('tr.data-row'));",
    "  var asc = table.getAttribute('data-sort-col')==colIndex && table.getAttribute('data-sort-dir')!='asc';",
    "  rows.sort(function(a,b){",
    "    var A=a.children[colIndex].textContent.trim().toLowerCase();",
    "    var B=b.children[colIndex].textContent.trim().toLowerCase();",
    "    if(A<B) return asc? -1:1; if(A>B) return asc?1:-1; return 0;",
    "  });",
    "  rows.forEach(function(r){ tbody.appendChild(r); });",
    "  table.setAttribute('data-sort-col', colIndex);",
    "  table.setAttribute('data-sort-dir', asc? 'asc':'desc');",
    "}",
    # client-side export CSV from table (also JSON by reading exported file server-side is OK)
    "function downloadCSV(){ window.location='/pvpgn_items.csv'; }",
    "function downloadJSON(){ window.location='/pvpgn_items.json'; }",
    "</script>",
    "</head><body>",
    f"<h1>PvPGN Items Report</h1>",
    f"<div class='meta'><b>Generated:</b> {html.escape(timestamp)} &nbsp; <span class='small'>({len(rows)} items, {len(by_account)} accounts)</span></div>",
    "<div class='controls'>",
    "<input id='search' class='searchbox' placeholder='Search characters/items/accounts...' oninput='searchTable()'/>",
    "<a class='btn' onclick='expandAll()'>Expand All</a>",
    "<a class='btn gray' onclick='collapseAll()'>Collapse All</a>",
    "<a class='btn' onclick='downloadCSV()'>Export CSV</a>",
    "<a class='btn' onclick='downloadJSON()'>Export JSON</a>",
    "</div>",
    "<table id='main-table' class='data' data-sort-col='' data-sort-dir=''>",
    "<thead><tr>",
    "<th onclick='sortTable(0)'>Account</th>",
    "<th onclick='sortTable(1)'>Character</th>",
    "<th onclick='sortTable(2)'>Item Name</th>",
    "<th onclick='sortTable(3)'>Category</th>",
    "<th onclick='sortTable(4)'>Charm Size</th>",
    "<th onclick='sortTable(5)'>Unique/Set</th>",
    "</tr></thead>",
    "<tbody>"
]

# generate a deterministic color per account
def account_color(name):
    # simple hash to color
    h = 0
    for ch in name:
        h = (h*131 + ord(ch)) & 0xFFFFFFFF
    # pick a pastel color from hash
    r = 150 + (h & 0x3F)
    g = 150 + ((h>>6) & 0x3F)
    b = 150 + ((h>>12) & 0x3F)
    return f"rgb({r%256},{g%256},{b%256})"

# create table rows from rows list
row_id = 0
for acct, items in sorted(by_account.items(), key=lambda x: x[0].lower()):
    acct_color = account_color(acct)
    # render each item as its own table row (so sorting/search works)
    for it in sorted(items, key=lambda x: (x["character"].lower(), x["item_name"].lower())):
        row_id += 1
        acc_html = html.escape(it["account"])
        char_html = html.escape(it["character"])
        name_html = html.escape(it["item_name"]) or "(unknown)"
        cat_html = html.escape(it["category"] or "")
        charm_html = html.escape(it["charm_size"] or "")
        uniq_html = ""
        if it["is_unique"]:
            uniq_html = "<span class='unique'>Unique</span>"
        elif it["is_set"]:
            uniq_html = "<span class='set'>Set</span>"
        # make item display colored for unique/set
        display_name = name_html
        if it["is_unique"]:
            display_name = f"<span class='unique'>{name_html}</span>"
        elif it["is_set"]:
            display_name = f"<span class='set'>{name_html}</span>"

        # row with account background color
        html_lines.append(
            f"<tr class='data-row' style='background:{acct_color}22'>"
            f"<td>{acc_html}</td>"
            f"<td>{char_html}</td>"
            f"<td>{display_name}</td>"
            f"<td>{cat_html}</td>"
            f"<td>{charm_html}</td>"
            f"<td>{uniq_html}</td>"
            f"</tr>"
        )

# if no rows, print note
if not rows:
    html_lines.append("<tr><td colspan='6'>No items found.</td></tr>")

html_lines.append("</tbody></table>")
html_lines.append("<p class='small'>Notes: Item classification is heuristic and can be expanded by editing the CATEGORY_MAP/CHARM_SIZE_MAP in the script.</p>")
html_lines.append("</body></html>")

# write HTML
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html_lines))

print("Generated:", OUTPUT_HTML)
print("Also exported:", OUTPUT_JSON, OUTPUT_CSV)
