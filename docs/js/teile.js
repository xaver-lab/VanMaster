"use strict";

/* --------------------------------------------------------------- Teile */

let teileFilterStatus = gemerkt("teileFilter", "");

function teileFilter() {
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
    zeile.append(a);
  }
  zeile.append(statusWechsler(t));
  box.append(zeile);
  return box;
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
  const gitter = neu("div", "teilgitter");
  for (const t of teile) gitter.append(teilKarte(t));
  ziel.append(gitter);
}
