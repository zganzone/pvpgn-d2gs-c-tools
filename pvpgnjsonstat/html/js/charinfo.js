// =======================================================
// /js/charinfo.js - ГЛАВЕН СКРИПТ ЗА ВИЗУАЛИЗАЦИЯ НА ГЕРОЙ
// =======================================================

// --- constants ---
// Логът Ви предполага, че е директно в data/, а не в data/chars/
const DATA_DIR = 'jsons/chars/'; 


// --- helpers (Общи) ---

function numericOrDash(v){ 
    if(v===null||v===undefined||v==='') return '-'; 
    return v; 
}

// Helper за Escape на HTML символи
// *** КОРИГИРАНА ВЕРСИЯ ЗА ХЕНДЛИНГ НА ЧИСЛА ***
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
    // Добавяме параметър за избягване на кеширане
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.json();
}

// =======================================================
// --- Item Rendering Helpers (за декодирани атрибути) ---
// =======================================================

function formatItemProperty(prop) {
    if (!prop) return '';
    // Опростена логика за оцветяване. Може да се разшири.
    let color = 'color: #fff;'; 
    
    if (prop.includes('Faster Cast Rate') || prop.includes('Faster Run/Walk') || prop.includes('Faster Hit Recovery')) {
        color = 'color: #00ccff;'; // Синьо за FCR/FHR
    } else if (prop.includes('Resist') || prop.includes('Defense') || prop.includes('Life') || prop.includes('Mana')) {
        color = 'color: #00ff00;'; // Зелено за защита
    } else if (prop.includes('Damage') || prop.includes('Skill Levels') || prop.includes('Attack Rating') || prop.includes('Find Item')) {
        color = 'color: #ffff00;'; // Жълто за атака/умения
    } else if (prop.includes('Magic Items')) {
        color = 'color: #ff9900;'; // Оранжево за MF
    }
    
    return `<li style="${color}">${escapeHTML(prop)}</li>`;
}

function renderCategorizedItems(itemLists) {
    // Филтрираме и подреждаме категориите за по-добър вид
    const categories = [
        'unique_set', 'runes', 'amulets', 'rings', 'belts', 
        'charms_grand', 'charms_large', 'charms_small',
        'weapons', 'armors', 'other'
    ];

    let html = '';
    
    const translationMap = {
        'unique_set': 'Уникални / Сетове',
        'runes': 'Руни',
        'rings': 'Пръстени',
        'belts': 'Колани',
        'amulets': 'Амулети',
        'charms_small': 'Малки талисмани (Small)',
        'charms_large': 'Големи талисмани (Large)',
        'charms_grand': 'Огромни талисмани (Grand)',
        'weapons': 'Оръжия',
        'armors': 'Брони (Вкл. Щитове/Каски)',
        'other': 'Други предмети'
    };


    categories.forEach(category => {
        const items = itemLists[category];
        if (!items || items.length === 0) return;
        
        const title = translationMap[category] || category.replace(/_/g, ' ');

        // Започваме нова details-card за всяка категория
        html += `<div class="details-card"><h3>${title} (${items.length})</h3><ul class="item-list">`;
        
        items.forEach(item => {
            const itemName = item.name || item; 
            // Item properties идват под ключа "properties" в JSON-а
            const itemProperties = item.properties || item.decoded_properties || []; 
            
            // Заглавие на предмета
            let itemHtml = `<li><span class="${item.type || ''} item-name">${escapeHTML(itemName)}</span>`;
            
            // Показване на свойствата
            if (itemProperties.length > 0) {
                itemHtml += `<ul class="properties-list">`;
                itemProperties.forEach(prop => {
                    itemHtml += formatItemProperty(prop);
                });
                itemHtml += `</ul>`;
            }
            itemHtml += `</li>`;
            html += itemHtml;
        });
        
        html += `</ul></div>`;
    });

    return html;
}


// =======================================================
// --- ГЛАВНА ФУНКЦИЯ ЗА ЗАРЕЖДАНЕ НА ДАННИТЕ ---
// =======================================================

async function loadCharacterData(charName) {
    const jsonPath = DATA_DIR + charName.toLowerCase() + '.json';
    
    // 1. Изтегляне на JSON
    const data = await fetchJSON(jsonPath);
    
    if (!data) {
        document.getElementById('char-name').textContent = `Error: Character '${charName}' data not found or failed to load.`;
        document.getElementById('char-summary').textContent = `Check file path: ${jsonPath}`;
        return;
    }

    // 2. Извличане на основните данни
    const charStats = data.char_stats || {};
    const charLevel = charStats.level || 'N/A';
    const charClass = charStats.class || 'N/A';
    
    // 3. Актуализиране на заглавието и резюмето
    document.getElementById('char-name').textContent = data.charname || charName;
    document.getElementById('char-summary').textContent = 
        `Account: ${data.account || 'N/A'} | Class: ${charClass} | Level: ${charLevel} | HC: ${charStats.is_hardcore ? 'Yes' : 'No'} | Ladder: ${charStats.is_ladder ? 'Yes' : 'No'}`;


    // 4. Генериране на ОСНОВНИ ДЕТАЙЛИ
    const formattedExp = new Intl.NumberFormat('en-US').format(charStats.experience || 0);
    const charDetails = document.getElementById('char-details');
    if (charDetails) {
        charDetails.innerHTML = `
            <div class="stat-item"><span>Account File</span><span>${escapeHTML(data.charfile || '-')}</span></div>
            <div class="stat-item"><span>Progression</span><span>${escapeHTML(charStats.progression || '-')}</span></div>
            <div class="stat-item"><span>Experience</span><span>${formattedExp}</span></div>
            <div class="stat-item"><span>Gold (On Hand)</span><span>${new Intl.NumberFormat('en-US').format(charStats.gold || 0)}</span></div>
            <div class="stat-item"><span>Gold (Stash)</span><span>${new Intl.NumberFormat('en-US').format(charStats.stashed_gold || 0)}</span></div>
        `;
    }

    // 5. Генериране на АТРИБУТИ
    const attributesDiv = document.getElementById('attributes');
    if (attributesDiv) {
        attributesDiv.innerHTML = `
            <div class="stat-item"><span>Strength</span><span>${numericOrDash(charStats.strength)}</span></div>
            <div class="stat-item"><span>Dexterity</span><span>${numericOrDash(charStats.dexterity)}</span></div>
            <div class="stat-item"><span>Vitality</span><span>${numericOrDash(charStats.vitality)}</span></div>
            <div class="stat-item"><span>Energy</span><span>${numericOrDash(charStats.energy)}</span></div>
            
            <div class="stat-item"><span>Life / Mana</span><span>${numericOrDash(Math.floor(charStats.current_hp))} / ${numericOrDash(Math.floor(charStats.current_mana))}</span></div>
            
            <div class="stat-item" style="color:#d0d0d0;"><span>Unused Stats</span><span>${numericOrDash(charStats.unused_stats)}</span></div>
            <div class="stat-item" style="color:#d0d0d0;"><span>Unused Skills</span><span>${numericOrDash(charStats.unused_skills)}</span></div>
        `;
    }


    // 6. ГЕНЕРИРАНЕ НА СПИСЪК С ПРЕДМЕТИ (Критичната част)
    const itemListsContainer = document.getElementById('categorized-items-list');
    if (itemListsContainer) {
        // Събираме всички категории предмети от data обекта
        const itemCategories = {
            unique_set: data.unique_set || [],
            runes: data.runes || [],
            rings: data.rings || [],
            belts: data.belts || [],
            amulets: data.amulets || [],
            charms_small: data.charms_small || [],
            charms_large: data.charms_large || [],
            charms_grand: data.charms_grand || [],
            weapons: data.weapons || [],
            armors: data.armors || [],
            other: data.other || []
        };
        itemListsContainer.innerHTML = renderCategorizedItems(itemCategories);
    }
    
    // 7. Инвентар (Grid) - Просто го попълваме с празни слотове
    const inventoryGrid = document.getElementById('inventory-grid');
    if (inventoryGrid) {
        // Генерира 40 празни слота (10x4)
        inventoryGrid.innerHTML = Array(40).fill(0).map((_,i)=>`<div class="slot"></div>`).join('');
    }
}


// =======================================================
// --- ИНИЦИАЛИЗАЦИЯ (ТРЯБВА ДА Е В КРАЯ НА charinfo.js) ---
// =======================================================
document.addEventListener('DOMContentLoaded', () => {
    // Извличане на името на героя от URL (напр. charinfo.html?name=sorsi)
    const urlParams = new URLSearchParams(window.location.search);
    const charName = urlParams.get('name');
    
    if (charName) {
        loadCharacterData(charName);
    } else {
        // Ако няма charName, търсим елемента и задаваме грешка
        const charNameElement = document.getElementById('char-name');
        if (charNameElement) {
             charNameElement.textContent = 'Error: No Character Name Specified';
        }
    }
});
