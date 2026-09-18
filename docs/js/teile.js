"use strict";

/* --------------------------------------------------------------- Teile */

let teileFilterStatus = gemerkt("teileFilter", "");
let teileRaster = gemerkt("teileRaster", "block");

function teileRasterwahl() {
  for (const knopf of el("teile-rasterwahl").children) {
    knopf.classList.toggle("aktiv", knopf.dataset.raster === teileRaster);
  }
}

function teileFilter() {
  teileRasterwahl();
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
    a.addEventListener("click", (e) => e.stopPropagation());
    zeile.append(a);
  }
  zeile.append(statusWechsler(t));
  box.append(zeile);
  box.addEventListener("click", () => teilModalOeffnen(t));
  return box;
}

function teilZeile(t) {
  const row = neu("div", "teilzeile");
  row.append(neu("span", "name", t.titel));
  row.append(neu("span", "kategorie", t.kategorie));
  row.append(neu("span", "preis", euro(t.gesamt)));
  row.append(statusWechsler(t));
  row.addEventListener("click", () => teilModalOeffnen(t));
  return row;
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
  if (teileRaster === "liste") {
    const liste = neu("div", "teilliste");
    for (const t of teile) liste.append(teilZeile(t));
    ziel.append(liste);
  } else {
    const gitter = neu("div", "teilgitter");
    for (const t of teile) gitter.append(teilKarte(t));
    ziel.append(gitter);
  }
}

/* ----------------------------------------------------------- Detail */

function teilModalOeffnen(t) {
  const box = leeren(el("teil-modal-inhalt"));

  box.append(neu("div", "tm-titel", t.titel));
  const kopf = neu("div", "tm-kopf");
  const status = statusWechsler(t);
  kopf.append(status);
  kopf.append(neu("span", null, euro(t.gesamt)));
  box.append(kopf);

  if (t.beschreibung) box.append(neu("p", "tm-beschreibung", t.beschreibung));

  const felder = [
    ["Kategorie", t.kategorie], ["System", t.system],
    ["Menge", t.menge_n ? `${t.menge_n} ${t.einheit}` : ""],
    ["Preis", t.preis_n ? euro(t.preis_n) + " / Stk" : ""],
    ["Priorität", t.prioritaet], ["Kennwerte", t.kennwerte],
    ["Gewicht", t.gewicht_n ? t.gewicht_n.toFixed(1) + " kg" : ""],
    ["Händler", t.haendler], ["Entscheidung", t.entscheidung],
    ["Notiz", t.notiz], ["Gekauft am", t.gekauft_am],
  ].filter(([, wert]) => wert);
  if (felder.length) {
    const dl = neu("dl", "tm-felder");
    for (const [k, wert] of felder) {
      const feld = neu("div", "tm-feld");
      feld.append(neu("dt", null, k), neu("dd", null, String(wert)));
      dl.append(feld);
    }
    box.append(dl);
  }

  if (t.link) {
    const abschnitt = neu("div", "tm-abschnitt");
    const a = neu("a", null, "Zum Shop ↗");
    a.href = t.link; a.target = "_blank"; a.rel = "noopener";
    abschnitt.append(a);
    box.append(abschnitt);
  }

  if (t.fotos && t.fotos.length) {
    const abschnitt = neu("div", "tm-abschnitt");
    abschnitt.append(neu("h4", null, "Fotos"));
    const raster = neu("div", "tm-fotos");
    for (const f of t.fotos) {
      const kachel = neu("button");
      const img = neu("img");
      img.src = f.pfad; img.alt = f.name; img.loading = "lazy";
      kachel.append(img);
      kachel.addEventListener("click", () => lupeOeffnen(t.fotos, t.fotos.indexOf(f)));
      raster.append(kachel);
    }
    abschnitt.append(raster);
    box.append(abschnitt);
  }

  if (t.bereich_name) {
    const abschnitt = neu("div", "tm-abschnitt");
    abschnitt.append(neu("h4", null, "Verwendet für"));
    const themen = neu("div", "tm-themen");
    const a = neu("a", "chip", t.bereich_name);
    a.href = "#" + ["themen", t.bereich_name].map(encodeURIComponent).join("/");
    a.addEventListener("click", () => teilModalSchliessen());
    themen.append(a);
    if (t.aufgabe_titel) themen.append(neu("span", "zusatz", "· " + t.aufgabe_titel));
    abschnitt.append(themen);
    box.append(abschnitt);
  }

  el("teil-modal").hidden = false;
}

function teilModalSchliessen() {
  el("teil-modal").hidden = true;
}
