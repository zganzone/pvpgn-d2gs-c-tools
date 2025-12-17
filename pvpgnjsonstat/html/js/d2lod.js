// js/d2lod.js

const D2_GAMES_JSON_URL = 'jsons/all_games_d2.json';
const UPTIME_JSON_URL = 'jsons/d2gs_uptime_data.json';
const STATUS_JSON_URL = 'jsons/d2gs_status_data.json';


// --- Helper Functions ---

// Нова функция за конвертиране на големи секунди в четим формат (години, дни, часове)
function formatLargeSeconds(totalSeconds) {
    if (!totalSeconds || isNaN(totalSeconds) || totalSeconds <= 0) {
        return "Unlimited / N/A";
    }

    totalSeconds = Number(totalSeconds);
    const years = Math.floor(totalSeconds / (3600 * 24 * 365));
    const days = Math.floor((totalSeconds % (3600 * 24 * 365)) / (3600 * 24));
    const hours = Math.floor((totalSeconds % (3600 * 24)) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);

    let parts = [];
    if (years > 0) parts.push(`${years}y`);
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0 && years === 0) parts.push(`${minutes}m`); // Показваме минути само ако няма години/дни

    return parts.length > 0 ? parts.join(' ') : 'Under 1 min';
}

function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PAL': 'Paladin', 'SOR': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ZGANSASIN': 'Assassin', 'SORSI SOR': 'Sorceress', 'ASS': 'Assassin' 
    };
    const cleanName = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[cleanName] || shortName; 
}

const COLOR_PALETTE = [
    '#607d8b', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', 
    '#ff9800', '#ff5722', '#e64a19', '#b71c1c',
];

// Универсална функция за зареждане на JSON
async function loadJson(url) {
    try {
        const response = await fetch(url + '?_=' + Date.now()); 
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error(`Неуспешно зареждане на данни от ${url}:`, error);
        return null;
    }
}

// --- D2GS Статистики ---

async function populateD2GSStats() {
    const [uptimeData, statusData] = await Promise.all([
        loadJson(UPTIME_JSON_URL),
        loadJson(STATUS_JSON_URL)
    ]);
    
    // Uptime и Време
    const uptimeValue = (uptimeData && uptimeData.uptime_duration_value) || 'N/A';
    document.getElementById('d2gs-uptime-value').textContent = uptimeValue;
    
    const lastUpdated = (uptimeData && uptimeData.current_time) ? new Date(uptimeData.current_time).toLocaleString() : new Date().toLocaleString();
    document.getElementById('last-updated').textContent = lastUpdated;
    document.getElementById('last-updated-footer').textContent = lastUpdated;

    // Status
    if (statusData) {
        // Основни метрики
        document.getElementById('d2gs-running-games').textContent = statusData.current_activity.running_games || 0;
        document.getElementById('d2gs-users-in-game').textContent = statusData.current_activity.users_in_game || 0;
        document.getElementById('d2gs-max-games').textContent = statusData.game_limits.max_games_set || 'N/A';
        document.getElementById('d2gs-max-prefer-users').textContent = statusData.game_limits.max_prefer_users || 'N/A';
        
        // Лимит на живота на играта (Max Game Life)
        const gameLifeSeconds = statusData.game_limits.max_game_life_seconds;
        document.getElementById('d2gs-max-game-life').textContent = formatLargeSeconds(gameLifeSeconds);
        
        // Връзки
        const d2csStatus = statusData.service_connections.d2cs.includes('connected') ? 'CONNECTED' : 'DISCONNECTED';
        const d2dbsStatus = statusData.service_connections.d2dbs.includes('connected') ? 'CONNECTED' : 'DISCONNECTED';
        document.getElementById('d2gs-d2cs').textContent = d2csStatus;
        document.getElementById('d2gs-d2dbs').textContent = d2dbsStatus;
        
        // Ресурси (Нови полета)
        const physUsed = (statusData.resource_usage.physical_memory.used_mb || 0.0).toFixed(2);
        const physTotal = (statusData.resource_usage.physical_memory.total_mb || 0.0).toFixed(2);
        const virtUsed = (statusData.resource_usage.virtual_memory.used_mb || 0.0).toFixed(2);
        const virtTotal = (statusData.resource_usage.virtual_memory.total_mb || 0.0).toFixed(2);
        const kernelCPU = (statusData.resource_usage.kernel_cpu_percent || 0.0).toFixed(2);
        const userCPU = (statusData.resource_usage.user_cpu_percent || 0.0).toFixed(2);

        document.getElementById('d2gs-phys-memory').textContent = `${physUsed} MB / ${physTotal} MB`;
        document.getElementById('d2gs-virt-memory').textContent = `${virtUsed} MB / ${virtTotal} MB`;
        document.getElementById('d2gs-kernel-cpu').textContent = `${kernelCPU} %`;
        document.getElementById('d2gs-user-cpu').textContent = `${userCPU} %`;

    } else {
        // Ако няма статус данни
        const ids = [
            'd2gs-running-games', 'd2gs-users-in-game', 'd2gs-max-games', 
            'd2gs-max-prefer-users', 'd2gs-max-game-life', 'd2gs-d2cs', 'd2gs-d2dbs',
            'd2gs-phys-memory', 'd2gs-virt-memory', 'd2gs-kernel-cpu', 'd2gs-user-cpu'
        ];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = 'N/A';
        });
    }
}


// --- Main Game Rendering Logic (Без промяна) ---
async function loadD2Games() {
    try {
        const resp = await fetch(D2_GAMES_JSON_URL + '?_=' + Date.now());
        if (!resp.ok) {
            throw new Error(`Неуспешно зареждане на D2 игри: ${resp.status}`);
        }
        const games = await resp.json();
        const container = document.getElementById('d2-games-container');
        container.innerHTML = ''; 

        if (games.length === 0) {
            container.innerHTML = '<p class="no-games-message">В момента няма активни Diablo II игри.</p>';
            return;
        }

        games.forEach(game => {
          const info = game.GameInfo;
          const userCount = info.UserCount; 
          const maxPlayers = 8;
          
          const xpRate = info.XPRateMultiplier || 1.0; 
          const xpBonus = info.XPBonusPercent || '+0%';
          
          const barWidth = (userCount / maxPlayers) * 100; 
          const hexColor = COLOR_PALETTE[userCount] || COLOR_PALETTE[0]; 
          const dynamicColorStyle = `background-color: ${hexColor};`;
          
          const div = document.createElement('div');
          let diff = info.Difficult.toLowerCase();
          if(diff != 'normal' && diff != 'nightmare' && diff != 'hell') diff = 'normal';
          div.className = 'game-card ' + diff;
          
          
          let htmlContent = `<div class="game-title">${info.GameName} (${info.Difficult}) - ${userCount}/${maxPlayers} player(s)</div>`;

          htmlContent += `
              <div class="xp-container">
                  <div class="xp-bar-wrapper">
                      <div class="xp-bar" style="width: ${barWidth}%; ${dynamicColorStyle}"></div>
                  </div>
                  <div class="xp-text">
                      <span>XP Potential: ${userCount}/${maxPlayers}</span>
                      <span class="xp-multiplier">${xpRate}x (${xpBonus})</span>
                  </div>
              </div>
          `;

          if(game.Characters && game.Characters.length>0){
            let table = `<table class="players-table"><tr><th>Name</th><th>Class</th><th>Level</th><th>EnterTime</th></tr>`;
            game.Characters.forEach(ch => {
                const className = translateClass(ch.Class); 
                table += `<tr>
                  <td><a href="charinfo.html?name=${ch.CharName.toLowerCase()}" target="_blank">${ch.CharName}</a></td> 
                  <td>${className}</td> 
                  <td>${ch.Level}</td>
                  <td>${ch.EnterTime}</td>
                </tr>`;
            });
            table += '</table>';
            htmlContent += table;
          }
          
          div.innerHTML = htmlContent;
          container.appendChild(div);
        });
        
    } catch(error) {
        console.error("Грешка при зареждане на D2 игри:", error);
        document.getElementById('d2-games-container').innerHTML = `<p class="error-message">Не мога да заредя активните D2 игри.</p>`;
    }
}


// --- Инициализация ---
populateD2GSStats();
loadD2Games();

// Автоматично обновяване на всеки 60 секунди
setInterval(() => {
    populateD2GSStats();
    loadD2Games();
}, 60000);
