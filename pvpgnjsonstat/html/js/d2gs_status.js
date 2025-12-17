// =======================================================
// js/d2gs_status.js - Скрипт за зареждане и показване на D2GS status
// =======================================================

// ПЪТ: data/d2gs_status_latest.json (генериран от Python скрипта)
const JSON_FILE_URL = 'data/d2gs_status_latest.json'; 

// Функция за актуализиране на елемент
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Helper за конвертиране на секунди към Дни/Часове/Минути/Секунди
function secondsToDhms(seconds) {
    seconds = Number(seconds);
    const d = Math.floor(seconds / (3600*24));
    const h = Math.floor((seconds % (3600*24))/3600);
    const m = Math.floor((seconds % 3600)/60);
    const s = Math.floor(seconds % 60);
    let str = '';
    if(d>0) str += d+'d ';
    if(h>0) str += h+'h ';\n    if(m>0) str += m+'m ';\n    str += s+'s';
    return str;
}


// Основна функция за изтегляне и парсване на JSON данните
function fetchAndDisplayD2GSStatus() {
    
    // Първоначално задаваме статус "Loading"
    updateElement('d2gs-uptime', '...');

    fetch(JSON_FILE_URL)
        .then(response => {
            if (!response.ok) {
                // Ако файлът не е намерен (напр. 404), предполагаме Offline
                throw new Error(`HTTP Error: ${response.status} - Could not find JSON file`);
            }
            return response.json();
        })
        .then(data => {
            // Проверка за вътрешния статус на парсера
            // Предполагаме, че Python скриптът може да върне uptime_seconds
            if (data.status === "success" && data.data && data.data.uptime) {
                
                const uptimeSeconds = data.data.uptime.uptime_seconds;
                const uptimeDuration = secondsToDhms(uptimeSeconds) || 'N/A';
                
                // --- АКТУАЛИЗИРАНЕ НА HTML ПОЛЕТАТА ---\n                
                // 1. D2GS Uptime
                updateElement('d2gs-uptime', uptimeDuration);
            } else {
                updateElement('d2gs-uptime', 'Error/Offline');
            }
        })
        .catch(error => {
            // Грешка при мрежата или JSON парсването
            console.error("Failed to fetch D2GS status:", error.message);
            updateElement('d2gs-uptime', 'Offline');
        });
}

// 1. Изпълнение на функцията веднага след зареждане на DOM
document.addEventListener('DOMContentLoaded', fetchAndDisplayD2GSStatus);

// 2. Обновяване на статуса на всеки 30 секунди
// setInterval(fetchAndDisplayD2GSStatus, 30000);
