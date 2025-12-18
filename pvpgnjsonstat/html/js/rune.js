/**
 * D2 Rune Inventory Viewer - app.js
 * Логика за зареждане на JSON, изграждане на таблица и филтриране.
 */

const JSON_FILE_PATH = 'jsons/rune_inventory.json';
const tableBody = document.querySelector('#runeTable tbody');
const searchInput = document.getElementById('runeSearch');
const loadingMessage = document.getElementById('loadingMessage');
let runeData = []; // Глобална променлива за съхранение на данните

/**
 * 1. Зарежда JSON файла с инвентара на руните.
 */
async function loadRuneData() {
    try {
        const response = await fetch(JSON_FILE_PATH);
        if (!response.ok) {
            throw new Error(`HTTP грешка! Статус: ${response.status}`);
        }
        runeData = await response.json();
        
        loadingMessage.style.display = 'none'; // Скриване на съобщението за зареждане
        buildTable(runeData); // Изграждане на таблицата с всички данни
        searchInput.addEventListener('input', filterTable); // Активиране на търсачката

    } catch (error) {
        console.error("Грешка при зареждане на JSON:", error);
        loadingMessage.textContent = `ГРЕШКА: Неуспешно зареждане на данни. Проверете пътя: ${JSON_FILE_PATH}`;
        loadingMessage.style.color = '#FF4500';
    }
}

/**
 * 2. Изгражда HTML таблицата от масива с данни.
 * @param {Array} data - Масив с обекти, съдържащи информация за руните.
 */
function buildTable(data) {
    tableBody.innerHTML = ''; // Изчистване на старото съдържание
    
    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="rune-stats">Няма намерени руни, отговарящи на критериите.</td></tr>';
        return;
    }
    
    data.forEach(rune => {
        const row = tableBody.insertRow();
        
        // --- Колона 1: Руна ---
        const cellRuneName = row.insertCell();
        cellRuneName.textContent = rune.name;
        cellRuneName.classList.add('rune-name');
        
        // --- Колона 2: Общ Брой ---
        const cellTotalCount = row.insertCell();
        cellTotalCount.textContent = rune.total_count;
        cellTotalCount.classList.add('rune-count');

        // --- Колона 3: Бонуси ---
        const cellStats = row.insertCell();
        cellStats.textContent = rune.stats;
        cellStats.classList.add('rune-stats');

        // --- Колона 4: Притежавана от ---
        const charHolders = row.insertCell();
        charHolders.classList.add('char-list');
        
        // Генериране на списък с притежателите
        let holdersHTML = '';
        // Сортираме по брой в низходящ ред
        const sortedHolders = Object.entries(rune.holders).sort(([, countA], [, countB]) => countB - countA);

        sortedHolders.forEach(([charName, count]) => {
            holdersHTML += `<span class="char-name">${charName}</span>: <span class="char-count">${count}x</span><br>`;
        });
        charHolders.innerHTML = holdersHTML;
    });
}

/**
 * 3. Филтрира таблицата въз основа на въведения текст.
 */
function filterTable() {
    const filterText = searchInput.value.toLowerCase().trim();
    
    if (!filterText) {
        buildTable(runeData); // Показване на всички данни, ако търсачката е празна
        return;
    }
    
    // Филтриране на оригиналните данни
    const filteredData = runeData.filter(rune => {
        
        // 1. Търсене по име на руна
        if (rune.name.toLowerCase().includes(filterText)) {
            return true;
        }
        
        // 2. Търсене по име на герой, който я притежава
        // Трябва да търсим в ключовете (имената на героите) на holders обекта
        const charMatches = Object.keys(rune.holders).some(charName => 
            charName.toLowerCase().includes(filterText)
        );
        if (charMatches) {
            return true;
        }
        
        return false;
    });
    
    buildTable(filteredData);
}

// Стартиране на приложението
loadRuneData();
