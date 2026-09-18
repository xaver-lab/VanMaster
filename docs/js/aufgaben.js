"use strict";

/* ------------------------------------------------------------ Aufgaben */

const AUFGABEN_FILTER = ["offen", "laeuft", "blockiert", "erledigt", "alle"];
let aufgabenFilter = gemerkt("aufgabenFilter", "offen");

/** Kopfbereich: was gerade in Arbeit ist, über alle Themen hinweg. */
function aufgabenUebersicht() {
  const ziel = leeren(el("aufgaben-uebersicht"));
  const laufend = blaetter().filter((a) => a.status === "laeuft");
  if (!laufend.length) {
    ziel.append(neu("p", "leer klein", "Gerade nichts in Arbeit."));
    return;
  }
  ziel.append(neu("h4", null, `In Arbeit (${laufend.length})`));
  const reihe = neu("div", "uebersicht-reihe");
  for (const a of laufend) {
    const eintrag = neu("button", "uebersicht-eintrag");
    eintrag.append(neu("span", "titel", a.titel));
    if (a.bereich) eintrag.append(neu("span", "zusatz", a.bereich));
    eintrag.addEventListener("click", () => aufgabeModalOeffnen(a));
    reihe.append(eintrag);
  }
  ziel.append(reihe);
}

function aufgabenChips() {
  const ziel = leeren(el("aufgaben-chips"));
  const zahlen = {
    offen: blaetter().filter((a) => a.status === "offen").length,
    laeuft: blaetter().filter((a) => a.status === "laeuft").length,
    blockiert: blaetter().filter((a) => a.status === "blockiert").length,
    erledigt: blaetter().filter((a) => a.status === "erledigt").length,
    alle: blaetter().length,
  };
  const beschriftung = { offen: "offen", laeuft: "in Arbeit", blockiert: "blockiert",
                         erledigt: "abgeschlossen", alle: "alle" };
  for (const f of AUFGABEN_FILTER) {
    const chip = neu("button", "chip" + (aufgabenFilter === f ? " aktiv" : ""));
    chip.append(neu("span", null, beschriftung[f]));
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
  aufgabenUebersicht();
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

  const eigeneGruppe = gruppierung === "prio" || gruppierung === "status";
  const schluessel = gruppierung === "prio" ? (a) => a.prio || "mittel"
    : gruppierung === "status" ? (a) => a.status
    : (a) => a.bereich || "Ohne Thema";
  const reihenfolge = gruppierung === "prio" ? ["kritisch", "hoch", "mittel", "nice"]
    : gruppierung === "status" ? ["laeuft", "blockiert", "offen", "erledigt", "verworfen"]
    : bereicheSortiert().map((b) => b.name);
  const anzeigename = gruppierung === "status" ? (s) => STATUS_WORT[s] || s : (s) => s;

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
    const alle = eigeneGruppe ? eintraege
      : themaAufgaben(name).filter((a) => !a.kinder.length);
    const fertig = alle.filter(erledigt).length;

    const block = neu("details", "sammelblock" + (gruppierung === "status" ? " nach-status " + name : ""));
    block.open = true;
    const kopf = neu("summary");
    kopf.append(neu("span", "name", anzeigename(name)));
    const balken = neu("div", "balken");
    const fuellung = neu("span");
    fuellung.style.width = (alle.length ? (100 * fertig) / alle.length : 0) + "%";
    balken.append(fuellung);
    kopf.append(balken, neu("span", "zaehler", `${fertig}/${alle.length}`));
    block.append(kopf, aufgabenUl(eintraege, karte_, eigeneGruppe));
    ziel.append(block);
  }
}

/* ----------------------------------------------------------- Detail */

function aufgabeModalOeffnen(a) {
  const box = leeren(el("aufgabe-modal-inhalt"));
  const karte_ = nachId();

  box.append(neu("div", "tm-titel", a.titel));
  const kopf = neu("div", "tm-kopf");
  kopf.append(aufgabeStatusWechsler(a));
  if (a.prio && a.prio !== "mittel") kopf.append(marke(a.prio, a.prio));
  if (a.dauer) kopf.append(marke(a.dauer));
  box.append(kopf);

  const wartet = blocker(a, karte_);
  if (wartet.length) {
    box.append(neu("p", "tm-beschreibung",
      "Blockiert durch: " + wartet.map((b) => b.titel).join(", ")));
  }

  if (a.kinder.length) {
    const abschnitt = neu("div", "tm-abschnitt");
    abschnitt.append(neu("h4", null, "Unterpunkte"));
    abschnitt.append(aufgabenUl(a.kinder.map((id) => karte_[id]).filter(Boolean), karte_, false));
    box.append(abschnitt);
  }

  const beschreibung = neu("div", "tm-abschnitt");
  beschreibung.append(neu("h4", null, "Wie wird das gemacht"));
  const feld = neu("textarea", "tm-notiz");
  feld.placeholder = "Noch keine Beschreibung — wie wird diese Aufgabe angegangen?";
  feld.rows = 4;
  feld.value = a.beschreibung || "";
  beschreibung.append(feld);
  if (SCHREIBEN) {
    const leiste = neu("div", "tm-notiz-leiste");
    const speichern = neu("button", "flachknopf", "Speichern");
    const hinweis = neu("span", "zusatz");
    speichern.addEventListener("click", async () => {
      try {
        const e = await api("task", { id: a.id, beschreibung: feld.value });
        hinweis.textContent = "gespeichert";
        setTimeout(() => { hinweis.textContent = ""; }, 1500);
        toast(e.text || "Beschreibung gespeichert");
      } catch (fehler) {
        toast("Ging nicht: " + fehler.message);
      }
    });
    leiste.append(speichern, hinweis);
    beschreibung.append(leiste);
  } else {
    feld.disabled = true;
    beschreibung.append(neu("p", "zusatz",
      "Nur mit `camper serve` bearbeitbar."));
  }
  box.append(beschreibung);

  if (a.fotos && a.fotos.length) {
    const abschnitt = neu("div", "tm-abschnitt");
    abschnitt.append(neu("h4", null, "Fotos"));
    const raster = neu("div", "tm-fotos");
    for (const f of a.fotos) {
      const kachel = neu("button");
      const img = neu("img");
      img.src = f.pfad; img.alt = f.name; img.loading = "lazy";
      kachel.append(img);
      kachel.addEventListener("click", () => lupeOeffnen(a.fotos, a.fotos.indexOf(f)));
      raster.append(kachel);
    }
    abschnitt.append(raster);
    box.append(abschnitt);
  }

  if (a.bereich) {
    const abschnitt = neu("div", "tm-abschnitt");
    abschnitt.append(neu("h4", null, "Thema"));
    const themen = neu("div", "tm-themen");
    const link = neu("a", "chip", a.bereich);
    link.href = "#" + ["themen", a.bereich].map(encodeURIComponent).join("/");
    link.addEventListener("click", () => aufgabeModalSchliessen());
    themen.append(link);
    abschnitt.append(themen);
    box.append(abschnitt);
  }

  el("aufgabe-modal").hidden = false;
}

function aufgabeModalSchliessen() {
  el("aufgabe-modal").hidden = true;
}
