// js/scbw.js

const LADDER_JSON_URL = 'jsons/multi_ladder.json';
const HISTORY_JSON_URL = 'jsons/game_history.json';
const TARGET_PLATFORM_TAG = 'SEXP'; // StarCraft history
const TARGET_LADDER_TAG = 'SEXP_NML'; // StarCraft Normal Ladder (Slot 0)

// Универсална функция за зареждане на JSON
async function loadJson(url) {
    try {
        const response = await fetch(url + '?_=' + Date.now());
        if (!response.ok) {
            console.warn(`JSON файлът не беше намерен или е празен: ${url}`);
            // Връщаме празен обект/масив при грешка 404/500
            return url.includes('ladder') ? { platform_ladders: {} } : { game_history: [] };
        }
        return await response.json();
    } catch (error) {
        console.error(`Неуспешно зареждане на данни от ${url}:`, error);
        return url.includes('ladder') ? { platform_ladders: {} } : { game_history: [] };
    }
}

// Попълване на Ладър Таблицата
function populateLadder(ladderData) {
    const tableBody = document.getElementById('scbw-ladder-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    const scbwLadder = ladderData.platform_ladders[TARGET_LADDER_TAG] || [];

    if (scbwLadder.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="empty-data-message">Няма намерена активна статистика (W/L) за StarCraft.</td></tr>`;
        return;
    }

    scbwLadder.forEach((player, i) => {
        const row = tableBody.insertRow();
        const totalGames = player.wins + player.losses + player.draws;
        
        let wlRatio = "0.00";
        if (player.losses > 0) {
            wlRatio = (player.wins / player.losses).toFixed(2);
        } else if (player.wins > 0) {
            wlRatio = "∞";
        }
        
        let wldDisplay = `${player.wins} / ${player.losses}`;
        if (player.draws > 0) {
            wldDisplay += ` / ${player.draws}`;
        }

        row.insertCell().textContent = i + 1;
        row.insertCell().innerHTML = `<strong>${player.username}</strong>`;
        row.insertCell().textContent = player.rating || 'N/A';
        row.insertCell().textContent = wldDisplay;
        row.insertCell().textContent = totalGames;
        row.insertCell().textContent = wlRatio;
    });
}

// Попълване на История на Игрите
function populateHistory(historyData) {
    const tableBody = document.getElementById('scbw-history-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    const scbwHistory = (historyData.game_history || []).filter(game => game.platform_tag === TARGET_PLATFORM_TAG);
    
    if (scbwHistory.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="empty-data-message">Няма намерена история на игрите за StarCraft.</td></tr>`;
        return;
    }

    scbwHistory.forEach(game => {
        const row = tableBody.insertRow();
        const resultClass = game.result.toLowerCase();
        
        const unitsDisplay = `${game.units_killed || 'N/A'} / ${game.units_lost || 'N/A'}`;
        
        row.insertCell().textContent = `${game.name} (#${game.id})`;
        row.insertCell().innerHTML = `<span class="${resultClass}">${game.result}</span>`;
        row.insertCell().textContent = `${game.player_name} / ${game.race}`;
        row.insertCell().textContent = unitsDisplay;
        row.insertCell().textContent = `${game.duration_minutes || 'N/A'} мин`;
        row.insertCell().textContent = game.ended_time || 'N/A';
    });
}

// Главна функция за изпълнение
async function initSCBW() {
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

    // Обновяване на времето, като се използва информация и от двата файла
    const generatedTime = (ladderData && ladderData.generated_at) || (historyData && historyData.generated_at) || new Date().toLocaleString();
    document.getElementById('generated-time').textContent = generatedTime;
    document.getElementById('generated-time-footer').textContent = generatedTime;
    
    // Автоматично обновяване на всеки 30 секунди
    setTimeout(initSCBW, 30000); 
}

// Стартиране
initSCBW();
