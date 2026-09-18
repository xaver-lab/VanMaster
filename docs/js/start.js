"use strict";

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
