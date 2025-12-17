// --- helper ---
function secondsToDhms(seconds) {
  seconds = Number(seconds);
  const d = Math.floor(seconds / (3600*24));
  const h = Math.floor((seconds % (3600*24))/3600);
  const m = Math.floor((seconds % 3600)/60);
  const s = Math.floor(seconds % 60);
  let str = '';
  if(d>0) str += d+'d ';
  if(h>0) str += h+'h ';
  if(m>0) str += m+'m ';
  str += s+'s';
  return str;
}

// --- fetch text helper (помага за server_uptime.txt и d2gs_uptime.txt) ---
async function fetchText(path) {
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.text();
}

// --- Class Translation Helper ---
function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PAL': 'Paladin', 'SOR': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ZGANSASIN': 'Assassin', 'SORSI SOR': 'Sorceress', 'ASS': 'Assassin' 
    };
    const cleanName = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[cleanName] || shortName; 
}


// --- load server info (зарежда uptime) ---
async function loadServerUptime() {
    // 1. Server Uptime (КОРИГИРАН ПЪТ: data/server_uptime.txt)
    try {
        const serverTxt = await fetchText('data/server_uptime.txt');
        const sec = parseInt(serverTxt.trim()) || 0;
        document.getElementById('server-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('server-uptime').textContent = 'N/A';
    }
    
    // 2. PvPGN Uptime (Пътят data/games.txt вече беше коректен)
    try {
        const resp = await fetch('data/games.txt'); 
        const text = await resp.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "text/xml");
        const pvpgn_uptime_sec = parseInt(xml.querySelector('server > uptime').textContent);
        document.getElementById('pvpgn-uptime').textContent = secondsToDhms(pvpgn_uptime_sec);
    } catch(e) {
        console.error("Error loading PvPGN Uptime:", e);
        document.getElementById('pvpgn-uptime').textContent = 'Error';
    }

    // 3. D2GS Uptime (КОРИГИРАН ПЪТ: data/d2gs_uptime.txt)
    try {
        const d2gsTxt = await fetchText('data/d2gs_uptime.txt');
        const sec = parseInt(d2gsTxt.trim()) || 0;
        document.getElementById('d2gs-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('d2gs-uptime').textContent = 'N/A';
    }
}

loadServerUptime(); 


// --- load games info (Пътят data/all_games.json вече е коректен) ---
fetch('data/all_games.json')
  .then(resp => resp.json())
  .then(games => {
    const container = document.getElementById('games-container');
    const now = new Date().toLocaleString();
    document.getElementById('last-updated').textContent = now;
// --- ПАЛИТРА ОТ 8 СТЪПКИ (От 1 до 8 Играча) ---
// Използваме HEX цветове, които преминават от зелено (1) към червено (8).
const COLOR_PALETTE = [
    '#607d8b', // 0: Резервен цвят (Сиво-синьо) - Никога не се използва
    '#8bc34a', // 1/8: Светло Зелено (Low XP)
    '#cddc39', // 2/8: Медиум Зелено
    '#ffeb3b', // 3/8: Жълто
    '#ffc107', // 4/8: Жълто-Оранжево (Среда)
    '#ff9800', // 5/8: Оранжево
    '#ff5722', // 6/8: Червено-Оранжево
    '#e64a19', // 7/8: Червено
    '#b71c1c', // 8/8: Тъмно Червено (MAX XP)
];

// --- load games info (Пътят data/all_games.json вече е коректен) ---
fetch('data/all_games.json')
  .then(resp => resp.json())
  .then(games => {
    const container = document.getElementById('games-container');
    const now = new Date().toLocaleString();
    document.getElementById('last-updated').textContent = now;

    // Изчистване на контейнера преди рендиране, за да се избегне дублиране при обновяване
    container.innerHTML = ''; 

    games.forEach(game => {
      const info = game.GameInfo;
      const userCount = info.UserCount; // int (1 до 8)
      const maxPlayers = 8;
      
      // Изчисляване на XP Rate параметри
      // Тези полета идват от Python скрипта 05.gameinfo2json.py
      const xpRate = info.XPRateMultiplier || 1.0; 
      const xpBonus = info.XPBonusPercent || '+0%';
      
      // 1. Изчисляване на Ширина на XP Bar
      const barWidth = (userCount / maxPlayers) * 100; 
      
      // 2. ИЗБОР НА ФИКСИРАН ЦВЯТ ОТ ПАЛИТРАТА
      // userCount се използва като индекс (1 до 8)
      // Ако userCount е извън граници (0 или >8), се използва резервният цвят (индекс 0)
      const hexColor = COLOR_PALETTE[userCount] || COLOR_PALETTE[0]; 
      
      // Прилагаме динамичния стил с фиксирания HEX цвят
      const dynamicColorStyle = `background-color: ${hexColor};`;
      
      
      const div = document.createElement('div');
      let diff = info.Difficult.toLowerCase();
      if(diff != 'normal' && diff != 'nightmare' && diff != 'hell') diff = 'normal';
      div.className = 'game-card ' + diff;
      
      
      // --- ГЕНЕРИРАНЕ НА HTML С НОВИЯ XP BAR ---
      
      // 1. Заглавие на играта
      let htmlContent = `<div class="game-title">${info.GameName} (${info.Difficult}) - ${userCount}/${maxPlayers} player(s)</div>`;

      // 2. Добавяне на XP Bar (с динамичните стилове)
      htmlContent += `
          <div class="xp-container">
              <div class="xp-bar-wrapper">
                  <div class="xp-bar xp-bar-fixed" style="width: ${barWidth}%; ${dynamicColorStyle}"></div>
              </div>
              <div class="xp-text">
                  <span>XP Potential: ${userCount}/${maxPlayers}</span>
                  <span class="xp-multiplier">${xpRate}x (${xpBonus})</span>
              </div>
          </div>
      `;
      // Край на XP Bar

      // 3. Таблица с героите
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
  });


  });
