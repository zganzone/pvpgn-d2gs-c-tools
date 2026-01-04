// script.js
// --- Пътища до вашите JSON файлове ---
const PVPGN_JSON_URL = '../../logs/pvpgn_server_status.json';
const D2GS_JSON_URL = '../../logs/d2gs_server_status.json';

// --- Helper Functions ---

function formatLargeSeconds(totalSeconds) {
    if (!totalSeconds || isNaN(totalSeconds) || totalSeconds <= 0) {
        return "N/A";
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
    if (minutes > 0 && years === 0) parts.push(`${minutes}m`); 

    return parts.length > 0 ? parts.join(' ') : 'Under 1 min';
}

function calculateXPMultiplier(players) {
    const N = Math.min(8, Math.max(1, players));
    const multiplier = (N + 1) / 2;
    const bonus = ((multiplier - 1) * 100).toFixed(0) + '%';
    return { multiplier: multiplier.toFixed(2), bonus: bonus, maxPlayers: 8 };
}

function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PALADIN': 'Paladin', 'SORCERESS': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ASS': 'Assassin', 'BAR': 'Barbarian',
        'Ama': 'Amazon', 'Sorceress': 'Sorceress', 'Bar': 'Barbarian', 
        'Paladin': 'Paladin'
    };
    const cleanName = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[cleanName] || shortName; 
}

const COLOR_PALETTE = [
    '#607d8b', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', 
    '#ff9800', '#ff5722', '#e64a19', '#b71c1c',
];

// --- Функции за попълване на данни ---

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Грешка при четене на файл ${url}:`, error);
        // Добавяне на визуална грешка
        document.getElementById('d2-games-container').innerHTML = `<p class="error-message">ГРЕШКА: Не може да зареди ${url}. Уверете се, че работите през уеб сървър.</p>`;
        return null;
    }
}


async function populatePvPGNStats() {
    const data = await fetchData(PVPGN_JSON_URL);
    
    if (!data) {
        document.getElementById('pvpgn-server-uptime').textContent = 'Грешка (OS)';
        return;
    }
    
    document.getElementById('last-updated').textContent = data.timestamp;
    document.getElementById('last-updated-footer').textContent = data.timestamp;

    document.getElementById('pvpgn-server-uptime').textContent = formatLargeSeconds(data.server.uptime_seconds) || 'N/A';
    document.getElementById('pvpgn-proc-uptime').textContent = formatLargeSeconds(data.pvpgn.uptime) || 'N/A';
    document.getElementById('pvpgn-users-online').textContent = data.pvpgn.users_online || 0;
    document.getElementById('pvpgn-games-online').textContent = data.pvpgn.games_online || 0;
    document.getElementById('pvpgn-load-average').textContent = `${data.server.load_average['1m']} / ${data.server.load_average['5m']} / ${data.server.load_average['15m']}`;
    document.getElementById('pvpgn-memory').textContent = `${data.server.used_mb} MB / ${data.server.total_mb} MB (Avail: ${data.server.available_mb} MB)`;
}


async function populateD2GSStats() {
    const statusData = await fetchData(D2GS_JSON_URL);

    if (!statusData) {
        document.getElementById('d2gs-uptime-value').textContent = 'Грешка (D2GS)';
        return;
    }

    document.getElementById('last-updated').textContent = statusData.timestamp;
    document.getElementById('last-updated-footer').textContent = statusData.timestamp;

    document.getElementById('d2gs-uptime-value').textContent = statusData.start_time || 'N/A';
    document.getElementById('d2gs-running-games').textContent = statusData.server_status.current_running_games;
    document.getElementById('d2gs-users-in-game').textContent = statusData.server_status.current_users;
    document.getElementById('d2gs-max-prefer-users').textContent = statusData.server_status.max_prefer_users;
    
    const d2csStatus = statusData.connections.D2CS.status.toUpperCase();
    const d2dbsStatus = statusData.connections.D2DBS.status.toUpperCase();
    document.getElementById('d2gs-d2cs').innerHTML = `<span class="status-${d2csStatus.toLowerCase()}">${d2csStatus}</span>`;
    document.getElementById('d2gs-d2dbs').innerHTML = `<span class="status-${d2dbsStatus.toLowerCase()}">${d2dbsStatus}</span>`;
    
    const kernelCPU = (statusData.server_status.kernel_cpu_percent || 0.0).toFixed(2);
    const userCPU = (statusData.server_status.user_cpu_percent || 0.0).toFixed(2);
    const physUsed = (statusData.server_status.physical_mem_used_mb || 0.0).toFixed(2);
    const physTotal = (statusData.server_status.physical_mem_total_mb || 0.0).toFixed(2);
    const virtUsed = (statusData.server_status.virtual_mem_used_mb || 0.0).toFixed(2);
    const virtTotal = (statusData.server_status.virtual_mem_total_mb || 0.0).toFixed(2);

    document.getElementById('d2gs-kernel-cpu').textContent = `${kernelCPU} %`;
    document.getElementById('d2gs-user-cpu').textContent = `${userCPU} %`;
    document.getElementById('d2gs-phys-memory').textContent = `${physUsed} MB / ${physTotal} MB`;
    document.getElementById('d2gs-virt-memory').textContent = `${virtUsed} MB / ${virtTotal} MB`;

    document.getElementById('d2gs-d2cs-peak-rate').textContent = `${(statusData.network.D2CS.peak_send_rate || 0).toFixed(3)} KB/s`;
    document.getElementById('d2gs-d2dbs-peak-rate').textContent = `${(statusData.network.D2DBS.peak_send_rate || 0).toFixed(3)} KB/s`;

    return statusData;
}


function loadD2Games(statusData) {
    const games = statusData.games;
    const charactersMap = statusData.characters;
    const container = document.getElementById('d2-games-container');
    container.innerHTML = ''; 

    if (!games || games.length === 0) {
        container.innerHTML = '<p class="no-games-message">В момента няма активни Diablo II игри.</p>';
        return;
    }

    games.forEach(game => {
      const gameId = game.game_id;
      const userCount = game.users;
      const maxPlayers = 8;
      
      const { multiplier, bonus: xpBonus } = calculateXPMultiplier(userCount);
      
      const barWidth = (userCount / maxPlayers) * 100; 
      const hexColor = COLOR_PALETTE[userCount] || COLOR_PALETTE[0]; 
      const dynamicColorStyle = `background: linear-gradient(90deg, #1f4f1f, ${hexColor});`;
      
      const div = document.createElement('div');
      let diff = (game.difficulty || 'normal').toLowerCase(); 
      if(diff !== 'normal' && diff !== 'nightmare' && diff !== 'hell') diff = 'normal';
      div.className = 'game-card ' + diff;
      
      
      let htmlContent = `<div class="game-title">${game.game_name} (${game.difficulty.toUpperCase()}) - ${userCount}/${maxPlayers} player(s)</div>`; 

      htmlContent += `
          <div class="xp-container">
              <div class="xp-bar-wrapper">
                  <div class="xp-bar" style="width: ${barWidth}%; ${dynamicColorStyle}"></div>
              </div>
              <div class="xp-text">
                  <span>XP Potential: Players ${userCount}</span>
                  <span class="xp-multiplier">XP Multiplier: +${xpBonus}</span>
              </div>
          </div>
      `;

      const characters = charactersMap[gameId.toString()] || [];
      if(characters.length > 0){
        let table = `<table class="players-table"><tr><th>Name</th><th>Class</th><th>Level</th><th>Enter Time</th></tr>`;
        characters.forEach(ch => {
            const className = translateClass(ch.class); 
            table += `<tr>
              <td>${ch.char_name}</td> 
              <td>${className}</td> 
              <td>${ch.level}</td> 
              <td>${ch.enter_time}</td> 
            </tr>`;
        });
        table += '</table>';
        htmlContent += table;
      }
      
      div.innerHTML = htmlContent;
      container.appendChild(div);
    });
    
}


// --- Инициализация ---
async function init() {
    await populatePvPGNStats();

    const d2gsData = await populateD2GSStats();
    if (d2gsData) {
        loadD2Games(d2gsData);
    }
}

document.addEventListener('DOMContentLoaded', init);

// Автоматично обновяване на всеки 60 секунди
setInterval(init, 60000);
