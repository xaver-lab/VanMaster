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

const STATUS_WORT = { offen: "offen", laeuft: "in Arbeit", blockiert: "blockiert",
                      erledigt: "abgeschlossen", verworfen: "verworfen" };
const STATUS_BEFEHL = { offen: "open", laeuft: "start", blockiert: "block",
                        erledigt: "done", verworfen: "drop" };
const AUFGABE_STATUS = ["offen", "laeuft", "blockiert", "erledigt"];
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

/** Statuswechsler für Aufgaben — gleicher Aufbau wie bei den Teilen. */
function aufgabeStatusWechsler(a) {
  const huelle = neu("div", "wechsler");
  const anzeige = a.status === "verworfen" ? "verworfen" : STATUS_WORT[a.status];
  const knopf = neu("button", null, anzeige + (a.kinder.length ? "" : " ▾"));
  knopf.className = "status " + a.status;
  huelle.append(knopf);

  if (a.kinder.length) {
    knopf.disabled = true;
    knopf.title = "Sammelaufgabe — Haken an den Unterpunkten";
    return huelle;
  }
  knopf.title = "Status ändern";
  knopf.addEventListener("click", (e) => {
    e.stopPropagation();
    const offen = huelle.querySelector(".menue");
    document.querySelectorAll(".menue").forEach((m) => m.remove());
    if (offen) return;
    const menue = neu("div", "menue");
    for (const s of AUFGABE_STATUS) {
      const eintrag = neu("button", a.status === s ? "aktiv" : "", STATUS_WORT[s]);
      eintrag.addEventListener("click", (ev) => {
        ev.stopPropagation();
        menue.remove();
        aufgabeSetzen(a, s);
      });
      menue.append(eintrag);
    }
    huelle.append(menue);
  });
  return huelle;
}

/** Aufgabenzeile — Klick öffnet das Detailmodal, das Kästchen den Statuswechsler. */
function aufgabeZeile(a, karte, mitThema) {
  const li = neu("li", `${a.status} ebene-${Math.min(a.ebene, 2)}` +
                       (a.kinder.length ? " kopfknoten" : ""));
  li.addEventListener("click", () => aufgabeModalOeffnen(a));

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

  li.append(aufgabeStatusWechsler(a), text);
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

function karte(ueberschrift, zaehler, icon) {
  const box = neu("section", "karte");
  const kopf = neu("div", "karten-kopf");
  if (icon) kopf.append(neu("span", "icon", icon));
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
