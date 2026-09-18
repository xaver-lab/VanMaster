"use strict";

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
