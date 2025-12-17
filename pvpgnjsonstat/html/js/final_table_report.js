// =======================================================
// /js/final_table_report.js - УЛТРА-ОПРОСТЕН ТАБЛИЧЕН ПРЕГЛЕД (ЗА Ctrl+F)
// =======================================================

const ALL_ITEMS_JSON_URL = '/data/all_items.json';

// --- helpers (Общи) ---

function escapeHTML(str) {
    let s = String(str || ''); 
    if (!s) return ''; 
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#39;');
}

async function fetchJSON(path){
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.json();
}

const extractName = (item) => {
    return (typeof item === 'object' && item !== null && item.name) ? item.name : item;
};

// =======================================================
// --- ФУНКЦИЯ ЗА ГЕНЕРИРАНЕ НА КЛЕТКА (ИМЕ + АТРИБУТИ) ---
// =======================================================

function formatItemsForCell(items) {
    if (!items || items.length === 0) return '—';
    
    // Връща един голям стринг с всички предмети и техните атрибути
    return items.map(item => {
        const name = extractName(item);
        if (!name) return '';

        let html = `<div class="item-entry"><h4>${escapeHTML(name)}</h4>`;
        
        let properties = null;
        if (typeof item === 'object' && item !== null) {
            properties = item.properties; 
        }

        if (properties && Array.isArray(properties) && properties.length > 0) {
            html += '<ul class="item-properties-list">';
            properties.forEach(prop => {
                // Добавяме тире и интервал, за да улесним четенето и Ctrl+F
                html += `<li>- ${escapeHTML(prop)}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        return html;
    }).join(''); 
}


// --- Основна функция за генериране на таблицата ---

async function loadTableReport() {
    const container = document.getElementById('item-report-container');
    const data = await fetchJSON(ALL_ITEMS_JSON_URL);

    if (!data || !data.rows) {
        container.innerHTML = `<p style="color:red;">Error: Could not load data from <code>${ALL_ITEMS_JSON_URL}</code>.</p>`;
        return;
    }

    const rows = data.rows;
    const updateTime = new Date(data.generated).toLocaleString();
    
    document.getElementById('last-updated').textContent = updateTime;
    document.getElementById('total-chars').textContent = rows.length;

    if (rows.length === 0) {
        container.innerHTML = '<p>No characters found in the Item Report.</p>';
        return;
    }

    let html = `
        <table class="report-table" id="item-report-table">
            <thead>
                <tr>
                    <th>Char Name</th>
                    <th>Account</th>
                    <th>Lvl</th>
                    <th>Class</th>
                    <th>Unique/Set Items</th>
                    <th>Runes</th>
                    <th>Charms</th>
                    <th>Rings/Amulets/Belts</th>
                </tr>
            </thead>
            <tbody>
    `;

    rows.forEach(char => {
        const charName = escapeHTML(char.charname || '-');
        const account = escapeHTML(char.account || '-');
        const level = char.level || 'N/A';
        const className = escapeHTML(char.class || '-');
        
        // Взимаме всички категории, включително останалите, които може да имат атрибути
        const uniqueSetItems = char.unique_set || [];
        const runesItems = char.runes || [];
        const charmsItems = char.charms || []; 
        
        // Добавяме и другите категории в една обща клетка за максимална плътност
        const otherGear = [
            ...(char.rings || []),
            ...(char.amulets || []),
            ...(char.belts || [])
        ];
        
        // Генериране на HTML
        const uniqueSetHTML = formatItemsForCell(uniqueSetItems);
        const runesHTML = formatItemsForCell(runesItems);
        const charmsHTML = formatItemsForCell(charmsItems);
        const otherGearHTML = formatItemsForCell(otherGear);


        html += `
            <tr>
                <td><a href="charinfo.html?name=${charName.toLowerCase()}" target="_blank">${charName}</a></td>
                <td>${account}</td>
                <td>${level}</td>
                <td>${className}</td>
                <td class="item-list-cell">${uniqueSetHTML}</td>
                <td class="item-list-cell">${runesHTML}</td>
                <td class="item-list-cell">${charmsHTML}</td>
                <td class="item-list-cell">${otherGearHTML}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    
    // Няма нужда от activateSearchFilter()
}


// --- Инициализация ---
document.addEventListener('DOMContentLoaded', loadTableReport);
