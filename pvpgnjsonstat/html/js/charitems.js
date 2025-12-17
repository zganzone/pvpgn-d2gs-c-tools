// =======================================================
// /js/charitems.js - ФИНАЛЕН КОД (ПОКАЗВА И ТЪРСИ АТРИБУТИ)
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
    // Добавяме параметър за кеш бюст, за да сме сигурни, че четем новия файл
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.json();
}

// Хелпер за извличане на името
const extractName = (item) => {
    // Взимаме 'name' от обекта, или самия item, ако е просто низ
    return (typeof item === 'object' && item !== null && item.name) ? item.name : item;
};

// =======================================================
// --- ФУНКЦИЯ ЗА ГЕНЕРИРАНЕ НА КЛЕТКА (ИМЕ + АТРИБУТИ) ---
// Тази функция отговаря за визуализацията на атрибутите
// =======================================================

function formatItemsForCell(items) {
    if (!items || items.length === 0) return '—';
    
    return items.map(item => {
        const name = extractName(item);
        if (!name) return '';

        let html = `<div class="item-cell-content"><h4>${escapeHTML(name)}</h4>`;
        
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
        
        html += '</div>';
        return html;
    }).join(''); 
}


// --- Основна функция за генериране на таблицата ---

async function loadItemReport() {
    const container = document.getElementById('item-report-container');
    const data = await fetchJSON(ALL_ITEMS_JSON_URL);

    if (!data || !data.rows) {
        container.innerHTML = `<p style="color:red;">Error: Could not load data from <code>${ALL_ITEMS_JSON_URL}</code>. Check the path and file generation.</p>`;
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
                </tr>
            </thead>
            <tbody>
    `;

    rows.forEach(char => {
        const charName = escapeHTML(char.charname || '-');
        const account = escapeHTML(char.account || '-');
        const level = char.level || 'N/A';
        const className = escapeHTML(char.class || '-');
        
        // Взимаме списъците от JSON.
        const uniqueSetItems = char.unique_set || [];
        const runesItems = char.runes || [];
        const charmsItems = char.charms || []; 
        
        // Генериране на HTML за ВИЗУАЛИЗАЦИЯ
        const uniqueSetHTML = formatItemsForCell(uniqueSetItems);
        const runesHTML = formatItemsForCell(runesItems);
        const charmsHTML = formatItemsForCell(charmsItems);
        
        
        // =======================================================
        // *** ЛОГИКА ЗА ТЪРСЕНЕ: ГЕНЕРИРАНЕ НА data-search АТРИБУТ ***
        // =======================================================
        
        let allProperties = [];
        let allItemNames = [];

        // Хелпер за извличане на имена и атрибути от даден списък
        const extractSearchData = (items) => {
            items.forEach(item => {
                const name = extractName(item);
                if (name) {
                    allItemNames.push(name);
                }
                
                // Проверяваме дали item е обект с properties (атрибути)
                if (typeof item === 'object' && item !== null) {
                    const props = item.properties; 
                    if (props && Array.isArray(props)) {
                        allProperties.push(...props); // Добавяме всички свойства като низове
                    }
                }
            });
        };

        // Извличаме данни от всички категории предмети за търсене
        extractSearchData(uniqueSetItems);
        extractSearchData(runesItems);
        extractSearchData(charmsItems);

        // Създаваме пълния стринг за търсене
        const searchableContentArray = [
            charName, 
            account, 
            className,
            ...allItemNames,
            ...allProperties // Всички атрибути
        ];
        
        // Превръщаме всички елементи в малки букви в един стринг
        const searchableContent = searchableContentArray.join(' ').toLowerCase();


        html += `
            <tr data-search="${searchableContent}">
                <td><a href="charinfo.html?name=${charName.toLowerCase()}" target="_blank">${charName}</a></td>
                <td>${account}</td>
                <td>${level}</td>
                <td>${className}</td>
                <td class="item-list-cell">${uniqueSetHTML}</td>
                <td class="item-list-cell">${runesHTML}</td>
                <td class="item-list-cell">${charmsHTML}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    
    activateSearchFilter();
}


// --- ФУНКЦИЯ ЗА ФИЛТРИРАНЕ НА ТАБЛИЦАТА ---

function activateSearchFilter() {
    const searchBar = document.getElementById('search-bar');
    if (!searchBar) return;

    searchBar.addEventListener('keyup', (e) => {
        const filter = e.target.value.toLowerCase(); // Търсене в малки букви
        const table = document.getElementById('item-report-table');
        
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const content = row.getAttribute('data-search'); // Взима съдържанието за търсене
            
            // Ако скритият data-search атрибут съдържа филтъра, показваме реда
            if (content && content.includes(filter)) {
                row.style.display = ''; 
            } else {
                row.style.display = 'none'; 
            }
        });
    });
}


// --- Инициализация ---
document.addEventListener('DOMContentLoaded', loadItemReport);
