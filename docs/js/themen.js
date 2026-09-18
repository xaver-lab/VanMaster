"use strict";

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
