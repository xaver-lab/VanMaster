"use strict";

/* ------------------------------------------------------------- Routing */

/** #themen/Möbel/aufgaben */
function ausHash() {
  const teile = decodeURIComponent(location.hash.slice(1)).split("/");
  return { ansicht: teile[0] || "start", eins: teile[1] || "", zwei: teile[2] || "" };
}

function gehe(ansicht, eins, zwei) {
  const stueck = [ansicht, eins, zwei].filter(Boolean).map(encodeURIComponent);
  location.hash = stueck.join("/");
  route();
}

function route() {
  const { ansicht, eins, zwei } = ausHash();
  const name = ANSICHTEN.includes(ansicht) ? ansicht : "start";
  ANSICHT = name;
  for (const knopf of el("hauptnav").children) {
    knopf.classList.toggle("aktiv", knopf.dataset.ansicht === name);
  }
  for (const s of document.querySelectorAll(".ansicht")) {
    s.classList.toggle("aktiv", s.id === name);
  }
  const [titel, unter] = TITEL[name];
  el("kopf-h1").textContent = titel;
  el("kopf-unter").textContent = unter;
  if (name === "themen" && DATEN) themaZeigen(eins || THEMA_AKTIV, zwei);
  window.scrollTo({ top: 0 });
}

/* ------------------------------------------------------------ Bedienung */

el("hauptnav").addEventListener("click", (e) => {
  const knopf = e.target.closest("button");
  if (knopf) gehe(knopf.dataset.ansicht);
});

el("thema-schalter").addEventListener("click", () => {
  const neuesThema = document.documentElement.dataset.thema === "hell" ? "dunkel" : "hell";
  document.documentElement.dataset.thema = neuesThema;
  merken("thema", neuesThema);
});

el("suchknopf").addEventListener("click", paletteOeffnen);
el("palette").addEventListener("click", (e) => {
  if (e.target === el("palette")) paletteSchliessen();
});
el("palette-eingabe").addEventListener("input", (e) => paletteSuchen(e.target.value));
el("palette-eingabe").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    palettePos = Math.max(0, Math.min(paletteTreffer.length - 1,
      palettePos + (e.key === "ArrowDown" ? 1 : -1)));
    paletteZeichnen();
  } else if (e.key === "Enter" && paletteTreffer[palettePos]) {
    paletteSchliessen();
    paletteTreffer[palettePos].gehe();
  }
});

for (const id of ["teile-suche", "teile-kategorie"]) {
  el(id).addEventListener("input", teileListe);
}
el("teile-rasterwahl").addEventListener("click", (e) => {
  const knopf = e.target.closest("button");
  if (!knopf) return;
  teileRaster = knopf.dataset.raster;
  merken("teileRaster", teileRaster);
  teileRasterwahl();
  teileListe();
});
el("teil-modal").addEventListener("click", (e) => {
  if (e.target === el("teil-modal") || e.target.closest(".modal-zu")) teilModalSchliessen();
});
for (const id of ["aufgaben-suche", "aufgaben-gruppierung"]) {
  el(id).addEventListener("input", aufgabenListe);
}
for (const id of ["zuschnitt-suche", "zuschnitt-bereich"]) {
  el(id).addEventListener("input", zuschnittListe);
}
el("medien-bereich").addEventListener("input", medienGalerie);

el("themen-sortierung").addEventListener("input", (e) => {
  sortierungSetzen(e.target.value);
});

el("lupe").addEventListener("click", (e) => {
  if (e.target.closest(".lupe-pfeil.links")) return lupeBlaettern(-1);
  if (e.target.closest(".lupe-pfeil.rechts")) return lupeBlaettern(1);
  if (e.target.closest("figure") && e.target.tagName === "IMG") return;
  el("lupe").hidden = true;
});

document.addEventListener("click", () => {
  document.querySelectorAll(".menue").forEach((m) => m.remove());
});

window.addEventListener("keydown", (e) => {
  const imFeld = /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName);
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    paletteOeffnen();
    return;
  }
  if (e.key === "Escape") {
    paletteSchliessen();
    el("lupe").hidden = true;
    el("teil-modal").hidden = true;
    document.querySelectorAll(".menue").forEach((m) => m.remove());
    if (imFeld) document.activeElement.blur();
    return;
  }
  if (!el("lupe").hidden) {
    if (e.key === "ArrowLeft") lupeBlaettern(-1);
    if (e.key === "ArrowRight") lupeBlaettern(1);
    return;
  }
  if (imFeld) return;
  if (e.key === "/") { e.preventDefault(); paletteOeffnen(); return; }
  if (e.key.toLowerCase() === "t") { el("thema-schalter").click(); return; }
  const nummer = Number(e.key);
  if (nummer >= 1 && nummer <= ANSICHTEN.length) gehe(ANSICHTEN[nummer - 1]);
});

window.addEventListener("hashchange", route);

/* Wischen in der Lupe */
let wischStart = null;
el("lupe").addEventListener("touchstart", (e) => { wischStart = e.touches[0].clientX; },
                            { passive: true });
el("lupe").addEventListener("touchend", (e) => {
  if (wischStart === null) return;
  const weg = e.changedTouches[0].clientX - wischStart;
  if (Math.abs(weg) > 50) lupeBlaettern(weg < 0 ? 1 : -1);
  wischStart = null;
}, { passive: true });

/* --------------------------------------------------------------- Start */

document.documentElement.dataset.thema = gemerkt("thema", "dunkel");
THEMA_REITER = gemerkt("themaReiter", "ueberblick");

laden().then(() => {
  if (!DATEN) return;
  route();
  // Beim Arbeiten am Laptop: nach einem `sync` von selbst nachladen.
  if (SCHREIBEN) setInterval(nachladenWennNeu, 4000);
});

/* Läuft nebenher ein `camper sync`, ändert sich der Zeitstempel von
 * data.json — dann holt sich die Seite die neuen Daten von selbst. */
async function nachladenWennNeu() {
  try {
    const a = await fetch("api/hallo", { cache: "no-store" });
    const { stand } = await a.json();
    if (!stand || stand === STAND_DATEI) return;
    STAND_DATEI = stand;
    const frisch = await fetch("data.json", { cache: "no-store" });
    DATEN = await frisch.json();
    zeichnen();
    toast("Daten neu geladen");
  } catch (e) { /* Server weg — nicht weiter stören */ }
}
