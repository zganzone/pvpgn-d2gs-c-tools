let DATA = {};

fetch("runewords.json")
  .then(r => r.json())
  .then(json => {
    DATA = json;
    renderRunewords();
    renderRunes();
  });

function showTab(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.add("hidden"));
  document.getElementById(name).classList.remove("hidden");
}

document.getElementById("rwSearch").addEventListener("input", renderRunewords);
document.getElementById("onlyCraftable").addEventListener("change", renderRunewords);
document.getElementById("runeSearch").addEventListener("input", renderRunes);

function renderRunewords() {
  const body = document.getElementById("rwBody");
  body.innerHTML = "";

  const search = document.getElementById("rwSearch").value.toLowerCase();
  const onlyCraftable = document.getElementById("onlyCraftable").checked;

  DATA.runewords.forEach(rw => {
    if (search && !rw.name.toLowerCase().includes(search)) return;
    if (onlyCraftable && !rw.can_build) return;

    const tr = document.createElement("tr");
    tr.className = rw.can_build ? "ok" : "bad";

    tr.innerHTML = `
      <td>${rw.name}</td>
      <td>${rw.can_build ? "OK" : "MISSING"}</td>
      <td>${Object.entries(rw.used).map(
        ([r, o]) => `<b>${r}</b><br><small>${o.join(", ")}</small>`
      ).join("<hr>") || "-"}</td>
      <td>${rw.missing.join("<br>") || "-"}</td>
    `;
    body.appendChild(tr);
  });
}

function renderRunes() {
  const list = document.getElementById("runeList");
  list.innerHTML = "";

  const search = document.getElementById("runeSearch").value.toLowerCase();

  Object.entries(DATA.rune_index).forEach(([rune, owners]) => {
    if (search && !rune.toLowerCase().includes(search)) return;

    const div = document.createElement("div");
    div.className = "runeBox";
    div.innerHTML = `<h3>${rune}</h3>` +
      owners.map(o =>
        `${o.account} / ${o.char} – ${o.count}x`
      ).join("<br>");
    list.appendChild(div);
  });
}
