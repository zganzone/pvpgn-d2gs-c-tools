// =======================================================
// /js/attribute_report.js - НОВ АТРИБУТЕН ДОКЛАД
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
// --- ФУНКЦИЯ ЗА ГЕНЕРИРАНЕ НА БЛОК С ПРЕДМЕТИ ---
// =======================================================

function generateItemListHTML(items) {
    if (!items || items.length === 0) return '';
    
    return items.map(item => {
        const name = extractName(item);
        if (!name) return '';

        let html = `<li class="item-entry"><h4>${escapeHTML(name)}</h4>`;
        
        let properties = null;
        if (typeof item === 'object' && item !== null) {
            properties = item.properties; 
        }

        if (properties && Array.isArray(properties) && properties.length > 0) {
            html += '<ul class="item-properties-list">';
            properties.forEach(prop => {
                html += `<li>${escapeHTML(prop)}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</li>';
        return html;
    }).join(''); 
}


// --- Основна функция за генериране на доклада ---

async function loadAttributeReport() {
    const container = document.getElementById('report-list-container');
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
        container.innerHTML = '<p>No characters found.</p>';
        return;
    }

    let html = '';

    rows.forEach(char => {
        const charName = escapeHTML(char.charname || '-');
        const account = escapeHTML(char.account || '-');
        const level = char.level || 'N/A';
        const className = escapeHTML(char.class || '-');
        
        // Взимаме списъците от JSON.
        const uniqueSetItems = char.unique_set || [];
        const runesItems = char.runes || [];
        const charmsItems = char.charms || []; 
        
        // --- ЛОГИКА ЗА ТЪРСЕНЕ: ГЕНЕРИРАНЕ НА data-search АТРИБУТ ---
        
        let allProperties = [];
        let allItemNames = [];

        const extractSearchData = (items) => {
            items.forEach(item => {
                const name = extractName(item);
                if (name) {
                    allItemNames.push(name);
                }
                if (typeof item === 'object' && item !== null) {
                    const props = item.properties; 
                    if (props && Array.isArray(props)) {
                        allProperties.push(...props);
                    }
                }
            });
        };

        extractSearchData(uniqueSetItems);
        extractSearchData(runesItems);
        extractSearchData(charmsItems);
        
        // Събираме всички ключови думи за търсене
        const searchableContentArray = [
            charName, 
            account, 
            className,
            level.toString(),
            ...allItemNames,
            ...allProperties
        ];
        
        // Превръщаме всички елементи в малки букви в един стринг
        const searchableContent = searchableContentArray.join(' ').toLowerCase();

        
        // --- ГЕНЕРИРАНЕ НА HTML БЛОКА ---
        const uniqueSetHTML = generateItemListHTML(uniqueSetItems);
        const runesHTML = generateItemListHTML(runesItems);
        const charmsHTML = generateItemListHTML(charmsItems);
        
        html += `
            <div class="char-block" data-search="${searchableContent}">
                <div class="char-header">
                    <h3><a href="charinfo.html?name=${charName.toLowerCase()}" target="_blank">${charName}</a></h3>
                    <p>Lvl: ${level} | Class: ${className} | Account: ${account}</p>
                </div>
                <ul class="item-list">
                    ${uniqueSetHTML}
                    ${charmsHTML}
                    ${runesHTML}
                    </ul>
            </div>
        `;
    });

    container.innerHTML = html;
    
    activateSearchFilter();
}


// --- ФУНКЦИЯ ЗА ФИЛТРИРАНЕ (Работи с новия дизайн) ---

function activateSearchFilter() {
    const searchBar = document.getElementById('search-bar');
    if (!searchBar) return;

    searchBar.addEventListener('keyup', (e) => {
        const filter = e.target.value.toLowerCase();
        const blocks = document.querySelectorAll('.char-block');

        blocks.forEach(block => {
            const content = block.getAttribute('data-search');
            
            if (content && content.includes(filter)) {
                block.classList.add('char-block-visible');
            } else {
                block.classList.remove('char-block-visible');
            }
        });
        
        // Покажи всички блокове, когато филтърът е празен
        if (filter === "") {
             blocks.forEach(block => block.classList.add('char-block-visible'));
        }
    });
    
    // Показване на всички блокове при първо зареждане
    document.querySelectorAll('.char-block').forEach(block => block.classList.add('char-block-visible'));
}


// --- Инициализация ---
document.addEventListener('DOMContentLoaded', loadAttributeReport);
