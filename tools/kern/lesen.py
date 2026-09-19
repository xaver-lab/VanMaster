"""Liest Bereiche, Aufgaben, Querverweise, Entscheidungen/Anleitungen/
Recherche, Teile, Einzelteile und Medien nach FORMAT.md in die
Datenklassen aus tools/kern/modelle.py.

Grammatik für Aufgabenzeilen und CSV-Spalten wird bewusst aus den
bestehenden Modulen (tools/tasks.py, tools/parts.py, tools/bauteile.py)
übernommen statt neu erfunden — gleiches Verhalten, zusätzlich die
Fundstelle (Datei + Zeile/Zeilenbereich) je gelesener Einheit.

Pfade werden zur Laufzeit über das common-Modul geholt (``common.VAULT``
usw.), nie per ``from .common import VAULT`` — nur so kann das
Test-Fixture ``repo`` (tests/conftest.py) sie auf ein tmp_path-Verzeichnis
umbiegen.
"""
from __future__ import annotations

import csv
import re

from .. import common
from .format import (
    ANKER, BESCHREIBUNG, BOX, EINZELTEIL_FELDER, LEER, MARKE, PRIO,
    TEIL_FELDER, ZEILE, ebene, phase as _phase,
)
from .modelle import (
    Abschnitt, Aufgabe, Bereich, Bestand, Einzelteil, Medium, Querverweis,
    Seite, Teil,
)

# [[Ziel]] bzw. [[Ziel|Anzeigetext]] — siehe FORMAT.md Abschnitt 4.
QUERVERWEIS = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

# Feste, web-/claude-editierbare Abschnitte einer Bereichsdatei.
_SAUBER_ABSCHNITTE = {"Beschreibung", "Stand", "Auslegung", "Notizen", "Links"}


def _sauber(text: str) -> str:
    """Platzhalter wie ``_(noch nichts eingetragen)_`` zählen als leer."""
    text = text.strip()
    return "" if LEER.match(text) else text


def abschnitte_mit_zeilen(text: str) -> dict[str, Abschnitt]:
    """Wie ``common.abschnitte()``, zusätzlich mit Zeilennummern.

    Arbeitet auf dem vollen Dateitext samt YAML-Kopf — der Kopf enthält
    keine ``## ``-Zeilen, die Zählung bleibt also unverschoben. Text vor
    der ersten ``## ``-Zeile landet wie dort unter dem Schlüssel ``""``.
    """
    zeilen = text.splitlines()
    ergebnis: dict[str, Abschnitt] = {}
    name = ""
    von = 1
    puffer: list[str] = []

    def abschliessen(bis: int) -> None:
        ergebnis[name] = Abschnitt(
            name=name, text="\n".join(puffer).strip(), zeile_von=von, zeile_bis=bis)

    for nr, zeile in enumerate(zeilen, start=1):
        if zeile.startswith("## ") and not zeile.startswith("### "):
            abschliessen(nr - 1)
            name = zeile[3:].strip()
            von = nr
            puffer = []
            continue
        puffer.append(zeile)
    abschliessen(len(zeilen))
    return ergebnis


# ------------------------------------------------------------------ Bereiche

def bereiche_lesen() -> list[Bereich]:
    """Alle Bereichsdateien, in feste Abschnitte zerlegt (ohne Aufgaben)."""
    ergebnis: list[Bereich] = []
    if not common.BEREICHE_DIR.exists():
        return ergebnis
    for datei in sorted(common.BEREICHE_DIR.glob("*.md")):
        text = common.read_text(datei)
        meta, _ = common.split_frontmatter(text)
        abschnitte = abschnitte_mit_zeilen(text)
        for name in _SAUBER_ABSCHNITTE:
            if name in abschnitte:
                abschnitte[name].text = _sauber(abschnitte[name].text)
        rel = str(datei.relative_to(common.BEREICHE_DIR.parent.parent)).replace("\\", "/")
        ergebnis.append(Bereich(
            name=meta.get("bereich") or datei.stem,
            kurz=meta.get("kurz", ""),
            status=meta.get("status", "geplant"),
            phase=_phase(meta.get("phase")),
            datei=rel,
            abschnitte=abschnitte,
        ))
    return ergebnis


# ------------------------------------------------------------------ Aufgaben

def _block_enden(aufgaben_datei: list[Aufgabe], zeilen: list[str]) -> None:
    """Setzt ``block_bis`` je Aufgabe — letzte Zeile inkl. aller Unterpunkte
    und ihrer Beschreibungen, bis zur nächsten Aufgabe gleicher/geringerer
    Tiefe, einer neuen Gruppe oder einem neuen Abschnitt."""
    n = len(zeilen)
    for a in aufgaben_datei:
        ende = n
        for nr in range(a.zeile + 1, n + 1):
            zeile = zeilen[nr - 1]
            if zeile.startswith("## ") and not zeile.startswith("### "):
                ende = nr - 1
                break
            if zeile.startswith("#"):
                ende = nr - 1
                break
            treffer = ZEILE.match(zeile)
            if treffer and ebene(treffer.group("einzug")) <= a.ebene:
                ende = nr - 1
                break
        a.block_bis = max(ende, a.zeile)


def aufgaben_lesen() -> list[Aufgabe]:
    """Alle Aufgaben aller Bereichsdateien, flach mit Eltern-/Kind-Bezügen.

    Grammatik identisch zu ``tools.tasks.load()`` (gleiche Regexe, gleiche
    Reihenfolge Anker/Prio/Marken), zusätzlich Fundstelle je Aufgabe.
    """
    aufgaben: list[Aufgabe] = []
    if not common.BEREICHE_DIR.exists():
        return aufgaben
    for datei in sorted(common.BEREICHE_DIR.glob("*.md")):
        meta, _ = common.split_frontmatter(common.read_text(datei))
        bereich_name = meta.get("bereich") or datei.stem
        # Einheitlich: alle datei-Felder im Kern sind Pfade relativ zur
        # Repo-Wurzel mit "/" — anders als tools.tasks.load(), das den
        # rohen OS-Pfadtrenner liefert (Vergleichstest normalisiert dort).
        rel = str(datei.relative_to(common.BEREICHE_DIR.parent.parent)).replace("\\", "/")
        zeilen = common.read_text(datei).splitlines()

        gruppe = ""
        drin = False
        stapel: dict[int, str] = {}
        aufgaben_datei: list[Aufgabe] = []
        letzte_aufgabe: Aufgabe | None = None

        for nr, zeile in enumerate(zeilen, start=1):
            if zeile.startswith("## ") and not zeile.startswith("### "):
                drin = zeile[3:].strip().lower() == "aufgaben"
                gruppe = ""
                letzte_aufgabe = None
                continue
            if not drin:
                continue
            if zeile.startswith("#"):
                gruppe = zeile.lstrip("#").strip()
                letzte_aufgabe = None
                continue
            treffer = ZEILE.match(zeile)
            if not treffer:
                beschr = BESCHREIBUNG.match(zeile)
                if beschr and letzte_aufgabe is not None:
                    zusatz = beschr.group("text").rstrip()
                    letzte_aufgabe.beschreibung = (
                        f"{letzte_aufgabe.beschreibung}\n{zusatz}"
                        if letzte_aufgabe.beschreibung else zusatz)
                    if letzte_aufgabe.beschreibung_von is None:
                        letzte_aufgabe.beschreibung_von = nr
                    letzte_aufgabe.beschreibung_bis = nr
                continue
            tiefe = ebene(treffer.group("einzug"))
            rest = treffer.group("rest").strip()

            anker = ANKER.search(rest)
            kennung = anker.group(1) if anker else ""
            if anker:
                rest = ANKER.sub(" ", rest).strip()

            prio_t = PRIO.search(rest)
            prio = prio_t.group(1).lower() if prio_t else ""
            rest = PRIO.sub(" ", rest)

            braucht: list[str] = []
            dauer = ""
            for art, wert in MARKE.findall(rest):
                if art == "braucht":
                    braucht.extend(w for w in wert.split(",") if w)
                else:
                    dauer = wert
            titel = MARKE.sub("", rest).strip()

            if not kennung:
                kennung = common.slug(f"{bereich_name}-{titel}")[:60]

            neu = Aufgabe(
                id=kennung, titel=titel, status=BOX[treffer.group("box")],
                bereich=bereich_name, gruppe=gruppe, ebene=tiefe,
                eltern=stapel.get(tiefe - 1, ""), braucht=braucht,
                prio=prio, dauer=dauer, datei=rel, zeile=nr, block_bis=nr,
            )
            aufgaben.append(neu)
            aufgaben_datei.append(neu)
            letzte_aufgabe = neu
            stapel[tiefe] = kennung
            for t in list(stapel):
                if t > tiefe:
                    del stapel[t]

        _block_enden(aufgaben_datei, zeilen)

    nach_id = {a.id: a for a in aufgaben}
    for a in aufgaben:
        if a.eltern in nach_id:
            nach_id[a.eltern].kinder.append(a.id)
    return aufgaben


# ---------------------------------------------- Entscheidungen/Anleitungen/Recherche

def seiten_lesen(ordner, typ: str) -> list[Seite]:
    """Alle Markdown-Seiten eines Ordners (Entscheidungen/Anleitungen/Recherche)."""
    ergebnis: list[Seite] = []
    if not ordner.exists():
        return ergebnis
    for datei in sorted(ordner.glob("*.md")):
        text = common.read_text(datei)
        meta, body = common.split_frontmatter(text)
        abschnitte = abschnitte_mit_zeilen(text)
        rel = str(datei.relative_to(common.VAULT.parent)).replace("\\", "/")
        ergebnis.append(Seite(
            titel=datei.stem, typ=typ,
            status=str(meta.get("status", "")),
            bereich=str(meta.get("bereich", meta.get("system", ""))),
            datei=rel, abschnitte=abschnitte, text=body.strip(),
        ))
    return ergebnis


# --------------------------------------------------------------------- Teile

def teile_lesen() -> list[Teil]:
    if not common.PARTS_CSV.exists():
        return []
    ergebnis: list[Teil] = []
    with common.PARTS_CSV.open(encoding="utf-8", newline="") as fh:
        for nr, row in enumerate(csv.DictReader(fh), start=2):
            werte = {f: (row.get(f) or "") for f in TEIL_FELDER}
            ergebnis.append(Teil(**werte, zeile=nr))
    return ergebnis


def einzelteile_lesen() -> list[Einzelteil]:
    if not common.BAUTEILE_CSV.exists():
        return []
    ergebnis: list[Einzelteil] = []
    with common.BAUTEILE_CSV.open(encoding="utf-8", newline="") as fh:
        for nr, row in enumerate(csv.DictReader(fh), start=2):
            werte = {f: (row.get(f) or "") for f in EINZELTEIL_FELDER}
            ergebnis.append(Einzelteil(**werte, zeile=nr))
    return ergebnis


# -------------------------------------------------------------------- Medien

def _medium(datei, bereich_name: str, art: str) -> Medium:
    rel = str(datei.relative_to(common.VAULT.parent)).replace("\\", "/")
    try:
        groesse = datei.stat().st_size
    except OSError:
        groesse = 0
    return Medium(name=datei.stem, dateiname=datei.name, bereich=bereich_name,
                  art=art, datei=rel, groesse=groesse)


def medien_lesen() -> list[Medium]:
    from .. import media

    ergebnis: list[Medium] = []
    for datei, bereich_name, art in media.ablage():
        ergebnis.append(_medium(datei, bereich_name, art))
    if common.MODELLE_DIR.exists():
        for datei in sorted(common.MODELLE_DIR.rglob("*")):
            if datei.is_file() and datei.suffix.lower() in media.MODELLE:
                rel = datei.relative_to(common.MODELLE_DIR)
                bereich_name = rel.parts[0] if len(rel.parts) > 1 else "Unsortiert"
                ergebnis.append(_medium(datei, bereich_name, "modell"))
    return ergebnis


# --------------------------------------------------------------- Querverweise

def _aufloesen(ziel: str, bereich_namen: dict[str, str],
               seiten_nach_titel: dict[str, Seite],
               teile_nach_id: dict[str, Teil],
               teile_nach_titel: dict[str, Teil]) -> tuple[str | None, str | None]:
    z = ziel.strip().lower()
    if z in bereich_namen:
        return "bereich", bereich_namen[z]
    seite = seiten_nach_titel.get(z)
    if seite:
        return seite.typ, seite.titel
    teil = teile_nach_id.get(z) or teile_nach_titel.get(z)
    if teil:
        return "teil", teil.id
    return None, None


def querverweise_lesen(bereiche: list[Bereich], seiten_alle: list[Seite],
                       teile: list[Teil]) -> list[Querverweis]:
    """Handgeschriebene ``[[…]]``-Verweise aus Bereichs- und Seitendateien.

    Erzeugte Verweise (vault/Stückliste/, vault/Medien/Medien.md) werden
    bewusst nicht gelesen — sie sind Ausgabe, keine Wahrheit (FORMAT.md §4).
    """
    bereich_namen = {b.name.lower(): b.name for b in bereiche}
    seiten_nach_titel = {s.titel.lower(): s for s in seiten_alle}
    teile_nach_id = {t.id.lower(): t for t in teile if t.id}
    teile_nach_titel = {t.titel.lower(): t for t in teile if t.titel}

    quellen = []
    if common.BEREICHE_DIR.exists():
        quellen += sorted(common.BEREICHE_DIR.glob("*.md"))
    for ordner in (common.ENTSCHEIDUNGEN_DIR, common.ANLEITUNGEN_DIR, common.RECHERCHE_DIR):
        if ordner.exists():
            quellen += sorted(ordner.glob("*.md"))

    ergebnis: list[Querverweis] = []
    for datei in quellen:
        rel = str(datei.relative_to(common.VAULT.parent)).replace("\\", "/")
        for nr, zeile in enumerate(common.read_text(datei).splitlines(), start=1):
            for treffer in QUERVERWEIS.finditer(zeile):
                ziel = treffer.group(1).strip()
                anzeige = (treffer.group(2) or ziel).strip()
                typ, kennung = _aufloesen(ziel, bereich_namen, seiten_nach_titel,
                                          teile_nach_id, teile_nach_titel)
                ergebnis.append(Querverweis(
                    ziel=ziel, anzeigetext=anzeige, datei=rel, zeile=nr,
                    ziel_typ=typ, ziel_id=kennung,
                ))
    return ergebnis


# ------------------------------------------------------------------- Bestand

def laden() -> Bestand:
    """Alles zusammen — einmal lesen, ein Bestand."""
    bereiche = bereiche_lesen()
    aufgaben = aufgaben_lesen()
    nach_bereich: dict[str, list[Aufgabe]] = {}
    for a in aufgaben:
        nach_bereich.setdefault(a.bereich, []).append(a)
    for b in bereiche:
        b.aufgaben = nach_bereich.get(b.name, [])

    entscheidungen = seiten_lesen(common.ENTSCHEIDUNGEN_DIR, "entscheidung")
    anleitungen = seiten_lesen(common.ANLEITUNGEN_DIR, "anleitung")
    recherche = seiten_lesen(common.RECHERCHE_DIR, "recherche")
    teile = teile_lesen()
    einzelteile = einzelteile_lesen()
    medien = medien_lesen()
    querverweise = querverweise_lesen(
        bereiche, entscheidungen + anleitungen + recherche, teile)

    return Bestand(
        bereiche=bereiche, aufgaben=aufgaben, querverweise=querverweise,
        entscheidungen=entscheidungen, anleitungen=anleitungen, recherche=recherche,
        teile=teile, einzelteile=einzelteile, medien=medien,
    )
