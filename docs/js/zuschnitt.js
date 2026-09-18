"use strict";

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
