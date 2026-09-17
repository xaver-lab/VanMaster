/* VanMaster-Dashboard — liest docs/data.json, kein Build-Werkzeug nötig.
 *
 * Läuft in zwei Betriebsarten:
 *   Datei/file:// oder statischer Server  → nur lesen, Änderungen als Befehl.
 *   `python camper.py serve`              → Kästchen und Status schreiben direkt.
 */
"use strict";

/* ------------------------------------------------------------ Werkzeug */

const el = (id) => document.getElementById(id);
const neu = (tag, klasse, text) => {
  const k = document.createElement(tag);
  if (klasse) k.className = klasse;
  if (text !== undefined && text !== null) k.textContent = text;
  return k;
};
const leeren = (knoten) => { knoten.innerHTML = ""; return knoten; };
const euro = (n) => (n || 0).toLocaleString("de-AT", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0,
});
const kleinschrift = (s) => (s || "").toLowerCase();

const STATUS_WORT = { offen: "offen", laeuft: "läuft", erledigt: "erledigt",
                      verworfen: "verworfen" };
const STATUS_BEFEHL = { offen: "open", laeuft: "start", erledigt: "done",
                        verworfen: "drop" };
const TEIL_STATUS = ["Idee", "Recherche", "Entschieden", "Bestellt",
                     "Geliefert", "Verbaut"];

const ANSICHTEN = ["start", "themen", "aufgaben", "teile", "zuschnitt", "medien"];
const TITEL = {
  start: ["Start", "Woran gerade gearbeitet wird"],
  themen: ["Themen", "Ein Arbeitsraum je Bereich"],
  aufgaben: ["Aufgaben", "Alles, was noch zu tun ist"],
  teile: ["Teile", "Stückliste — was gekauft wird"],
  zuschnitt: ["Zuschnitt", "Einzelteile mit Maßen"],
  medien: ["Medien", "Bilder und Unterlagen"],
};

let DATEN = null;
let SCHREIBEN = false;          // Server mit Schreibzugriff erkannt?
let ANSICHT = "start";
let THEMA_AKTIV = "";
let THEMA_REITER = "ueberblick";
let LUPE_LISTE = [];
let LUPE_POS = 0;
let STAND_DATEI = 0;            // Zeitstempel von data.json, für das Nachladen

const merken = (schluessel, wert) => {
  try { localStorage.setItem("vm." + schluessel, wert); } catch (e) { /* egal */ }
};
const gemerkt = (schluessel, standard) => {
  try { return localStorage.getItem("vm." + schluessel) ?? standard; }
  catch (e) { return standard; }
};

/* --------------------------------------------------------------- Laden */

async function laden() {
  try {
    const antwort = await fetch("data.json", { cache: "no-store" });
    if (!antwort.ok) throw new Error(antwort.status);
    DATEN = await antwort.json();
  } catch (fehler) {
    DATEN = window.VANMASTER_DATEN || null;   // data.js — auch per Doppelklick
  }
  if (!DATEN) {
    el("stand").textContent = "keine Daten";
    el("buehne").append(neu("p", "leer",
      "data.json fehlt — einmal `python camper.py build` laufen lassen."));
    return;
  }
  await schreibzugriffPruefen();
  zeichnen();
}

async function schreibzugriffPruefen() {
  try {
    const a = await fetch("api/hallo", { cache: "no-store" });
    const hallo = a.ok ? await a.json() : {};
    SCHREIBEN = hallo.schreiben === true;
    STAND_DATEI = hallo.stand || 0;
  } catch (e) { SCHREIBEN = false; }
  const punkt = el("verbindung");
  punkt.classList.toggle("live", SCHREIBEN);
  punkt.title = SCHREIBEN
    ? "camper serve — Änderungen werden geschrieben"
    : "nur lesen — Änderungen als Befehl (camper serve startet den Schreibmodus)";
}

/** Nach einer Schreiboperation kommen die frischen Daten zurück. */
async function api(pfad, nutzlast) {
  const antwort = await fetch("api/" + pfad, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(nutzlast),
  });
  const ergebnis = await antwort.json();
  if (!antwort.ok || ergebnis.fehler) throw new Error(ergebnis.fehler || antwort.status);
  if (ergebnis.daten) DATEN = ergebnis.daten;
  if (ergebnis.stand) STAND_DATEI = ergebnis.stand;
  return ergebnis;
}

function zeichnen() {
  const stand = new Date(DATEN.erzeugt);
  el("stand").textContent = "Stand " + stand.toLocaleString("de-AT", {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
  kennzahlen();
  startSeite();
  themenListe();
  themaZeigen(THEMA_AKTIV || (DATEN.bereiche[0] || {}).name);
  aufgabenChips();
  aufgabenListe();
  teileFilter();
  teileListe();
  zuschnittFilter();
  zuschnittListe();
  medienFilter();
  medienGalerie();
  navZahlen();
}

function navZahlen() {
  const offen = blaetter().filter((a) => !erledigt(a)).length;
  el("nav-offen").textContent = offen || "";
}

/* ------------------------------------------------------- Aufgabenlogik */

const nachId = () => Object.fromEntries(DATEN.aufgaben.map((a) => [a.id, a]));
const erledigt = (a) => a.status === "erledigt" || a.status === "verworfen";
const blaetter = () => DATEN.aufgaben.filter((a) => !a.kinder.length);
const RANG = { kritisch: 0, hoch: 1, mittel: 2, nice: 3 };

function offeneAufgaben() {
  return blaetter().filter((a) => !erledigt(a))
    .sort((a, b) => (RANG[a.prio] ?? 2) - (RANG[b.prio] ?? 2));
}

function blocker(a, karte) {
  return (a.braucht || []).map((id) => karte[id]).filter((b) => b && !erledigt(b));
}

/** Klick auf das Kästchen: offen → läuft → erledigt → offen. */
function naechsterStatus(status, rueckwaerts) {
  const drei = ["offen", "laeuft", "erledigt"];
  const i = drei.indexOf(status);
  if (i < 0) return "offen";                    // aus „verworfen" zurück auf offen
  return drei[(i + (rueckwaerts ? -1 : 1) + 3) % 3];
}

async function aufgabeSetzen(a, status) {
  if (!SCHREIBEN) {
    befehlAnbieten(`python camper.py task ${STATUS_BEFEHL[status]} ${a.id}`);
    return;
  }
  try {
    const e = await api("task", { id: a.id, status });
    zeichnen();
    toast(e.text || `${a.titel} → ${STATUS_WORT[status]}`);
  } catch (fehler) {
    toast("Ging nicht: " + fehler.message);
  }
}

async function teilSetzen(t, status) {
  if (!SCHREIBEN) {
    befehlAnbieten(`python camper.py parts set ${t.id} status ${status}`);
    return;
  }
  try {
    await api("teil", { id: t.id, feld: "status", wert: status });
    zeichnen();
    toast(`${t.titel} → ${status}`);
  } catch (fehler) {
    toast("Ging nicht: " + fehler.message);
  }
}

/* ------------------------------------------------------------- Bausteine */

function fortschrittZeile(name, fertig, gesamt, beiKlick, geld) {
  const zeile = neu(beiKlick ? "button" : "div", "zeile-balken");
  const balken = neu("div", "balken" + (geld ? " geld" : ""));
  const fuellung = neu("span");
  fuellung.style.width = (gesamt ? (100 * fertig) / gesamt : 0) + "%";
  balken.append(fuellung);
  zeile.append(neu("div", "name", name), balken,
               neu("div", "zahl", geld ? euro(fertig) : `${fertig}/${gesamt}`));
  if (beiKlick) zeile.addEventListener("click", beiKlick);
  return zeile;
}

function ring(prozent) {
  const r = 22, u = 2 * Math.PI * r;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "ring");
  svg.setAttribute("viewBox", "0 0 56 56");
  svg.setAttribute("width", "56");
  svg.setAttribute("height", "56");
  svg.innerHTML =
    `<circle class="spur" cx="28" cy="28" r="${r}"></circle>` +
    `<circle class="fuell" cx="28" cy="28" r="${r}" ` +
    `stroke-dasharray="${(u * prozent) / 100} ${u}"></circle>` +
    `<text x="28" y="29">${prozent}%</text>`;
  return svg;
}

function marke(text, klasse) { return neu("span", "marke " + (klasse || ""), text); }

function statusMarke(wert) {
  return neu("span", "status " + (wert || "").replace(/\s+/g, "-"), wert || "—");
}

/** Aufgabenzeile mit klickbarem Kästchen. */
function aufgabeZeile(a, karte, mitThema) {
  const li = neu("li", `${a.status} ebene-${Math.min(a.ebene, 2)}` +
                       (a.kinder.length ? " kopfknoten" : ""));
  const kasten = neu("button", "kasten",
                     { erledigt: "✓", laeuft: "●", verworfen: "✕", offen: "" }[a.status] || "");
  kasten.title = a.kinder.length
    ? "Sammelaufgabe — Haken an den Unterpunkten"
    : `${STATUS_WORT[a.status]} · klicken zum Weiterschalten, Umschalt+Klick verwirft`;
  if (a.kinder.length) kasten.classList.add("bittewarten");
  kasten.addEventListener("click", (e) => {
    e.stopPropagation();
    if (a.kinder.length) return;
    aufgabeSetzen(a, e.shiftKey ? "verworfen" : naechsterStatus(a.status, e.altKey));
  });

  const text = neu("div", "aufgabe-text");
  text.append(neu("span", "titel", a.titel));
  const meta = neu("div", "aufgabe-meta");
  if (mitThema && a.bereich) {
    const b = marke(a.bereich, "thema");
    meta.append(b);
  }
  if (a.prio && a.prio !== "mittel") meta.append(marke(a.prio, a.prio));
  if (a.dauer) meta.append(marke(a.dauer));
  const wartet = blocker(a, karte);
  if (wartet.length) {
    meta.append(marke("braucht: " + wartet.map((b) => b.titel).join(", "), "blocker"));
  }
  if (meta.children.length) text.append(meta);

  li.append(kasten, text);
  return li;
}

function aufgabenUl(liste, karte, mitThema) {
  const ul = neu("ul", "aufgaben");
  let gruppe = null;
  for (const a of liste) {
    if (a.gruppe && a.gruppe !== gruppe && a.gruppe !== a.bereich) {
      gruppe = a.gruppe;
      ul.append(neu("li", "gruppe", gruppe));
    }
    ul.append(aufgabeZeile(a, karte, mitThema));
  }
  return ul;
}

function karte(ueberschrift, zaehler) {
  const box = neu("section", "karte");
  const kopf = neu("div", "karten-kopf");
  kopf.append(neu("h2", null, ueberschrift));
  if (zaehler) kopf.append(neu("span", "zaehler", zaehler));
  box.append(kopf);
  return box;
}

/* ----------------------------------------------------------- Kennzahlen */

function kennzahlen() {
  const k = DATEN.kennzahlen;
  const prozent = k.aufgaben_gesamt
    ? Math.round((100 * k.aufgaben_fertig) / k.aufgaben_gesamt) : 0;
  const ziel = leeren(el("kennzahlen"));

  const mitRing = neu("button", "kachel");
  mitRing.append(ring(prozent));
  const rechts = neu("div");
  rechts.append(neu("div", "wert", `${k.aufgaben_fertig}/${k.aufgaben_gesamt}`),
                neu("div", "titel", "Aufgaben erledigt"));
  mitRing.append(rechts);
  mitRing.addEventListener("click", () => gehe("aufgaben"));
  ziel.append(mitRing);

  const kacheln = [
    [euro(k.kosten), "Kosten geplant", `davon ${euro(k.kosten_bestellt)} bestellt`, "teile"],
    [k.gewicht.toFixed(0) + " kg", "Zuladung Teile", `${k.teile} Teile erfasst`, "teile"],
    [String(k.offene_entscheidungen), "offene Entscheidungen",
     k.bauteile ? `${k.bauteile} Einzelteile` : "im Vault hinterlegt", "themen"],
  ];
  for (const [wert, titel, zusatz, ziel_ansicht] of kacheln) {
    const kachel = neu("button", "kachel");
    const block = neu("div");
    block.append(neu("div", "wert", wert), neu("div", "titel", titel));
    if (zusatz) block.append(neu("div", "zusatz", zusatz));
    kachel.append(block);
    kachel.addEventListener("click", () => gehe(ziel_ansicht));
    ziel.append(kachel);
  }
}

/* --------------------------------------------------------------- Start */

function startSeite() {
  const karte_ = nachId();
  const naechste = offeneAufgaben().filter((a) => !blocker(a, karte_).length).slice(0, 8);
  const ziel = leeren(el("naechste"));
  el("naechste-zahl").textContent = offeneAufgaben().length + " offen";
  if (naechste.length) ziel.append(aufgabenUl(naechste, karte_, true));
  else ziel.append(neu("p", "leer", "Nichts offen — oder alles blockiert."));

  const bereiche = leeren(el("start-bereiche"));
  for (const b of bereicheSortiert()) {
    bereiche.append(fortschrittZeile(b.name, b.fertig, b.gesamt,
      () => gehe("themen", b.name)));
  }

  const kosten = leeren(el("start-kosten"));
  const groesste = Math.max(...DATEN.kategorien.map((x) => x.kosten), 1);
  el("kosten-summe").textContent = euro(DATEN.kennzahlen.kosten);
  for (const k of [...DATEN.kategorien].sort((a, b) => b.kosten - a.kosten)) {
    kosten.append(fortschrittZeile(k.name, k.kosten, groesste, () => {
      el("teile-kategorie").value = k.name;
      teileListe();
      gehe("teile");
    }, true));
  }

  const offeneEnt = (DATEN.entscheidungen || []).filter((e) => e.status !== "entschieden");
  el("start-entscheidungen-karte").hidden = !offeneEnt.length;
  const ent = leeren(el("start-entscheidungen"));
  for (const e of offeneEnt) {
    const zeile = neu("button", "zeile-balken");
    zeile.append(statusMarke(e.status), neu("div", "name", e.titel));
    zeile.querySelector(".name").style.flex = "1 1 auto";
    if (e.bereich) zeile.append(neu("div", "zahl", e.bereich));
    zeile.addEventListener("click", () => gehe("themen", e.bereich, "entscheidungen"));
    ent.append(zeile);
  }
}

/* -------------------------------------------------------------- Themen */

/* ------------------------------------------------- Reihenfolge der Themen */
/* Die Regeln stehen in tools/bereiche.py; data.json kommt bereits sortiert.
 * Hier wird nur umsortiert, wenn der Wechsler etwas anderes sagt. */

const SORTIERUNGEN = ["baustellen", "phase", "name"];
const SORT_WORT = { baustellen: "Baustellen zuerst", phase: "Bauabschnitt",
                    name: "A–Z" };
const SORT_STATUS_RANG = { "in-arbeit": 0, geplant: 1, fertig: 2 };
const OHNE_PHASE = 999;

let bereichSortierung = gemerkt("bereichSortierung", "");

const sortOffen = (b) => Math.max((b.gesamt || 0) - (b.fertig || 0), 0);

const SORT_SCHLUESSEL = {
  name: (b) => [b.name.toLowerCase()],
  baustellen: (b) => [SORT_STATUS_RANG[b.status] ?? 1, -sortOffen(b),
                      b.name.toLowerCase()],
  phase: (b) => [b.phase ?? OHNE_PHASE, SORT_STATUS_RANG[b.status] ?? 1,
                 -sortOffen(b), b.name.toLowerCase()],
};

function vergleiche(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) return -1;
    if (a[i] > b[i]) return 1;
  }
  return 0;
}

/* Gewählte Sortierung — leer heißt: die aus data.json übernehmen. */
function sortierungAktiv() {
  if (SORTIERUNGEN.includes(bereichSortierung)) return bereichSortierung;
  const aus_daten = DATEN && DATEN.sortierung;
  return SORTIERUNGEN.includes(aus_daten) ? aus_daten : "baustellen";
}

function bereicheSortiert() {
  const art = sortierungAktiv();
  if (DATEN.sortierung === art) return DATEN.bereiche;   // schon so gebaut
  const schluessel = SORT_SCHLUESSEL[art];
  return [...DATEN.bereiche].sort(
    (a, b) => vergleiche(schluessel(a), schluessel(b)));
}

function sortierungSetzen(art) {
  bereichSortierung = art;
  merken("bereichSortierung", art);
  startSeite();
  themenListe();
  aufgabenListe();
  zuschnittFilter();
  medienFilter();
  medienGalerie();
}

function sortierWechsler() {
  const wahl = el("themen-sortierung");
  leeren(wahl);
  for (const art of SORTIERUNGEN) wahl.append(new Option(SORT_WORT[art], art));
  wahl.value = sortierungAktiv();
}

const themaTeile = (name) => DATEN.teile.filter(
  (t) => t.system === name || t.kategorie === name);
const themaEinzelteile = (name) => (DATEN.bauteile || []).filter((r) => r.bereich === name);
const themaBilder = (name) => DATEN.medien.filter((m) => m.bereich === name);
const themaDokumente = (name) => (DATEN.dokumente || []).filter((m) => m.bereich === name);
const themaAufgaben = (name) => DATEN.aufgaben.filter((a) => a.bereich === name);
const themaEntscheidungen = (name) =>
  (DATEN.entscheidungen || []).filter((e) => e.bereich === name);

function themenListe() {
  sortierWechsler();
  const liste = leeren(el("themen-liste"));
  for (const b of bereicheSortiert()) {
    const knopf = neu("button");
    knopf.dataset.thema = b.name;
    knopf.append(neu("span", "name", b.name));
    const mini = neu("span", "mini");
    const fuellung = neu("span");
    fuellung.style.width = (b.gesamt ? (100 * b.fertig) / b.gesamt : 0) + "%";
    mini.append(fuellung);
    knopf.append(mini);
    knopf.addEventListener("click", () => gehe("themen", b.name));
    liste.append(knopf);
  }
}

function themaZeigen(name, reiter) {
  const b = DATEN.bereiche.find((x) => x.name === name) || bereicheSortiert()[0];
  if (!b) return;
  THEMA_AKTIV = b.name;
  if (reiter) THEMA_REITER = reiter;
  for (const k of el("themen-liste").children) {
    k.classList.toggle("aktiv", k.dataset.thema === b.name);
  }
  themaKopf(b);
  themaSegmente(b);
  themaInhalt(b);
  if (ANSICHT === "themen") el("kopf-unter").textContent = b.kurz || b.name;
}

function themaKopf(b) {
  const ziel = leeren(el("thema-kopf"));
  const oben = neu("div", "obenzeile");
  oben.append(neu("h2", null, b.name), statusMarke(b.status));
  ziel.append(oben);
  if (b.kurz) ziel.append(neu("p", "kurz", b.kurz));

  const teile = themaTeile(b.name);
  const werte = [
    [`${b.fertig}/${b.gesamt}`, "Aufgaben"],
    [euro(teile.reduce((s, t) => s + t.gesamt, 0)), "Teilekosten"],
    [teile.reduce((s, t) => s + t.gewicht_n, 0).toFixed(1) + " kg", "Gewicht"],
    [String(themaBilder(b.name).length + themaDokumente(b.name).length), "Medien"],
  ];
  const kasten = neu("div", "kennwerte");
  for (const [w, t] of werte) {
    const d = neu("div");
    d.append(neu("span", "w", w), neu("span", "t", t));
    kasten.append(d);
  }
  ziel.append(kasten);
  if (b.gesamt) ziel.append(fortschrittZeile("", b.fertig, b.gesamt));
}

function themaReiter(b) {
  return [
    ["ueberblick", "Überblick", 0],
    ["aufgaben", "Aufgaben", themaAufgaben(b.name).filter((a) => !a.kinder.length).length],
    ["teile", "Teile", themaTeile(b.name).length],
    ["zuschnitt", "Zuschnitt", themaEinzelteile(b.name).length],
    ["medien", "Medien", themaBilder(b.name).length + themaDokumente(b.name).length],
    ["entscheidungen", "Entscheidungen", themaEntscheidungen(b.name).length],
  ];
}

function themaSegmente(b) {
  const nav = leeren(el("thema-segmente"));
  const reiter = themaReiter(b);
  if (!reiter.some((r) => r[0] === THEMA_REITER)) THEMA_REITER = "ueberblick";
  for (const [id, wort, zahl] of reiter) {
    const knopf = neu("button", THEMA_REITER === id ? "aktiv" : "");
    knopf.append(neu("span", null, wort));
    if (zahl) knopf.append(neu("span", "zahl", String(zahl)));
    knopf.addEventListener("click", () => {
      THEMA_REITER = id;
      merken("themaReiter", id);
      themaSegmente(b);
      themaInhalt(b);
    });
    nav.append(knopf);
  }
}

function themaInhalt(b) {
  const ziel = leeren(el("thema-inhalt"));
  const bau = {
    ueberblick: () => themaUeberblick(b, ziel),
    aufgaben: () => {
      const aufgaben = themaAufgaben(b.name);
      const box = karte("Aufgaben", `${b.fertig}/${b.gesamt}`);
      if (aufgaben.length) box.append(aufgabenUl(aufgaben, nachId(), false));
      else box.append(neu("p", "leer", "Noch keine Aufgaben unter `## Aufgaben`."));
      ziel.append(box);
    },
    teile: () => ziel.append(themaTeileBlock(b)),
    zuschnitt: () => ziel.append(einzelteilBlock(b.name)),
    medien: () => ziel.append(themaMedienBlock(b), modellBlock(b.name)),
    entscheidungen: () => ziel.append(entscheidungsBlock(b.name)),
  }[THEMA_REITER];
  bau();
}

function themaUeberblick(b, ziel) {
  let etwas = false;
  for (const [ueber, text] of [["Beschreibung", b.beschreibung], ["Stand", b.stand],
                               ["Auslegung", b.auslegung], ["Notizen", b.notizen]]) {
    if (!text) continue;
    etwas = true;
    const box = karte(ueber);
    const inhalt = neu("div", "fliess");
    inhalt.innerHTML = md(text);
    box.append(inhalt);
    ziel.append(box);
  }
  if (b.links && b.links.length) {
    etwas = true;
    const box = karte("Links");
    const liste = neu("ul", "liste-schlicht");
    for (const l of b.links) {
      const li = neu("li");
      const a = neu("a", null, l.titel);
      a.href = l.url; a.target = "_blank"; a.rel = "noopener";
      li.append(a);
      if (l.zusatz) li.append(neu("span", "zusatz", l.zusatz));
      liste.append(li);
    }
    box.append(liste);
    ziel.append(box);
  }
  const bilder = themaBilder(b.name);
  if (bilder.length) {
    const box = karte("Bilder", String(bilder.length));
    box.append(galerie(bilder.slice(0, 8)));
    ziel.append(box);
  }
  if (!etwas && !bilder.length) {
    ziel.append(neu("p", "leer",
      `Noch nichts hinterlegt — vault/Bereiche/${b.name}.md füllen.`));
  }
}

function themaTeileBlock(b) {
  const teile = themaTeile(b.name);
  const summe = teile.reduce((s, t) => s + t.gesamt, 0);
  const box = karte("Teile aus der Stückliste", `${teile.length} · ${euro(summe)}`);
  if (!teile.length) {
    box.append(neu("p", "leer", "Keine Teile auf diesen Bereich gebucht."));
    return box;
  }
  const gitter = neu("div", "teilgitter");
  for (const t of teile) gitter.append(teilKarte(t));
  box.append(gitter);
  return box;
}

function themaMedienBlock(b) {
  const bilder = themaBilder(b.name);
  const docs = themaDokumente(b.name);
  const box = karte("Bilder und Unterlagen", String(bilder.length + docs.length));
  if (bilder.length) box.append(galerie(bilder));
  if (docs.length) box.append(dokumentListe(docs));
  if (!bilder.length && !docs.length) {
    box.append(neu("p", "leer",
      "Dateien nach `_input/` legen und `camper media` laufen lassen."));
  }
  return box;
}

function entscheidungsBlock(name) {
  const ent = themaEntscheidungen(name);
  const box = karte("Entscheidungen", String(ent.length));
  if (!ent.length) {
    box.append(neu("p", "leer", "Keine Entscheidung zu diesem Thema festgehalten."));
    return box;
  }
  for (const e of ent) {
    const details = neu("details", "sammelblock");
    const kopf = neu("summary");
    kopf.append(statusMarke(e.status), neu("span", "name", e.titel));
    details.append(kopf);
    const rumpf = neu("div", "fliess");
    rumpf.innerHTML = md(e.text);
    details.append(rumpf);
    box.append(details);
  }
  return box;
}

/* Platz für die 3D-Zeichnungen — heute Dateiliste, später der Betrachter. */
function modellBlock(name) {
  const modelle = (DATEN.modelle || []).filter((m) => m.bereich === name);
  if (!modelle.length) return neu("div");
  const box = karte("3D-Modell", String(modelle.length));
  box.append(dokumentListe(modelle));
  return box;
}

function einzelteilBlock(name) {
  const rows = themaEinzelteile(name);
  const box = karte("Einzelteile", String(rows.length));
  if (!rows.length) {
    box.append(neu("p", "leer",
      `Noch keine. Anlegen mit \`camper bauteile add --titel … --bereich ${name}\`.`));
    return box;
  }
  box.append(einzelteilTabelle(rows));
  const qm = rows.reduce((s, r) => s + (r.flaeche_m2 || 0), 0);
  if (qm) box.append(neu("p", "summenband", qm.toFixed(2) + " m² Fläche gesamt"));
  return box;
}

function einzelteilTabelle(rows) {
  const rahmen = neu("div", "tabellenrand");
  const tabelle = neu("table", "tabelle");
  const kopf = neu("tr");
  for (const spalte of ["Teil", "Maß (mm)", "Anz", "Material", "Quelle", "Status"]) {
    kopf.append(neu("th", null, spalte));
  }
  const thead = neu("thead"); thead.append(kopf);
  const tbody = neu("tbody");
  for (const r of rows) {
    const tr = neu("tr");
    const erste = neu("td");
    erste.append(neu("span", "titel", r.titel));
    if (r.teil_id) erste.append(neu("div", "zusatz", "aus " + r.teil_id));
    tr.append(erste);
    tr.append(neu("td", "mass", r.mass || "—"));
    tr.append(neu("td", "zahl", r.anzahl || "1"));
    tr.append(neu("td", null, r.material || "—"));
    tr.append(neu("td", "zusatz", r.massquelle || "—"));
    const st = neu("td"); st.append(statusMarke(r.status));
    tr.append(st);
    tbody.append(tr);
  }
  tabelle.append(thead, tbody);
  rahmen.append(tabelle);
  return rahmen;
}

/* ------------------------------------------------------------ Aufgaben */

const AUFGABEN_FILTER = ["offen", "laeuft", "erledigt", "alle"];
let aufgabenFilter = gemerkt("aufgabenFilter", "offen");

function aufgabenChips() {
  const ziel = leeren(el("aufgaben-chips"));
  const zahlen = {
    offen: blaetter().filter((a) => a.status === "offen").length,
    laeuft: blaetter().filter((a) => a.status === "laeuft").length,
    erledigt: blaetter().filter((a) => a.status === "erledigt").length,
    alle: blaetter().length,
  };
  for (const f of AUFGABEN_FILTER) {
    const chip = neu("button", "chip" + (aufgabenFilter === f ? " aktiv" : ""));
    chip.append(neu("span", null, { offen: "offen", laeuft: "läuft",
                                    erledigt: "erledigt", alle: "alle" }[f]));
    chip.append(neu("span", "zahl", String(zahlen[f])));
    chip.addEventListener("click", () => {
      aufgabenFilter = f;
      merken("aufgabenFilter", f);
      aufgabenChips();
      aufgabenListe();
    });
    ziel.append(chip);
  }
}

function aufgabenListe() {
  const ziel = leeren(el("aufgaben-liste"));
  const suche = kleinschrift(el("aufgaben-suche").value.trim());
  const gruppierung = el("aufgaben-gruppierung").value;
  const karte_ = nachId();

  let liste = DATEN.aufgaben.filter((a) => {
    if (suche && !kleinschrift(a.titel + " " + a.bereich + " " + a.gruppe).includes(suche)) {
      return false;
    }
    if (aufgabenFilter === "alle") return true;
    if (a.kinder.length) return false;
    return a.status === aufgabenFilter;
  });

  if (!liste.length) {
    ziel.append(neu("p", "leer", "Keine Aufgabe passt zum Filter."));
    return;
  }

  if (gruppierung === "flach") {
    liste = [...liste].sort((a, b) => (RANG[a.prio] ?? 2) - (RANG[b.prio] ?? 2));
    const box = karte("Alle Treffer", String(liste.length));
    box.append(aufgabenUl(liste, karte_, true));
    ziel.append(box);
    return;
  }

  const schluessel = gruppierung === "prio"
    ? (a) => a.prio || "mittel"
    : (a) => a.bereich || "Ohne Thema";
  const reihenfolge = gruppierung === "prio"
    ? ["kritisch", "hoch", "mittel", "nice"]
    : bereicheSortiert().map((b) => b.name);

  const gruppen = new Map();
  for (const a of liste) {
    const s = schluessel(a);
    if (!gruppen.has(s)) gruppen.set(s, []);
    gruppen.get(s).push(a);
  }
  const namen = [...gruppen.keys()].sort(
    (a, b) => (reihenfolge.indexOf(a) + 1 || 99) - (reihenfolge.indexOf(b) + 1 || 99));

  for (const name of namen) {
    const eintraege = gruppen.get(name);
    const alle = gruppierung === "prio"
      ? eintraege
      : themaAufgaben(name).filter((a) => !a.kinder.length);
    const fertig = alle.filter(erledigt).length;

    const block = neu("details", "sammelblock");
    block.open = true;
    const kopf = neu("summary");
    kopf.append(neu("span", "name", name));
    const balken = neu("div", "balken");
    const fuellung = neu("span");
    fuellung.style.width = (alle.length ? (100 * fertig) / alle.length : 0) + "%";
    balken.append(fuellung);
    kopf.append(balken, neu("span", "zaehler", `${fertig}/${alle.length}`));
    block.append(kopf, aufgabenUl(eintraege, karte_, gruppierung === "prio"));
    ziel.append(block);
  }
}

/* --------------------------------------------------------------- Teile */

let teileFilterStatus = gemerkt("teileFilter", "");

function teileFilter() {
  const kat = el("teile-kategorie");
  const gewaehlt = kat.value;
  leeren(kat).append(new Option("alle Kategorien", ""));
  for (const k of DATEN.kategorien) kat.append(new Option(`${k.name} (${k.teile})`, k.name));
  kat.value = gewaehlt;

  const ziel = leeren(el("teile-chips"));
  const vorhanden = [...new Set(DATEN.teile.map((t) => t.status))].filter(Boolean);
  for (const s of ["", ...TEIL_STATUS.filter((s) => vorhanden.includes(s))]) {
    const chip = neu("button", "chip" + (teileFilterStatus === s ? " aktiv" : ""));
    chip.append(neu("span", null, s || "alle"));
    if (s) {
      chip.append(neu("span", "zahl",
        String(DATEN.teile.filter((t) => t.status === s).length)));
    }
    chip.addEventListener("click", () => {
      teileFilterStatus = s;
      merken("teileFilter", s);
      teileFilter();
      teileListe();
    });
    ziel.append(chip);
  }
}

function teilKarte(t) {
  const box = neu("div", "teil");
  const kopf = neu("div", "kopf");
  kopf.append(neu("div", "name", t.titel), neu("div", "preis", euro(t.gesamt)));
  box.append(kopf);
  if (t.beschreibung) box.append(neu("p", "beschreibung", t.beschreibung));

  const zeile = neu("div", "zeile2");
  zeile.append(neu("span", null, t.kategorie));
  if (t.menge_n !== 1) zeile.append(neu("span", null, `${t.menge_n} ${t.einheit}`));
  if (t.kennwerte) zeile.append(neu("span", null, t.kennwerte));
  if (t.gewicht_n) zeile.append(neu("span", null, t.gewicht_n.toFixed(1) + " kg"));
  if (t.haendler) zeile.append(neu("span", null, t.haendler));
  if (t.link) {
    const a = neu("a", null, "Shop ↗");
    a.href = t.link; a.target = "_blank"; a.rel = "noopener";
    zeile.append(a);
  }
  zeile.append(statusWechsler(t));
  box.append(zeile);
  return box;
}

/** Statusknopf mit kleinem Menü — schreibt über die API oder zeigt den Befehl. */
function statusWechsler(t) {
  const huelle = neu("div", "wechsler");
  const knopf = neu("button", null, (t.status || "—") + " ▾");
  knopf.className = "status " + (t.status || "").replace(/\s+/g, "-");
  huelle.append(knopf);

  knopf.addEventListener("click", (e) => {
    e.stopPropagation();
    const offen = huelle.querySelector(".menue");
    document.querySelectorAll(".menue").forEach((m) => m.remove());
    if (offen) return;
    const menue = neu("div", "menue");
    for (const s of TEIL_STATUS) {
      const eintrag = neu("button", t.status === s ? "aktiv" : "", s);
      eintrag.addEventListener("click", (ev) => {
        ev.stopPropagation();
        menue.remove();
        teilSetzen(t, s);
      });
      menue.append(eintrag);
    }
    huelle.append(menue);
  });
  return huelle;
}

function teileListe() {
  const ziel = leeren(el("teile-liste"));
  const kat = el("teile-kategorie").value;
  const suche = kleinschrift(el("teile-suche").value.trim());

  const teile = DATEN.teile.filter((t) =>
    (!kat || t.kategorie === kat) &&
    (!teileFilterStatus || t.status === teileFilterStatus) &&
    (!suche || kleinschrift([t.titel, t.beschreibung, t.kennwerte, t.haendler,
                             t.notiz, t.system].join(" ")).includes(suche)));

  const summe = teile.reduce((s, t) => s + t.gesamt, 0);
  const kg = teile.reduce((s, t) => s + t.gewicht_n, 0);
  const band = leeren(el("teile-summe"));
  band.append(neu("span", null, `${teile.length} Teile`));
  const geld = neu("span"); geld.append(neu("b", null, euro(summe)));
  band.append(geld);
  if (kg) band.append(neu("span", null, kg.toFixed(1) + " kg"));
  const ohnePreis = teile.filter((t) => !t.preis_n).length;
  if (ohnePreis) band.append(neu("span", null, `${ohnePreis} ohne Preis`));

  if (!teile.length) {
    ziel.append(neu("p", "leer", "Kein Teil passt zum Filter."));
    return;
  }
  const gitter = neu("div", "teilgitter");
  for (const t of teile) gitter.append(teilKarte(t));
  ziel.append(gitter);
}

/* ----------------------------------------------------------- Zuschnitt */

function zuschnittFilter() {
  const wahl = el("zuschnitt-bereich");
  const gewaehlt = wahl.value;
  leeren(wahl).append(new Option("alle Themen", ""));
  for (const b of bereicheSortiert()) wahl.append(new Option(b.name, b.name));
  wahl.value = gewaehlt;
}

function zuschnittListe() {
  const ziel = leeren(el("zuschnitt-liste"));
  const bereich = el("zuschnitt-bereich").value;
  const suche = kleinschrift(el("zuschnitt-suche").value.trim());
  const rows = (DATEN.bauteile || []).filter((r) =>
    (!bereich || r.bereich === bereich) &&
    (!suche || kleinschrift([r.titel, r.material, r.notiz, r.bereich].join(" ")).includes(suche)));

  const band = leeren(el("zuschnitt-summe"));
  band.append(neu("span", null, `${rows.length} Einzelteile`));
  const qm = rows.reduce((s, r) => s + (r.flaeche_m2 || 0), 0);
  if (qm) { const b = neu("span"); b.append(neu("b", null, qm.toFixed(2) + " m²")); band.append(b); }
  const lfm = rows.reduce((s, r) => s + (r.laufmeter || 0), 0);
  if (lfm) band.append(neu("span", null, lfm.toFixed(2) + " lfm"));

  if (!rows.length) {
    ziel.append(neu("p", "leer",
      "Noch keine Einzelteile — `camper bauteile add --titel … --bereich …`."));
    return;
  }
  ziel.append(einzelteilTabelle(rows));
}

/* -------------------------------------------------------------- Medien */

const medienBereiche = () => {
  const vorhanden = new Set(
    [...DATEN.medien, ...(DATEN.dokumente || [])].map((m) => m.bereich));
  // Bekannte Themen in der gewählten Reihenfolge, alles Übrige hinten.
  const reihe = bereicheSortiert().map((b) => b.name).filter((n) => vorhanden.has(n));
  const rest = [...vorhanden].filter((n) => !reihe.includes(n)).sort();
  return [...reihe, ...rest];
};

let medienArt = "alle";

function galerie(bilder) {
  const gitter = neu("div", "galerie");
  for (const b of bilder) {
    const kachel = neu("button", "kachel-bild");
    const img = neu("img");
    img.src = b.pfad;
    img.alt = b.name;
    img.loading = "lazy";
    kachel.append(img, neu("span", "beschriftung", b.name));
    kachel.addEventListener("click", () => lupeOeffnen(bilder, bilder.indexOf(b)));
    gitter.append(kachel);
  }
  return gitter;
}

function dokumentListe(dokumente) {
  const liste = neu("ul", "liste-schlicht");
  for (const d of dokumente) {
    const li = neu("li");
    const a = neu("a", null, d.datei || d.name);
    a.href = d.pfad; a.target = "_blank"; a.rel = "noopener";
    li.append(a);
    if (d.bereich) li.append(neu("span", "zusatz", d.bereich));
    liste.append(li);
  }
  return liste;
}

function medienFilter() {
  const wahl = el("medien-bereich");
  const gewaehlt = wahl.value;
  leeren(wahl).append(new Option("alle Themen", ""));
  for (const b of medienBereiche()) wahl.append(new Option(b || "Unsortiert", b));
  wahl.value = gewaehlt;

  const chips = leeren(el("medien-chips"));
  for (const [id, wort] of [["alle", "alles"], ["bilder", "Bilder"],
                            ["dokumente", "Unterlagen"]]) {
    const chip = neu("button", "chip" + (medienArt === id ? " aktiv" : ""), wort);
    chip.addEventListener("click", () => { medienArt = id; medienFilter(); medienGalerie(); });
    chips.append(chip);
  }
}

function medienGalerie() {
  const ziel = leeren(el("medien-liste"));
  const nur = el("medien-bereich").value;
  let gezeigt = 0;

  for (const bereich of medienBereiche()) {
    if (nur && bereich !== nur) continue;
    const bilder = medienArt === "dokumente" ? [] : DATEN.medien.filter((m) => m.bereich === bereich);
    const docs = medienArt === "bilder" ? [] : (DATEN.dokumente || []).filter((m) => m.bereich === bereich);
    if (!bilder.length && !docs.length) continue;
    gezeigt += bilder.length + docs.length;
    const box = karte(bereich || "Unsortiert", String(bilder.length + docs.length));
    if (bilder.length) box.append(galerie(bilder));
    if (docs.length) box.append(dokumentListe(docs));
    ziel.append(box);
  }
  if (!gezeigt) {
    ziel.append(neu("p", "leer",
      "Noch nichts einsortiert — Dateien nach `_input/` legen, dann `camper media`."));
  }
}

/* --------------------------------------------------------------- Lupe */

function lupeOeffnen(liste, pos) {
  LUPE_LISTE = liste;
  LUPE_POS = Math.max(0, pos);
  lupeZeichnen();
  el("lupe").hidden = false;
}

function lupeZeichnen() {
  const b = LUPE_LISTE[LUPE_POS];
  if (!b) return;
  const lupe = el("lupe");
  lupe.querySelector("img").src = b.pfad;
  lupe.querySelector("figcaption").textContent =
    `${b.name}${b.bereich ? " · " + b.bereich : ""}  (${LUPE_POS + 1}/${LUPE_LISTE.length})`;
  const mehrere = LUPE_LISTE.length > 1;
  lupe.querySelectorAll(".lupe-pfeil").forEach((p) => { p.style.visibility = mehrere ? "" : "hidden"; });
}

function lupeBlaettern(schritt) {
  if (!LUPE_LISTE.length) return;
  LUPE_POS = (LUPE_POS + schritt + LUPE_LISTE.length) % LUPE_LISTE.length;
  lupeZeichnen();
}

/* ------------------------------------------------------------ Palette */

function palettenQuellen() {
  const eintraege = [];
  for (const b of bereicheSortiert()) {
    eintraege.push({ art: "Thema", text: b.name, neben: `${b.fertig}/${b.gesamt}`,
                     gehe: () => gehe("themen", b.name) });
  }
  for (const a of DATEN.aufgaben) {
    if (a.kinder.length) continue;
    eintraege.push({ art: "Aufgabe", text: a.titel, neben: a.bereich,
                     gehe: () => gehe("themen", a.bereich, "aufgaben") });
  }
  for (const t of DATEN.teile) {
    eintraege.push({ art: "Teil", text: t.titel, neben: euro(t.gesamt), gehe: () => {
      el("teile-suche").value = t.titel;
      teileListe();
      gehe("teile");
    } });
  }
  for (const e of DATEN.entscheidungen || []) {
    eintraege.push({ art: "Entscheidung", text: e.titel, neben: e.bereich,
                     gehe: () => gehe("themen", e.bereich, "entscheidungen") });
  }
  for (const m of DATEN.medien) {
    eintraege.push({ art: "Bild", text: m.name, neben: m.bereich,
                     gehe: () => lupeOeffnen(DATEN.medien, DATEN.medien.indexOf(m)) });
  }
  return eintraege;
}

let paletteTreffer = [];
let palettePos = 0;

function paletteOeffnen() {
  el("palette").hidden = false;
  const eingabe = el("palette-eingabe");
  eingabe.value = "";
  eingabe.focus();
  paletteSuchen("");
}

function paletteSchliessen() { el("palette").hidden = true; }

function paletteSuchen(text) {
  const suche = kleinschrift(text.trim());
  const alle = palettenQuellen();
  paletteTreffer = (suche
    ? alle.filter((e) => kleinschrift(e.text + " " + e.neben).includes(suche))
    : alle.filter((e) => e.art === "Thema")).slice(0, 40);
  palettePos = 0;
  paletteZeichnen();
}

function paletteZeichnen() {
  const ziel = leeren(el("palette-treffer"));
  if (!paletteTreffer.length) {
    ziel.append(neu("p", "leer", "Nichts gefunden."));
    return;
  }
  paletteTreffer.forEach((e, i) => {
    const knopf = neu("button", i === palettePos ? "aktiv" : "");
    knopf.append(neu("span", "art", e.art), neu("span", "txt", e.text));
    if (e.neben) knopf.append(neu("span", "neben", e.neben));
    knopf.addEventListener("click", () => { paletteSchliessen(); e.gehe(); });
    ziel.append(knopf);
  });
  const aktiv = ziel.children[palettePos];
  if (aktiv && aktiv.scrollIntoView) aktiv.scrollIntoView({ block: "nearest" });
}

/* -------------------------------------------------------------- Toasts */

function toast(text, knopf) {
  const t = neu("div", "toast");
  t.append(neu("span", null, text));
  if (knopf) t.append(knopf);
  el("toasts").append(t);
  setTimeout(() => t.remove(), knopf ? 9000 : 3500);
}

/** Ohne Schreibzugriff: den passenden Befehl zeigen, Kopierknopf daneben. */
function befehlAnbieten(befehl) {
  const t = neu("div", "toast");
  t.append(neu("span", null, "Nur Lesemodus — "), neu("code", null, befehl));
  const knopf = neu("button", null, "Kopieren");
  knopf.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(befehl);
      knopf.textContent = "kopiert ✓";
    } catch (e) {
      knopf.textContent = "geht nicht";
    }
  });
  t.append(knopf);
  el("toasts").append(t);
  setTimeout(() => t.remove(), 9000);
}

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

/* ------------------------------------------------------------- Markdown */

/* Kleiner Renderer — reicht für die Bereichstexte, keine Bibliothek nötig. */
function mdInline(s) {
  return s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,
             '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

function md(text) {
  const aus = [];
  let liste = null;
  let absatz = [];
  const absatzEnde = () => {
    if (absatz.length) { aus.push("<p>" + mdInline(absatz.join(" ")) + "</p>"); absatz = []; }
  };
  const listeEnde = () => { if (liste) { aus.push("</" + liste + ">"); liste = null; } };
  let tabelle = null;
  const tabelleEnde = () => { if (tabelle) { aus.push("</table></div>"); tabelle = null; } };
  // | a | b |  ·  die Trennzeile aus Strichen wird nur erkannt, nicht gezeigt.
  const zellen = (z) => z.slice(1, -1).split("|").map((c) => c.trim());

  for (const roh of (text || "").split("\n")) {
    const z = roh.trim();
    if (!z) { absatzEnde(); listeEnde(); tabelleEnde(); continue; }

    if (z.startsWith("|") && z.endsWith("|")) {
      absatzEnde(); listeEnde();
      if (/^\|[\s|:-]+\|$/.test(z)) {
        if (tabelle === "kopf") tabelle = "rumpf";
        continue;
      }
      const kopfzeile = tabelle === null;
      if (kopfzeile) { aus.push('<div class="tabellenrand"><table>'); tabelle = "kopf"; }
      const tag = kopfzeile ? "th" : "td";
      aus.push("<tr>" + zellen(z).map(
        (c) => "<" + tag + ">" + mdInline(c) + "</" + tag + ">").join("") + "</tr>");
      continue;
    }
    tabelleEnde();

    const ueberschrift = z.match(/^(#{1,6})\s+(.*)$/);
    if (ueberschrift) {
      absatzEnde(); listeEnde();
      const stufe = Math.min(ueberschrift[1].length + 2, 6);
      aus.push("<h" + stufe + ">" + mdInline(ueberschrift[2]) + "</h" + stufe + ">");
      continue;
    }

    const punkt = z.match(/^[-*]\s+(.*)$/);
    const nummer = z.match(/^\d+\.\s+(.*)$/);
    if (punkt || nummer) {
      absatzEnde();
      const art = punkt ? "ul" : "ol";
      if (liste !== art) { listeEnde(); aus.push("<" + art + ">"); liste = art; }
      aus.push("<li>" + mdInline((punkt || nummer)[1]) + "</li>");
      continue;
    }

    // Eingerückte Fortsetzung gehört zum vorigen Listenpunkt.
    if (liste && /^\s/.test(roh)) {
      aus[aus.length - 1] = aus[aus.length - 1]
        .replace(/<\/li>$/, " " + mdInline(z) + "</li>");
      continue;
    }

    listeEnde();
    absatz.push(z);
  }
  absatzEnde(); listeEnde(); tabelleEnde();
  return aus.join("");
}
