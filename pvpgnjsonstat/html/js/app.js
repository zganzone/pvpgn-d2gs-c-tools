// js/app.js

const STATUS_JSON_URL = 'jsons/server_status.json'; 
const HISTORY_JSON_URL = 'jsons/game_history.json';

// Функция за зареждане на JSON данни
async function loadServerData() {
    try {
        const response = await fetch(STATUS_JSON_URL);
        if (!response.ok) {
            throw new Error(`Грешка при зареждане на JSON: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Неуспешно зареждане на сървърните данни:', error);
        document.getElementById('live-status').innerHTML = '<p class="error">Грешка при зареждане на данните. Проверете дали Python скриптът работи.</p>';
        return null;
    }
}

// Функция за форматиране на "карти" (за live status и total stats)
function createCard(title, value, colorClass = 'card-value') {
    return `
        <div class="card">
            <div class="card-title">${title}</div>
            <div class="${colorClass}">${value}</div>
        </div>
    `;
}

// Попълване на Актуалните Статуси (Live Status)
function populateLiveStatus(status) {
    const liveStatusDiv = document.getElementById('live-status');
    if (!status || Object.keys(status).length === 0) {
        liveStatusDiv.innerHTML = createCard('Статус', 'Няма данни', 'card-value');
        return;
    }

    let html = '';
    html += createCard('Онлайн Потребители', status.users || 0);
    html += createCard('Активни Игри', status.games || 0);
    html += createCard('Общо Акаунти', status.useraccounts || 'N/A', 'card-value');
    html += createCard('Версия', status.version || 'N/A', 'card-value');
    html += createCard('Uptime', status.uptime || 'N/A', 'card-value');
    
    liveStatusDiv.innerHTML = html;
}

// Попълване на Общата Сървърна Статистика (Total Stats)
function populateTotalStats(meta) {
    const totalStatsDiv = document.getElementById('total-stats');
    if (!meta || Object.keys(meta).length === 0) {
        totalStatsDiv.innerHTML = '<p>Няма обща статистика (games.txt).</p>';
        return;
    }

    let html = '<h2>Обща Игрова Статистика</h2><div class="card-group">';
    html += createCard('Общ Брой Игри', meta.totalgames || 0);
    html += createCard('Общ Брой Логвания', meta.logins || 0);
    html += createCard('Локация', meta.location || 'N/A', 'card-value');
    html += createCard('Контакт', `${meta.contactname || 'N/A'} (${meta.contactemail || 'N/A'})`, 'card-value');
    html += createCard('URL', `<a href="${meta.url || '#'}">${meta.url || 'N/A'}</a>`, 'card-value');
    html += '</div>';

    totalStatsDiv.innerHTML = html;
}

// Попълване на Таблицата с Активни Игри
function populateActiveGames(games) {
    const tableBody = document.getElementById('active-games-table').querySelector('tbody');
    document.getElementById('active-games-count').textContent = games.length;
    tableBody.innerHTML = ''; // Изчистване
    
    if (games.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3">Няма активни игри в момента.</td></tr>';
        return;
    }

    games.forEach(game => {
        const row = tableBody.insertRow();
        row.insertCell().textContent = game.platform_name;
        row.insertCell().textContent = game.name;
        row.insertCell().textContent = game.players;
    });
}

// Попълване на Таблицата с Логнати Потребители
function populateActiveUsers(users) {
    const tableBody = document.getElementById('active-users-table').querySelector('tbody');
    document.getElementById('active-users-count').textContent = users.length;
    tableBody.innerHTML = ''; // Изчистване

    if (users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4">Няма логнати потребители в момента.</td></tr>';
        return;
    }

    users.forEach(user => {
        const row = tableBody.insertRow();
        row.insertCell().textContent = user.username;
        row.insertCell().textContent = user.platform_name;
        row.insertCell().textContent = user.region;
        row.insertCell().textContent = user.version;
    });
}

// Главна функция за изпълнение
async function initDashboard() {
    const data = await loadServerData();

    if (data) {
        // Обновяване на всички секции
        populateLiveStatus(data.active_status);
        populateTotalStats(data.total_stats);
        populateActiveGames(data.active_games);
        populateActiveUsers(data.active_users);

        // Обновяване на времето на генериране
        document.getElementById('generated-time').textContent = data.generated_at;
    }
    
    // Презареждане на всеки 30 секунди (за актуалност)
    setTimeout(initDashboard, 30000); 
}

// Стартиране
initDashboard();
