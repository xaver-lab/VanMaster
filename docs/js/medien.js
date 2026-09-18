"use strict";

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

/** Bildraster. `zuordnen` (optional) liefert je Bild {label, art, oeffnen}
 * für eine kleine Beschriftung, welchem Teil/welcher Aufgabe es zugeordnet
 * ist — ein Klick darauf öffnet direkt dessen Detailmodal. */
function galerie(bilder, zuordnen) {
  const gitter = neu("div", "galerie");
  for (const b of bilder) {
    const kachel = neu("button", "kachel-bild");
    const img = neu("img");
    img.src = b.pfad;
    img.alt = b.name;
    img.loading = "lazy";
    kachel.append(img, neu("span", "beschriftung", b.name));
    const z = zuordnen && zuordnen(b);
    if (z) {
      const chip = neu("span", "zuordnung art-" + z.art, z.label);
      if (z.oeffnen) {
        chip.addEventListener("click", (e) => { e.stopPropagation(); z.oeffnen(); });
      }
      kachel.append(chip);
    }
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
