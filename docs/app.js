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
  bereichLeiste();
  bereichZeigen(BEREICH_AUS_HASH() || (DATEN.bereiche[0] || {}).name);
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

/** Aufgabenliste eines Bereichs — im Aufgaben-Tab und auf der Bereichsseite. */
function aufgabenListe(aufgaben, karte, bereich) {
  const ul = neu("ul", "aufgaben");
  let gruppe = null;
  for (const a of aufgaben) {
    if (a.gruppe && a.gruppe !== gruppe && a.gruppe !== bereich) {
      gruppe = a.gruppe;
      ul.append(neu("li", "gruppe", gruppe));
    }
    const li = neu("li", `${a.status} ebene-${Math.min(a.ebene, 2)}`);
    li.append(neu("span", "kasten", KASTEN[a.status] || "☐"));
    li.append(neu("span", "titel", a.titel));
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
  return ul;
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

    box.append(aufgabenListe(gezeigt, karte, name));

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
    if (absatz.length) {
      aus.push("<p>" + mdInline(absatz.join(" ")) + "</p>");
      absatz = [];
    }
  };
  const listeEnde = () => {
    if (liste) { aus.push("</" + liste + ">"); liste = null; }
  };

  for (const roh of (text || "").split("\n")) {
    const z = roh.trim();
    if (!z) { absatzEnde(); listeEnde(); continue; }

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
  absatzEnde(); listeEnde();
  return aus.join("");
}

function textblock(ueberschrift, text) {
  if (!text) return null;
  const box = neu("div", "textblock");
  box.append(neu("h3", null, ueberschrift));
  const inhalt = neu("div", "fliess");
  inhalt.innerHTML = md(text);
  box.append(inhalt);
  return box;
}

/* ------------------------------------------------------------- Bereiche */

let BEREICH_AKTIV = "";

const bereichTeile = (name) => DATEN.teile.filter(
  (t) => t.system === name || t.kategorie === name);

const bereichEinzelteile = (name) => (DATEN.bauteile || []).filter(
  (r) => r.bereich === name);

function bereichLeiste() {
  const leiste = el("bereich-leiste");
  leiste.innerHTML = "";
  for (const b of DATEN.bereiche) {
    const knopf = neu("button");
    knopf.dataset.bereich = b.name;
    knopf.append(neu("span", "name", b.name));
    if (b.gesamt) knopf.append(neu("span", "zahl", b.fertig + "/" + b.gesamt));
    knopf.addEventListener("click", () => {
      location.hash = "bereiche/" + encodeURIComponent(b.name);
    });
    leiste.append(knopf);
  }
}

function bereichZeigen(name) {
  const b = DATEN.bereiche.find((x) => x.name === name) || DATEN.bereiche[0];
  if (!b) return;
  BEREICH_AKTIV = b.name;
  for (const k of el("bereich-leiste").children) {
    k.classList.toggle("aktiv", k.dataset.bereich === b.name);
  }
  bereichInhalt(b);
}

function bereichInhalt(b) {
  const ziel = el("bereich-inhalt");
  ziel.innerHTML = "";

  const kopf = neu("div", "bereich-kopf");
  kopf.append(neu("h2", null, b.name));
  if (b.kurz) kopf.append(neu("p", "kurz", b.kurz));
  const zeile = neu("div", "zeile2");
  zeile.append(neu("span", "status " + b.status, b.status));
  if (b.gesamt) zeile.append(neu("span", null, b.fertig + "/" + b.gesamt + " Aufgaben"));
  kopf.append(zeile);
  if (b.gesamt) kopf.append(fortschrittszeile("", b.fertig, b.gesamt));
  ziel.append(kopf);

  for (const paar of [["Beschreibung", b.beschreibung], ["Stand", b.stand],
                      ["Auslegung", b.auslegung], ["Notizen", b.notizen]]) {
    const block = textblock(paar[0], paar[1]);
    if (block) ziel.append(block);
  }

  if (b.links && b.links.length) {
    const box = neu("div", "textblock");
    box.append(neu("h3", null, "Links"));
    const liste = neu("ul", "dokumente");
    for (const l of b.links) {
      const li = neu("li");
      const a = neu("a", null, l.titel);
      a.href = l.url;
      a.target = "_blank";
      a.rel = "noopener";
      li.append(a);
      if (l.zusatz) li.append(neu("span", "zusatz", " — " + l.zusatz));
      liste.append(li);
    }
    box.append(liste);
    ziel.append(box);
  }

  const bilder = DATEN.medien.filter((m) => m.bereich === b.name);
  const docs = (DATEN.dokumente || []).filter((m) => m.bereich === b.name);
  if (bilder.length || docs.length) {
    const box = neu("div", "textblock");
    box.append(neu("h3", null, "Bilder und Unterlagen"));
    if (bilder.length) box.append(bilderstreifen(bilder));
    if (docs.length) box.append(dokumentliste(docs));
    ziel.append(box);
  }

  ziel.append(modellblock(b.name));

  const aufgaben = DATEN.aufgaben.filter((a) => a.bereich === b.name);
  if (aufgaben.length) {
    const box = neu("div", "textblock");
    box.append(neu("h3", null, "Aufgaben"));
    box.append(aufgabenListe(aufgaben, nachId(), b.name));
    ziel.append(box);
  }

  ziel.append(einzelteilblock(b.name));

  const teile = bereichTeile(b.name);
  if (teile.length) {
    const box = neu("div", "textblock");
    const summe = teile.reduce((s, t) => s + t.gesamt, 0);
    box.append(neu("h3", null, "Teile aus der Stückliste (" + teile.length + ")"));
    box.append(neu("p", "summe", euro(summe)));
    const liste = neu("ul", "kurzteile");
    for (const t of teile) {
      const li = neu("li");
      li.append(neu("span", "status " + t.status, t.status || "—"));
      li.append(neu("span", "titel", t.titel));
      if (t.kennwerte) li.append(neu("span", "zusatz", t.kennwerte));
      liste.append(li);
    }
    box.append(liste);
    ziel.append(box);
  }

  const ent = (DATEN.entscheidungen || []).filter((e) => e.bereich === b.name);
  if (ent.length) {
    const box = neu("div", "textblock");
    box.append(neu("h3", null, "Entscheidungen"));
    for (const e of ent) {
      const details = neu("details", "entscheidung");
      const kopfz = neu("summary");
      kopfz.append(neu("span", "status " + e.status, e.status),
                   neu("span", "titel", e.titel));
      details.append(kopfz);
      const rumpf = neu("div", "fliess");
      rumpf.innerHTML = md(e.text);
      details.append(rumpf);
      box.append(details);
    }
    ziel.append(box);
  }
}

/* Platz für die 3D-Zeichnungen — heute Dateiliste, später der Betrachter. */
function modellblock(name) {
  const modelle = (DATEN.modelle || []).filter((m) => m.bereich === name);
  const box = neu("div", "textblock modelle");
  box.append(neu("h3", null, "3D-Modell"));
  const buehne = neu("div", "modell-buehne");
  if (!modelle.length) {
    buehne.append(neu("p", "leer",
      "Noch keine Zeichnung. Dateien nach vault/Modelle/" + name +
      "/ legen und `camper media` laufen lassen."));
    box.append(buehne);
    return box;
  }
  // Hier zieht der Betrachter ein, sobald eine .glb-Datei vorliegt.
  buehne.append(neu("p", "leer", modelle.length + " Datei(en) hinterlegt."));
  box.append(buehne, dokumentliste(modelle));
  return box;
}

function einzelteilblock(name) {
  const rows = bereichEinzelteile(name);
  const box = neu("div", "textblock");
  box.append(neu("h3", null, "Einzelteile (" + rows.length + ")"));
  if (!rows.length) {
    box.append(neu("p", "leer",
      "Noch keine. Anlegen mit `camper bauteile add --titel … --bereich " +
      name + "`."));
    return box;
  }
  const tabelle = neu("table", "einzelteile");
  const kopf = neu("tr");
  for (const spalte of ["Teil", "Maß (mm)", "Anz", "Material", "Quelle", "Status"]) {
    kopf.append(neu("th", null, spalte));
  }
  tabelle.append(kopf);
  for (const r of rows) {
    const tr = neu("tr");
    const erste = neu("td");
    erste.append(neu("span", "titel", r.titel));
    if (r.teil_id) erste.append(neu("span", "zusatz", " aus " + r.teil_id));
    tr.append(erste);
    tr.append(neu("td", "mass", r.mass || "—"));
    tr.append(neu("td", null, r.anzahl || "1"));
    tr.append(neu("td", null, r.material || "—"));
    tr.append(neu("td", "quelle", r.massquelle || "—"));
    const st = neu("td");
    st.append(neu("span", "status " + r.status, r.status || "—"));
    tr.append(st);
    tabelle.append(tr);
  }
  const rahmen = neu("div", "tabellenrand");
  rahmen.append(tabelle);
  box.append(rahmen);
  const qm = rows.reduce((s, r) => s + (r.flaeche_m2 || 0), 0);
  if (qm) box.append(neu("p", "summe", qm.toFixed(2) + " m² Fläche gesamt"));
  return box;
}

/* --------------------------------------------------------------- Bedienung */

/** #bereiche/Möbel → "Möbel"; sonst leer. */
function BEREICH_AUS_HASH() {
  const teile = location.hash.slice(1).split("/");
  return teile[0] === "bereiche" && teile[1]
    ? decodeURIComponent(teile[1]) : "";
}

function tabZeigen(name) {
  for (const b of el("tabs").children) {
    b.classList.toggle("aktiv", b.dataset.tab === name);
  }
  for (const s of document.querySelectorAll(".tab")) {
    s.classList.toggle("aktiv", s.id === name);
  }
}

el("tabs").addEventListener("click", (e) => {
  const knopf = e.target.closest("button");
  if (!knopf) return;
  location.hash = knopf.dataset.tab === "bereiche" && BEREICH_AKTIV
    ? "bereiche/" + encodeURIComponent(BEREICH_AKTIV)
    : knopf.dataset.tab;
  tabZeigen(knopf.dataset.tab);
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
  const tab = location.hash.slice(1).split("/")[0];
  if (!document.querySelector(`#tabs button[data-tab="${tab}"]`)) return;
  tabZeigen(tab);
  const name = BEREICH_AUS_HASH();
  if (name) bereichZeigen(name);
});

laden().then(() => {
  if (location.hash) window.dispatchEvent(new HashChangeEvent("hashchange"));
});
