#!/usr/bin/env python3
"""
PvPGN item report - enhanced:
- Account | Character | Unique/Set | Runes | Rings | Belts | Amulets/Medallions | Charms (small/large/grand) | Weapons | Armor | Other
- search/filter, sorting, expand/collapse, color per account, export JSON/CSV
- No auto-refresh
"""
from d2lib.files import D2SFile
import os, glob, html, json, csv
from datetime import datetime
from collections import defaultdict

# === Configuration ===
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
CHARINFO_DIR = "/usr/local/pvpgn/var/pvpgn/charinfo"
OUTPUT_HTML = "/var/www/html/webstat.html"
OUTPUT_JSON = "/var/www/html/items_export.json"
OUTPUT_CSV  = "/var/www/html/items_export.csv"

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Best-effort mapping from item.code (from d2lib) to human item type categories
# Extend this mapping if you find codes not present for your saves.
CODE_TO_TYPE = {
    # amulet
    "amu": "amulet",
    # ring
    "rin": "ring", "rin": "ring",
    # belt
    "bel": "belt",
    # charm codes seen in your output: cm1, cm2, cm3
    "cm1": "charm_small",
    "cm2": "charm_large",
    "cm3": "charm_grand",
    # jewelry generic
    "jew": "jewelry",
    # weapons / armor (examples)
    "swd": "weapon", "swf": "weapon", "axe": "weapon", "axe": "weapon",
    "bow": "weapon", "xbow": "weapon", "stf": "weapon", "bst": "weapon",
    "amu": "amulet",
    # shields / armor
    "shd": "armor", "plt": "armor", "plt": "armor", "ht": "armor",
    # jewels / gems
    "gem": "gem", "gld": "gold", "tkp": "token",
    # books / tomes etc
    "tbk": "book",
    # other/skill items
    "uap": "helmet",  # harlequin crest = uap (uniq helm)
    # fallback mapping placeholders
}

# Helper detection: if item.code not in CODE_TO_TYPE, try suffix/prefix heuristics
def detect_type_from_code_and_name(code, name):
    if not code:
        code = ""
    if not name:
        name = ""
    code = code.lower()
    name = name.lower()
    # direct mapping
    if code in CODE_TO_TYPE:
        return CODE_TO_TYPE[code]
    # heuristics by name
    if "ring" in name or "band" in name:
        return "ring"
    if "amulet" in name or "gorget" in name or "neck" in name:
        return "amulet"
    if "belt" in name:
        return "belt"
    if "charm" in name or "annihilus" in name or "gheed" in name:
        # charm size cannot be guaranteed by name but treat as generic charm
        return "charm"
    if "helm" in name or "crown" in name or "mask" in name:
        return "helmet"
    if "shield" in name:
        return "shield"
    # weapon keywords
    for kw in ("sword","axe","mace","dagger","bow","crossbow","staff","polearm","spear","hammer"):
        if kw in name:
            return "weapon"
    # armor keywords
    for kw in ("armor","plate","mail","leather","chain","robe","shield"):
        if kw in name:
            return "armor"
    # fallback
    return "other"

# Finds account name (BNET account) for a character filename using charinfo dirs
def find_account_for_character(char_filename):
    # char_filename may be the name of charsave file (same as character)
    # search CHARINFO_DIR subfolders for this filename
    try:
        for acc in os.listdir(CHARINFO_DIR):
            p = os.path.join(CHARINFO_DIR, acc)
            if not os.path.isdir(p):
                continue
            # list files inside
            try:
                if char_filename in os.listdir(p):
                    return acc
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return "Unknown"

# Gather data
rows = []
for path in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
    try:
        d2s = D2SFile(path)
    except Exception:
        # skip unreadable
        continue

    char_fname = os.path.basename(path)
    char_name = getattr(d2s, "name", None) or char_fname
    account_name = find_account_for_character(char_fname)

    # combine inventory + stash if present
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

    # categorize items
    unique_set = []
    runes = []
    rings = []
    belts = []
    amulets = []
    charms_small = []
    charms_large = []
    charms_grand = []
    weapons = []
    armors = []
    other = []

    for item in all_items:
        # get attributes safely
        name = getattr(item, "name", "") or ""
        code = getattr(item, "code", "") or ""
        is_unique = getattr(item, "is_unique", False)
        is_set = getattr(item, "is_set", False)

        # track unique/set separately
        if is_unique:
            unique_set.append((name, "unique"))
        elif is_set:
            unique_set.append((name, "set"))

        # runes
        if getattr(item, "is_rune", False):
            rid = getattr(item, "rune_id", None)
            runes.append(name or (f"Rune ID {rid}" if rid is not None else "Rune"))
            continue
        rid = getattr(item, "rune_id", None)
        if rid is not None and not name:
            # fallback to rune id item without name
            runes.append(f"Rune ID {rid}")
            continue

        # charms detection by code prefix (cm1/cm2/cm3 shown in your qt.py)
        code_l = code.lower()
        if code_l.startswith("cm"):
            # cm1 / cm2 / cm3 heuristics
            if code_l.startswith("cm1"):
                charms_small.append(name or code)
            elif code_l.startswith("cm2"):
                charms_large.append(name or code)
            elif code_l.startswith("cm3"):
                charms_grand.append(name or code)
            else:
                # generic charm
                charms_small.append(name or code)
            continue

        # detect type by mapping or heuristics
        itype = detect_type_from_code_and_name(code, name)

        if itype == "ring":
            rings.append(name)
        elif itype == "belt":
            belts.append(name)
        elif itype == "amulet":
            amulets.append(name)
        elif itype.startswith("charm"):
            # fallback if charm detection by code didn't trigger
            charms_small.append(name)
        elif itype == "weapon":
            weapons.append(name)
        elif itype in ("armor","helmet","shield"):
            armors.append(name)
        elif itype == "other":
            other.append(name)
        else:
            # put into other if unknown
            other.append(name)

    rows.append({
        "account": account_name,
        "charfile": char_fname,
        "charname": char_name,
        "unique_set": unique_set,
        "runes": runes,
        "rings": rings,
        "belts": belts,
        "amulets": amulets,
        "charms_small": charms_small,
        "charms_large": charms_large,
        "charms_grand": charms_grand,
        "weapons": weapons,
        "armors": armors,
        "other": other,
    })

# Save JSON and CSV exports (single exports)
with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
    json.dump({"generated": timestamp, "rows": rows}, jf, ensure_ascii=False, indent=2)

# CSV: one row per character, serializing lists as JSON strings
with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as cf:
    writer = csv.writer(cf)
    header = ["account","charfile","charname","unique_set","runes","rings","belts","amulets","charms_small","charms_large","charms_grand","weapons","armors","other"]
    writer.writerow(header)
    for r in rows:
        writer.writerow([
            r["account"], r["charfile"], r["charname"],
            json.dumps(r["unique_set"], ensure_ascii=False),
            json.dumps(r["runes"], ensure_ascii=False),
            json.dumps(r["rings"], ensure_ascii=False),
            json.dumps(r["belts"], ensure_ascii=False),
            json.dumps(r["amulets"], ensure_ascii=False),
            json.dumps(r["charms_small"], ensure_ascii=False),
            json.dumps(r["charms_large"], ensure_ascii=False),
            json.dumps(r["charms_grand"], ensure_ascii=False),
            json.dumps(r["weapons"], ensure_ascii=False),
            json.dumps(r["armors"], ensure_ascii=False),
            json.dumps(r["other"], ensure_ascii=False),
        ])

# === Build HTML with JS controls ===
html_parts = []
html_parts.append("<!doctype html><html><head><meta charset='utf-8'><title>PvPGN Item Report</title>")
html_parts.append("<style>")
html_parts.append("body{font-family:Arial,Helvetica,sans-serif;background:#f7f7f7;padding:18px}")
html_parts.append("h1{margin:0 0 12px 0}")
html_parts.append("table{border-collapse:collapse;width:100%}")
html_parts.append("th,td{border:1px solid #ddd;padding:8px;vertical-align:top}")
html_parts.append("th{background:#efefef;cursor:pointer}")
html_parts.append(".unique{color:orange;font-weight:bold}")
html_parts.append(".set{color:green;font-weight:bold}")
html_parts.append(".rune{color:blue}")
html_parts.append(".account-row{background:#ffffff}")
html_parts.append(".collapsed .account-details{display:none}")
html_parts.append(".account-header{padding:6px;margin:2px 0;cursor:pointer}")
html_parts.append("</style></head><body>")

html_parts.append(f"<p><b>Generated:</b> {html.escape(timestamp)}</p>")
html_parts.append(f'<p><a href="/index2.html"><H1>More Stats</h1></a></p>')
html_parts.append("<h1>PvPGN Items (Unique / Set / Charms / Rings / Belts / Amulets)</h1>")

# Controls
html_parts.append("<div style='margin-bottom:10px'>")
html_parts.append("<button onclick='expandAll()'>Expand All</button>")
html_parts.append("<button onclick='collapseAll()'>Collapse All</button>")
html_parts.append("&nbsp; <input id='searchInput' placeholder='Search character/account/item...' oninput='filterTable()' style='width:320px;padding:4px' />")
html_parts.append("&nbsp; <button onclick='exportJSON()'>Export JSON</button>")
html_parts.append("&nbsp; <button onclick='exportCSV()'>Export CSV</button>")
html_parts.append("</div>")

# Table header
html_parts.append("<table id='itemsTable'>")
html_parts.append("<thead><tr>")
html_parts.append("<th data-col='account'>Account</th>")
html_parts.append("<th data-col='charname'>Character</th>")
html_parts.append("<th data-col='unique_set'>Unique / Set</th>")
html_parts.append("<th data-col='runes'>Runes</th>")
html_parts.append("<th data-col='rings'>Rings</th>")
html_parts.append("<th data-col='belts'>Belts</th>")
html_parts.append("<th data-col='amulets'>Amulets</th>")
html_parts.append("<th data-col='charms'>Charms (S/L/G)</th>")
html_parts.append("<th data-col='weapons'>Weapons</th>")
html_parts.append("<th data-col='armors'>Armor</th>")
html_parts.append("<th data-col='other'>Other</th>")
html_parts.append("</tr></thead><tbody>")

# Color palette per account (cycled)
palette = ["#ffffff","#fffbe6","#f7fff2","#eef7ff","#fff0f6","#f9f5ff"]

acc_to_color = {}
acc_list = sorted({r["account"] for r in rows})
for i, acc in enumerate(acc_list):
    acc_to_color[acc] = palette[i % len(palette)]

# rows
for r in rows:
    acct = html.escape(r["account"])
    charfile = html.escape(r["charfile"])
    charname = html.escape(r["charname"])
    color = acc_to_color.get(r["account"], "#ffffff")

    # unique/set formatted
    us_html = []
    for name, kind in r["unique_set"]:
        cls = "unique" if kind == "unique" else "set"
        us_html.append(f"<span class='{cls}'>{html.escape(name)}</span>")
    us_cell = ", ".join(us_html) if us_html else "<i>—</i>"

    def join_span(lst, cls=""):
        if not lst:
            return "<i>—</i>"
        return ", ".join(html.escape(x) if not cls else f"<span class='{cls}'>{html.escape(x)}</span>" for x in lst)

    runes_cell = join_span(r["runes"], "rune")
    rings_cell = join_span(r["rings"])
    belts_cell = join_span(r["belts"])
    amulets_cell = join_span(r["amulets"])
    charms_cell = ", ".join([
        f"S:{len(r['charms_small'])}",
        f"L:{len(r['charms_large'])}",
        f"G:{len(r['charms_grand'])}"
    ])
    weapons_cell = join_span(r["weapons"])
    armors_cell = join_span(r["armors"])
    other_cell = join_span(r["other"])

    html_parts.append(f"<tr class='account-row' data-account='{html.escape(r['account'])}' style='background:{color}'>")
    html_parts.append(f"<td>{acct}</td>")
    html_parts.append(f"<td>{charname}</td>")
    html_parts.append(f"<td>{us_cell}</td>")
    html_parts.append(f"<td>{runes_cell}</td>")
    html_parts.append(f"<td>{rings_cell}</td>")
    html_parts.append(f"<td>{belts_cell}</td>")
    html_parts.append(f("<td>{}</td>").format(amulets_cell) if False else f"<td>{amulets_cell}</td>")  # keep structure; no eval
    html_parts.append(f"<td>{charms_cell}</td>")
    html_parts.append(f"<td>{weapons_cell}</td>")
    html_parts.append(f"<td>{armors_cell}</td>")
    html_parts.append(f"<td>{other_cell}</td>")
    html_parts.append("</tr>")

html_parts.append("</tbody></table>")

# JavaScript for filtering, sorting, expand/collapse and export
html_parts.append("""
<script>
const table = document.getElementById('itemsTable');
let sortCol = null;
let sortDir = 1;

function filterTable(){
    const q = document.getElementById('searchInput').value.toLowerCase();
    const rows = table.tBodies[0].rows;
    for(let r of rows){
        const text = r.innerText.toLowerCase();
        r.style.display = text.indexOf(q) === -1 ? 'none' : '';
    }
}

function toggleAccountRows(account){
    const rows = document.querySelectorAll(`tr[data-account='${account}']`);
    rows.forEach(r => {
        r.style.display = (r.style.display === 'none') ? '' : 'none';
    });
}

function expandAll(){
    const rows = table.tBodies[0].rows;
    for(let r of rows) r.style.display = '';
}
function collapseAll(){
    const rows = table.tBodies[0].rows;
    for(let r of rows) r.style.display = 'none';
}

// sorting
document.querySelectorAll('th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
        const col = th.getAttribute('data-col');
        sortTableBy(col);
    });
});

function sortTableBy(col){
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    rows.sort((a,b) => {
        const ai = a.querySelector(`td:nth-child(${getColIndex(col)})`).innerText.trim();
        const bi = b.querySelector(`td:nth-child(${getColIndex(col)})`).innerText.trim();
        if(ai < bi) return -1*sortDir;
        if(ai > bi) return 1*sortDir;
        return 0;
    });
    // toggle direction if same column
    if(sortCol === col) sortDir *= -1; else { sortDir = 1; sortCol = col; }
    // append in order
    for(let r of rows) tbody.appendChild(r);
}

function getColIndex(col){
    const map = {account:1, charname:2, unique_set:3, runes:4, rings:5, belts:6, amulets:7, charms:8, weapons:9, armors:10, other:11};
    return map[col];
}

// Exports
function exportJSON(){
    fetch('/items_export.json').then(r=>r.json()).then(data=>{
        const s = JSON.stringify(data, null, 2);
        downloadBlob(s, 'items_export.json', 'application/json');
    }).catch(e=>alert('Export failed: '+e));
}
function exportCSV(){
    fetch('/items_export.csv').then(r=>r.text()).then(text=>{
        downloadBlob(text, 'items_export.csv', 'text/csv');
    }).catch(e=>alert('Export failed: '+e));
}
function downloadBlob(content, filename, mime){
    const blob = new Blob([content], {type:mime});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}
</script>
""")

html_parts.append("</body></html>")

# write HTML
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html_parts))

print("Generated:", OUTPUT_HTML)
print("JSON exported:", OUTPUT_JSON)
print("CSV exported:", OUTPUT_CSV)
