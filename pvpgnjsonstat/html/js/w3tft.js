// js/w3tft.js

const W3GS_UPTIME_JSON = 'jsons/w3gs_uptime_data.json'; // Предполагаем път
const W3GS_STATUS_JSON = 'jsons/w3gs_status_data.json'; // Предполагаем път

const LADDER_JSON_URL = 'jsons/multi_ladder.json';
const HISTORY_JSON_URL = 'jsons/game_history.json';

const TARGET_PLATFORM_TAG = 'W3XP'; // Warcraft III history (TFT)
const TARGET_LADDER_TAG = 'W3XP_NML'; // Warcraft III Normal Ladder

// Универсална функция за зареждане на JSON
async function loadJson(url) {
    try {
        const response = await fetch(url + '?_=' + Date.now());
        if (!response.ok) {
            return null; // Връщаме null при 404/500
        }
        return await response.json();
    } catch (error) {
        console.error(`Неуспешно зареждане на данни от ${url}:`, error);
        return null;
    }
}

// Попълване на W3GS Статуса
async function populateW3GSStats() {
    const [uptimeData, statusData] = await Promise.all([
        loadJson(W3GS_UPTIME_JSON),
        loadJson(W3GS_STATUS_JSON)
    ]);
    
    // Uptime и Време
    const uptimeValue = (uptimeData && uptimeData.uptime_duration_value) || 'N/A';
    document.getElementById('w3gs-uptime-value').textContent = uptimeValue;
    
    const generatedTime = (uptimeData && uptimeData.current_time) || new Date().toLocaleString();
    document.getElementById('generated-time').textContent = generatedTime;
    document.getElementById('generated-time-footer').textContent = generatedTime;

    // Status
    if (statusData) {
        document.getElementById('w3gs-running-games').textContent = statusData.current_activity.running_games || 0;
        document.getElementById('w3gs-users-in-game').textContent = statusData.current_activity.users_in_game || 0;
        
        // Връзки
        const w3csStatus = statusData.service_connections.w3cs.includes('connected') ? 'CONNECTED' : 'DISCONNECTED';
        const w3dbsStatus = statusData.service_connections.w3dbs.includes('connected') ? 'CONNECTED' : 'DISCONNECTED';
        document.getElementById('w3gs-w3cs').textContent = w3csStatus;
        document.getElementById('w3gs-w3dbs').textContent = w3dbsStatus;
    } else {
        ['w3gs-running-games', 'w3gs-users-in-game', 'w3gs-w3cs', 'w3gs-w3dbs'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = 'N/A';
        });
    }
}

// Попълване на Ладър Таблицата
function populateLadder(ladderData) {
    const tableBody = document.getElementById('w3tft-ladder-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    const w3tftLadder = (ladderData && ladderData.platform_ladders && ladderData.platform_ladders[TARGET_LADDER_TAG]) || [];

    if (w3tftLadder.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="empty-data-message">Няма намерена активна статистика (W/L) за Warcraft III.</td></tr>`;
        return;
    }

    w3tftLadder.forEach((player, i) => {
        const row = tableBody.insertRow();
        const totalGames = player.wins + player.losses;
        
        row.insertCell().textContent = i + 1;
        row.insertCell().innerHTML = `<strong>${player.username}</strong>`;
        row.insertCell().textContent = player.race || 'N/A';
        row.insertCell().textContent = player.rating || 'N/A';
        row.insertCell().textContent = `${player.wins} / ${player.losses}`;
        row.insertCell().textContent = totalGames;
    });
}

// Попълване на История на Игрите
function populateHistory(historyData) {
    const tableBody = document.getElementById('w3tft-history-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    const w3tftHistory = (historyData.game_history || []).filter(game => game.platform_tag === TARGET_PLATFORM_TAG);
    
    if (w3tftHistory.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-data-message">Няма намерена история на игрите за Warcraft III.</td></tr>`;
        return;
    }

    w3tftHistory.forEach(game => {
        const row = tableBody.insertRow();
        const resultClass = game.result.toLowerCase();
        
        row.insertCell().textContent = `${game.name} (#${game.id})`;
        row.insertCell().innerHTML = `<span class="${resultClass}">${game.result}</span>`;
        row.insertCell().textContent = `${game.player_name} / ${game.race}`;
        row.insertCell().textContent = `${game.duration_minutes || 'N/A'} мин`;
        row.insertCell().textContent = game.ended_time || 'N/A';
    });
}

// Главна функция за изпълнение
async function initW3TFT() {
    // 1. Зареждане на W3GS статус (за Uptime/Connections)
    await populateW3GSStats(); 

    // 2. Зареждане на Ладър и История
    const [ladderData, historyData] = await Promise.all([
        loadJson(LADDER_JSON_URL),
        loadJson(HISTORY_JSON_URL)
    ]);

    if (ladderData) {
        populateLadder(ladderData);
    }
    
    if (historyData) {
        populateHistory(historyData);
    }
    
    // Автоматично обновяване на всеки 30 секунди
    setTimeout(initW3TFT, 30000); 
}

// Стартиране
initW3TFT();
