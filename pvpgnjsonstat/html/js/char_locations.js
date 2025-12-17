// =======================================================
// /js/char_locations.js - Визуализация на локациите
// =======================================================

const LOCATIONS_JSON_URL = '/data/char_locations.json';

// --- helpers ---

async function fetchJSON(path){
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.json();
}

function escapeHTML(str) {
    let s = String(str || ''); 
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#39;');
}

// --- Основна функция за генериране на таблицата ---

async function loadLocationReport() {
    const container = document.getElementById('location-report-container');
    const data = await fetchJSON(LOCATIONS_JSON_URL);

    if (!data || !data.rows) {
        container.innerHTML = `<p style="color:red;">Error: Could not load data from <code>${LOCATIONS_JSON_URL}</code>.</p>`;
        return;
    }

    const rows = data.rows;
    const updateTime = new Date(data.generated * 1000).toLocaleString(); // Времето е в секунди
    
    document.getElementById('last-updated').textContent = updateTime;
    document.getElementById('total-chars').textContent = rows.length;

    if (rows.length === 0) {
        container.innerHTML = '<p>No character location data found.</p>';
        return;
    }

    let html = `
        <table class="location-table" id="location-table">
            <thead>
                <tr>
                    <th>Char Name</th>
                    <th>Current Location</th>
                    <th>Area ID</th>
                </tr>
            </thead>
            <tbody>
    `;

    rows.forEach(char => {
        const charName = escapeHTML(char.charname || '-');
        const location = escapeHTML(char.location || 'N/A');
        const areaId = char.area_id || 'N/A';
        
        // Визуален статус: Ако локацията е Lobby, да е жълта, ако е in-game (различна от 0), да е зелена
        const statusClass = (areaId > 1) ? 'status-online' : 'status-offline'; 

        html += `
            <tr data-search="${charName.toLowerCase()} ${location.toLowerCase()}">
                <td><a href="charinfo.html?name=${charName.toLowerCase()}" target="_blank">${charName}</a></td>
                <td class="${statusClass}">${location}</td>
                <td>${areaId}</td>
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

// --- ФУНКЦИЯ ЗА ФИЛТРИРАНЕ НА ТАБЛИЦАТА (От предишния ни работещ код) ---

function activateSearchFilter() {
    const searchBar = document.getElementById('search-bar');
    if (!searchBar) return;

    searchBar.addEventListener('keyup', (e) => {
        const filter = e.target.value.toLowerCase();
        const table = document.getElementById('location-table');
        
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const content = row.getAttribute('data-search');
            
            if (content && content.includes(filter)) {
                row.style.display = ''; 
            } else {
                row.style.display = 'none'; 
            }
        });
    });
}


// --- Инициализация ---
document.addEventListener('DOMContentLoaded', loadLocationReport);
