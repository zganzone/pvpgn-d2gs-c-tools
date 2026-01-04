let DATA = [];

fetch("runewords.json")
  .then(r => r.json())
  .then(json => {
    DATA = json.runewords;
    render();
  });

document.getElementById("search").addEventListener("input", render);
document.getElementById("onlyCraftable").addEventListener("change", render);

function render() {
  const tbody = document.querySelector("#runewordTable tbody");
  tbody.innerHTML = "";

  const search = document.getElementById("search").value.toLowerCase();
  const onlyCraftable = document.getElementById("onlyCraftable").checked;

  DATA.forEach(rw => {
    if (search && !rw.name.toLowerCase().includes(search)) return;
    if (onlyCraftable && !rw.can_build) return;

    const tr = document.createElement("tr");
    tr.className = rw.can_build ? "craftable" : "missing";

    // Name
    const tdName = document.createElement("td");
    tdName.textContent = rw.name;

    // Status
    const tdStatus = document.createElement("td");
    tdStatus.innerHTML = rw.can_build
      ? `<span class="status-ok">OK</span>`
      : `<span class="status-missing">MISSING</span>`;

    // Used
    const tdUsed = document.createElement("td");
    if (rw.used && Object.keys(rw.used).length > 0) {
      tdUsed.innerHTML = Object.entries(rw.used)
        .map(([rune, chars]) =>
          `<div><b>${rune}</b><br><span class="small">${chars.join(", ")}</span></div>`
        ).join("");
    } else {
      tdUsed.textContent = "-";
    }

    // Missing
    const tdMissing = document.createElement("td");
    if (rw.missing && rw.missing.length > 0) {
      tdMissing.innerHTML = rw.missing.join("<br>");
    } else {
      tdMissing.textContent = "-";
    }

    tr.appendChild(tdName);
    tr.appendChild(tdStatus);
    tr.appendChild(tdUsed);
    tr.appendChild(tdMissing);
    tbody.appendChild(tr);
  });
}
