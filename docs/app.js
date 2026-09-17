/* VanMaster-Dashboard — liest docs/data.json, kein Build-Werkzeug nötig. */
"use strict";

const KASTEN = { offen: "☐", laeuft: "◐", erledigt: "☑", verworfen: "✕" };
const euro = (n) => (n || 0).toLocaleString("de-AT", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0,
});

let DATEN = null;

const el = (id) => document.getElementById(id);
const neu = (tag, klasse, text) => {
  const k = document.createElement(tag);
  if (klasse) k.className = klasse;
  if (text !== undefined) k.textContent = text;
  return k;
};

/* ---------------------------------------------------------------- Laden */

async function laden() {
  if (window.VANMASTER_DATEN) {        // data.js — auch per Doppelklick nutzbar
    DATEN = window.VANMASTER_DATEN;
    zeichnen();
    return;
  }
  try {
    const antwort = await fetch("data.json", { cache: "no-store" });
    if (!antwort.ok) throw new Error(antwort.status);
    DATEN = await antwort.json();
  } catch (fehler) {
    el("stand").textContent =
      "data.json nicht gefunden — einmal `python camper.py build` laufen lassen.";
    return;
  }
  zeichnen();
}

function zeichnen() {
  const stand = new Date(DATEN.erzeugt);
  el("stand").textContent = "Stand " + stand.toLocaleString("de-AT", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
  kennzahlen();
  uebersicht();
  aufgabenbaum();
  teileFilterFuellen();
  teileliste();
  bilderFilterFuellen();
  bildergalerie();
}

/* ----------------------------------------------------------- Medien */

const medienBereiche = () => [...new Set(
  [...DATEN.medien, ...(DATEN.dokumente || [])].map((m) => m.bereich))].sort();

/** Kachelstreifen mit Bildern eines Bereichs — auch im Aufgabenbaum genutzt. */
function bilderstreifen(bilder) {
  const gitter = neu("div", "galerie");
  for (const b of bilder) {
    const kachel = neu("button", "kachel-bild");
    const img = neu("img");
    img.src = b.pfad;
    img.alt = b.name;
    img.loading = "lazy";
    kachel.append(img);
    kachel.addEventListener("click", () => lupeZeigen(b));
    gitter.append(kachel);
  }
  return gitter;
}

function dokumentliste(dokumente) {
  const liste = neu("ul", "dokumente");
  for (const d of dokumente) {
    const li = neu("li");
    const a = neu("a", null, d.datei || d.name);
    a.href = d.pfad;
    a.target = "_blank";
    a.rel = "noopener";
    li.append(a);
    liste.append(li);
  }
  return liste;
}

function lupeZeigen(bild) {
  const lupe = el("lupe");
  lupe.querySelector("img").src = bild.pfad;
  lupe.querySelector("p").textContent = bild.name;
  lupe.hidden = false;
}

function bilderFilterFuellen() {
  const auswahl = el("f-bereich");
  for (const b of medienBereiche()) auswahl.append(new Option(b || "Unsortiert", b));
}

function bildergalerie() {
  const ziel = el("bilder-liste");
  const nur = el("f-bereich").value;
  ziel.innerHTML = "";
  let gezeigt = 0;

  for (const bereich of medienBereiche()) {
    if (nur && bereich !== nur) continue;
    const bilder = DATEN.medien.filter((m) => m.bereich === bereich);
    const docs = (DATEN.dokumente || []).filter((m) => m.bereich === bereich);
    if (!bilder.length && !docs.length) continue;
    gezeigt += bilder.length + docs.length;
    ziel.append(neu("h2", null, bereich || "Unsortiert"));
    if (bilder.length) ziel.append(bilderstreifen(bilder));
    if (docs.length) ziel.append(dokumentliste(docs));
  }
  if (!gezeigt) {
    ziel.append(neu("p", "leer",
      "Noch keine Bilder — `python camper.py media` einsortieren."));
  }
}

/* ----------------------------------------------------------- Kennzahlen */

function kennzahlen() {
  const k = DATEN.kennzahlen;
  const prozent = k.aufgaben_gesamt
    ? Math.round((100 * k.aufgaben_fertig) / k.aufgaben_gesamt) : 0;
  const kacheln = [
    [prozent + " %", `Fortschritt · ${k.aufgaben_fertig}/${k.aufgaben_gesamt}`],
    [euro(k.kosten), "Kosten geplant"],
    [euro(k.kosten_bestellt), "davon bestellt"],
    [k.gewicht.toFixed(0) + " kg", "Zuladung Teile"],
  ];
  const ziel = el("kennzahlen");
  ziel.innerHTML = "";
  for (const [wert, titel] of kacheln) {
    const kachel = neu("div", "kachel");
    kachel.append(neu("div", "wert", wert), neu("div", "titel", titel));
    ziel.append(kachel);
  }
}

function fortschrittszeile(name, fertig, gesamt) {
  const zeile = neu("div", "fortschritt");
  const balken = neu("div", "balken");
  const fuellung = neu("span");
  fuellung.style.width = (gesamt ? (100 * fertig) / gesamt : 0) + "%";
  balken.append(fuellung);
  zeile.append(neu("div", "name", name), balken,
               neu("div", "zahl", `${fertig}/${gesamt}`));
  return zeile;
}

/* ------------------------------------------------------------ Übersicht */

function uebersicht() {
  const ziel = el("uebersicht");
  ziel.innerHTML = "";

  ziel.append(neu("h2", null, "Fortschritt je Bereich"));
  for (const b of DATEN.bereiche) {
    ziel.append(fortschrittszeile(b.name, b.fertig, b.gesamt));
  }

  const naechste = offeneAufgaben().filter((a) => !blockiert(a)).slice(0, 6);
  if (naechste.length) {
    ziel.append(neu("h2", null, "Als Nächstes"));
    const liste = neu("ul", "bereich-liste");
    liste.style.cssText = "list-style:none;margin:0;padding:0";
    for (const a of naechste) {
      const li = neu("li", "teil");
      li.append(neu("div", "name", a.titel));
      const zeile = neu("div", "zeile2");
      zeile.append(neu("span", null, a.bereich));
      if (a.prio) zeile.append(neu("span", "marke " + a.prio, a.prio));
      if (a.dauer) zeile.append(neu("span", null, a.dauer));
      li.append(zeile);
      liste.append(li);
    }
    ziel.append(liste);
  }

  if (DATEN.kategorien.length) {
    ziel.append(neu("h2", null, "Kosten je Kategorie"));
    for (const k of DATEN.kategorien) {
      const zeile = neu("div", "fortschritt");
      const balken = neu("div", "balken");
      const groesste = Math.max(...DATEN.kategorien.map((x) => x.kosten), 1);
      const fuellung = neu("span");
      fuellung.style.width = (100 * k.kosten) / groesste + "%";
      fuellung.style.background = "var(--akzent)";
      balken.append(fuellung);
      zeile.append(neu("div", "name", k.name), balken,
                   neu("div", "zahl", euro(k.kosten)));
      ziel.append(zeile);
    }
  }
}

/* ------------------------------------------------------------- Aufgaben */

const nachId = () => Object.fromEntries(DATEN.aufgaben.map((a) => [a.id, a]));

function offeneAufgaben() {
  const rang = { kritisch: 0, hoch: 1, mittel: 2, nice: 3 };
  return DATEN.aufgaben
    .filter((a) => !a.kinder.length && a.status !== "erledigt" && a.status !== "verworfen")
    .sort((a, b) => (rang[a.prio] ?? 2) - (rang[b.prio] ?? 2));
}

function blockiert(a) {
  const karte = nachId();
  return a.braucht.some((id) => karte[id] &&
    karte[id].status !== "erledigt" && karte[id].status !== "verworfen");
}

function aufgabenbaum() {
  const ziel = el("aufgaben-baum");
  const suche = el("aufgaben-suche").value.trim().toLowerCase();
  const nurOffen = el("nur-offen").checked;
  const karte = nachId();
  ziel.innerHTML = "";

  const bereiche = [...new Set(DATEN.aufgaben.map((a) => a.bereich))];
  let sichtbar = 0;

  for (const name of bereiche) {
    let liste = DATEN.aufgaben.filter((a) => a.bereich === name);
    const blaetter = liste.filter((a) => !a.kinder.length);
    const fertig = blaetter.filter(
      (a) => a.status === "erledigt" || a.status === "verworfen").length;

    let gezeigt = liste;
    if (suche) gezeigt = gezeigt.filter((a) => a.titel.toLowerCase().includes(suche));
    if (nurOffen) gezeigt = gezeigt.filter(
      (a) => a.status !== "erledigt" && a.status !== "verworfen");
    if (!gezeigt.length) continue;
    sichtbar += gezeigt.length;

    const box = neu("details", "bereich");
    box.open = Boolean(suche) || bereiche.length <= 3;
    const kopf = neu("summary");
    const balken = neu("div", "balken");
    const fuellung = neu("span");
    fuellung.style.width = (blaetter.length ? (100 * fertig) / blaetter.length : 0) + "%";
    balken.append(fuellung);
    kopf.append(neu("span", "name", name), balken,
                neu("span", "zahl", `${fertig}/${blaetter.length}`));
    box.append(kopf);

    const ul = neu("ul");
    let gruppe = null;
    for (const a of gezeigt) {
      if (a.gruppe && a.gruppe !== gruppe && a.gruppe !== name) {
        gruppe = a.gruppe;
        ul.append(neu("li", "gruppe", gruppe));
      }
      const li = neu("li", `${a.status} ebene-${Math.min(a.ebene, 2)}`);
      li.append(neu("span", "kasten", KASTEN[a.status] || "☐"));
      const text = neu("span", "titel", a.titel);
      li.append(text);
      if (a.prio) li.append(neu("span", "marke " + a.prio, a.prio));
      const offeneBlocker = a.braucht
        .map((id) => karte[id])
        .filter((b) => b && b.status !== "erledigt" && b.status !== "verworfen");
      if (offeneBlocker.length) {
        li.append(neu("span", "marke blocker",
                      "braucht: " + offeneBlocker.map((b) => b.titel).join(", ")));
      }
      ul.append(li);
    }
    box.append(ul);

    const bilder = DATEN.medien.filter((m) => m.bereich === name);
    const docs = (DATEN.dokumente || []).filter((m) => m.bereich === name);
    if (bilder.length || docs.length) {
      const anhang = neu("div", "anhang");
      anhang.append(neu("div", "gruppe", "Bilder & Unterlagen"));
      if (bilder.length) anhang.append(bilderstreifen(bilder));
      if (docs.length) anhang.append(dokumentliste(docs));
      box.append(anhang);
    }
    ziel.append(box);
  }
  if (!sichtbar) ziel.append(neu("p", "leer", "Keine Aufgabe passt zum Filter."));
}

/* ----------------------------------------------------------- Stückliste */

function teileFilterFuellen() {
  const kat = el("f-kategorie");
  const st = el("f-status");
  for (const k of DATEN.kategorien) kat.append(new Option(k.name, k.name));
  for (const s of [...new Set(DATEN.teile.map((t) => t.status))].filter(Boolean)) {
    st.append(new Option(s, s));
  }
}

function teileliste() {
  const ziel = el("teile-tabelle");
  const kat = el("f-kategorie").value;
  const st = el("f-status").value;
  const suche = el("teile-suche").value.trim().toLowerCase();

  const teile = DATEN.teile.filter((t) =>
    (!kat || t.kategorie === kat) &&
    (!st || t.status === st) &&
    (!suche || (t.titel + " " + t.beschreibung + " " + t.kennwerte + " " + t.haendler)
      .toLowerCase().includes(suche)));

  const summe = teile.reduce((s, t) => s + t.gesamt, 0);
  const kg = teile.reduce((s, t) => s + t.gewicht_n, 0);
  el("teile-summe").innerHTML =
    `${teile.length} Teile · <b>${euro(summe)}</b>` + (kg ? ` · ${kg.toFixed(1)} kg` : "");

  ziel.innerHTML = "";
  if (!teile.length) {
    ziel.append(neu("p", "leer", "Kein Teil passt zum Filter."));
    return;
  }
  for (const t of teile) {
    const karte = neu("div", "teil");
    const kopf = neu("div", "kopf");
    kopf.append(neu("div", "name", t.titel), neu("div", "preis", euro(t.gesamt)));
    karte.append(kopf);

    const zeile = neu("div", "zeile2");
    zeile.append(neu("span", "status " + t.status, t.status || "—"));
    zeile.append(neu("span", null, t.kategorie));
    if (t.menge_n !== 1) zeile.append(neu("span", null, `${t.menge_n} ${t.einheit}`));
    if (t.kennwerte) zeile.append(neu("span", null, t.kennwerte));
    if (t.gewicht_n) zeile.append(neu("span", null, t.gewicht_n.toFixed(1) + " kg"));
    if (t.haendler) zeile.append(neu("span", null, t.haendler));
    if (t.link) {
      const a = neu("a", null, "Link");
      a.href = t.link;
      a.target = "_blank";
      a.rel = "noopener";
      zeile.append(a);
    }
    karte.append(zeile);
    ziel.append(karte);
  }
}

/* --------------------------------------------------------------- Bedienung */

el("tabs").addEventListener("click", (e) => {
  const knopf = e.target.closest("button");
  if (!knopf) return;
  for (const b of el("tabs").children) b.classList.toggle("aktiv", b === knopf);
  for (const s of document.querySelectorAll(".tab")) {
    s.classList.toggle("aktiv", s.id === knopf.dataset.tab);
  }
  location.hash = knopf.dataset.tab;
});

for (const id of ["f-kategorie", "f-status", "teile-suche"]) {
  el(id).addEventListener("input", teileliste);
}
for (const id of ["aufgaben-suche", "nur-offen"]) {
  el(id).addEventListener("input", aufgabenbaum);
}
el("f-bereich").addEventListener("input", bildergalerie);

el("lupe").addEventListener("click", () => { el("lupe").hidden = true; });
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") el("lupe").hidden = true;
});

window.addEventListener("hashchange", () => {
  const knopf = document.querySelector(`#tabs button[data-tab="${location.hash.slice(1)}"]`);
  if (knopf) knopf.click();
});

laden().then(() => {
  if (location.hash) window.dispatchEvent(new HashChangeEvent("hashchange"));
});
