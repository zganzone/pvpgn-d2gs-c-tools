// --- helpers (Общи) ---

// Връщаме се към Promise-базиран fetch за по-голяма стабилност
function fetchXML(path){
    return fetch(path + '?_=' + Date.now())
        .then(r => {
            if (!r.ok) {
                // Хващане на HTTP грешки
                console.error(`HTTP Error: ${r.status} when fetching ${path}`);
                return Promise.reject(new Error(`Failed to fetch XML: ${r.status}`));
            }
            return r.text();
        })
        .then(text => {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(text, 'application/xml');

            // Проверка за грешки при XML парсване
            if (xmlDoc.getElementsByTagName('parsererror').length > 0) {
                console.error("XML Parsing Error in d2ladder.xml");
                return null;
            }
            return xmlDoc;
        })
        .catch(error => {
            console.error("Network or Fetch Error:", error);
            return null;
        });
}

function getXMLText(elem, tag) {
    const child = elem.querySelector(tag);
    if (child && child.textContent) {
        return child.textContent.trim();
    }
    return "";
}

// Форматиране на опит (Experience) с разделители
function formatExperience(exp) {
    const num = parseInt(exp);
    return isNaN(num) || num === 0 ? '-' : new Intl.NumberFormat('en-US').format(num);
}

// --- Main Ladder Logic ---
function loadLadder() {
    const container = document.getElementById('ladder-container');
    container.innerHTML = '<h2>Loading Ladder...</h2>';

    fetchXML('jsons/d2ladder.xml')
        .then(xmlDoc => {
            if (!xmlDoc) {
                container.innerHTML = '<h2>Error: Could not load data/d2ladder.xml. Check console for details.</h2>';
                return;
            }

            const ladders = xmlDoc.querySelectorAll('ladder');
            let htmlContent = '';
            
            const uniqueChars = {}; 
            let ladderModeName = 'Expansion'; // Задаваме Expansion по подразбиране
            let foundLadder27 = false;

            ladders.forEach(ladder => {
                const ladderType = getXMLText(ladder, 'type');
                
                // Филтриране: Показваме само Expansion (ID: 27)
                if (ladderType !== '27') {
                    return; 
                }
                
                ladderModeName = getXMLText(ladder, 'mode'); 
                foundLadder27 = true;

                const chars = ladder.querySelectorAll('char');
                
                chars.forEach(char => {
                    const rank = parseInt(getXMLText(char, 'rank'));
                    const name = getXMLText(char, 'name');
                    
                    if (!name) return;
                    
                    if (!uniqueChars[name] || rank < uniqueChars[name].rank) {
                         uniqueChars[name] = {
                             rank: rank,
                             name: name,
                             level: getXMLText(char, 'level'),
                             experience: getXMLText(char, 'experience'),
                             char_class: getXMLText(char, 'class'),
                             prefix: getXMLText(char, 'prefix'),
                             status: getXMLText(char, 'status')
                         };
                    }
                });
            }); 
            
            // 3. Сортиране и рендиране
            const sortedChars = Object.values(uniqueChars).sort((a, b) => a.rank - b.rank);

            if (foundLadder27) {
                // Заглавие без ID
                htmlContent += `<h2>Ladder Type: ${ladderModeName}</h2>`;
            }
            
            if (sortedChars.length > 0) {
                
                htmlContent += `<table class="ladder-table">`;
                htmlContent += `<tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Level</th>
                    <th>Experience</th>
                    <th>Class</th>
                    <th>Status</th>
                    <th>Prefix</th>
                </tr>`;
                
                sortedChars.forEach(char => {
                    
                    // Генериране на линк към charinfo.html
                    const charLink = `<a href="charinfo.html?name=${char.name.toLowerCase()}" target="_blank">${char.name}</a>`;
                    const formattedExp = formatExperience(char.experience);

                    htmlContent += `<tr>
                        <td>${char.rank}</td>
                        <td>${charLink}</td>
                        <td>${char.level}</td>
                        <td>${formattedExp}</td>
                        <td>${char.char_class}</td>
                        <td>${char.status}</td>
                        <td>${char.prefix}</td>
                    </tr>`;
                });

                htmlContent += `</table>`;
                container.innerHTML = htmlContent; 
            } else {
                 container.innerHTML = '<p>No Expansion Ladder entries found (ID 27).</p>';
            }

        }); // Край на then(xmlDoc => ...)
}

document.addEventListener('DOMContentLoaded', loadLadder);
