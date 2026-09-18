"use strict";

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
