"""Formatprüfung: meldet Abweichungen von FORMAT.md mit Datei und Zeile.

Arbeitet auf einem ``Bestand`` (``lesen.laden()``) für die inhaltlichen
Prüfungen (Bezüge, Kreise, Querverweise) und zusätzlich zeilenweise auf den
Rohdateien für alles, was der Parser gar nicht erst als Aufgabe erkennt
(unbekanntes Kästchenzeichen, fehlender Anker, ungültige Priorität,
ungerader Einzug) — solche Zeilen tauchen im Bestand schlicht nicht auf.

Reine Lesefunktion, kein Verhalten außer Melden. Schreibt nichts.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass

from .. import common
from . import lesen
from .format import ANKER, BOX, EINZELTEIL_FELDER, PRIOS, TEIL_FELDER, ebene
from .modelle import Bestand


@dataclass
class Befund:
    """Eine gemeldete Format-Abweichung."""

    datei: str    # repo-relativ, mit "/"
    zeile: int
    art: str      # "fehler" | "warnung"
    meldung: str


# --------------------------------------------------------------------- Hilfen

_ROH_BOX = re.compile(r"^([ \t]*)- \[(.)\](?: (.*))?$")
_HASH_TOKEN = re.compile(r"(?:^|\s)#([A-Za-z0-9\-_]+)")
_ZAHL = re.compile(r"^-?\d+([.,]\d+)?$")
_DATUM = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _kopf_zeilen(zeilen: list[str]) -> dict[str, int]:
    """Zeilennummer je Kopf-Schlüssel (nur oberste Ebene, keine Listen)."""
    schluessel: dict[str, int] = {}
    if not zeilen or zeilen[0].strip() != "---":
        return schluessel
    for nr, zeile in enumerate(zeilen[1:], start=2):
        if zeile.strip() == "---":
            break
        treffer = re.match(r"^(\w+):", zeile)
        if treffer:
            schluessel[treffer.group(1)] = nr
    return schluessel


def _rel(pfad, wurzel) -> str:
    return str(pfad.relative_to(wurzel)).replace("\\", "/")


# ---------------------------------------------------------- Bereichsdateien

def _bereichskopf(rel: str, zeilen: list[str], stem: str) -> list[Befund]:
    befunde: list[Befund] = []
    schluessel = _kopf_zeilen(zeilen)
    meta, _ = common.split_frontmatter("\n".join(zeilen))

    bereich_wert = meta.get("bereich")
    if not bereich_wert:
        befunde.append(Befund(rel, schluessel.get("bereich", 1), "fehler",
                               "bereich fehlt im Kopf"))
    elif bereich_wert != stem:
        befunde.append(Befund(rel, schluessel.get("bereich", 1), "fehler",
                               f"bereich '{bereich_wert}' passt nicht zum Dateinamen '{stem}'"))

    status_wert = meta.get("status")
    if status_wert and status_wert not in common.BEREICH_STATUS:
        befunde.append(Befund(rel, schluessel.get("status", 1), "fehler",
                               f"status '{status_wert}' ist nicht erlaubt"))

    if "phase" in meta and meta.get("phase"):
        from .format import phase as _phase
        if _phase(meta.get("phase")) is None:
            befunde.append(Befund(rel, schluessel.get("phase", 1), "fehler",
                                   "phase muss eine ganze Zahl sein"))

    return befunde


def _abschnitte_pruefen(rel: str, text: str, erwartet: list[str],
                        zeilenfeld_bei_fehlend: int = 1) -> list[Befund]:
    """Gemeinsame Prüfung für feste ##-Abschnitte in fester Reihenfolge."""
    befunde: list[Befund] = []
    abschnitte = lesen.abschnitte_mit_zeilen(text)
    gefunden = [name for name in abschnitte if name != ""]

    fehlend = [n for n in erwartet if n not in gefunden]
    fremd = [n for n in gefunden if n not in erwartet]

    for name in fehlend:
        befunde.append(Befund(rel, zeilenfeld_bei_fehlend, "fehler",
                               f"Abschnitt '## {name}' fehlt"))
    for name in fremd:
        befunde.append(Befund(rel, abschnitte[name].zeile_von, "fehler",
                               f"unbekannter Abschnitt '## {name}'"))

    if not fehlend and not fremd and gefunden != erwartet:
        erste_zeile = min(abschnitte[n].zeile_von for n in gefunden)
        befunde.append(Befund(rel, erste_zeile, "fehler",
                               "Abschnitte stehen nicht in der vorgeschriebenen Reihenfolge"))
    return befunde


# ---------------------------------------------------------------- Aufgaben

def _aufgaben_roh(rel: str, zeilen: list[str]) -> tuple[list[Befund], list[tuple[str, int]]]:
    """Zeilenweise Prüfung der ``## Aufgaben``-Zeilen selbst.

    Liefert die Befunde und, je gefundenem Anker in dieser Datei, ein
    (Anker, Zeile)-Paar (für die globale Eindeutigkeitsprüfung über alle
    Dateien — auch Duplikate innerhalb derselben Datei müssen erhalten
    bleiben, deshalb eine Liste statt eines Dicts).
    """
    befunde: list[Befund] = []
    anker_zeilen: list[tuple[str, int]] = []
    drin = False

    for nr, zeile in enumerate(zeilen, start=1):
        if zeile.startswith("## ") and not zeile.startswith("### "):
            drin = zeile[3:].strip().lower() == "aufgaben"
            continue
        if not drin:
            continue

        treffer = _ROH_BOX.match(zeile)
        if not treffer:
            continue
        einzug, box, rest = treffer.group(1), treffer.group(2), treffer.group(3) or ""

        if box not in BOX:
            befunde.append(Befund(rel, nr, "fehler",
                                   f"unbekanntes Kästchenzeichen '{box}'"))
            continue

        einzug_glatt = einzug.replace("\t", "  ")
        if len(einzug_glatt) % 2 != 0:
            befunde.append(Befund(rel, nr, "fehler",
                                   "Einzug ist nicht in Zweierschritten"))

        anker = ANKER.search(rest)
        if not anker:
            befunde.append(Befund(rel, nr, "fehler", "Anker (^id) fehlt"))
        else:
            anker_zeilen.append((anker.group(1), nr))

        rest_ohne_anker = ANKER.sub(" ", rest)
        for token in _HASH_TOKEN.findall(rest_ohne_anker):
            if token.lower() not in PRIOS:
                befunde.append(Befund(rel, nr, "fehler",
                                       f"ungültige Priorität '#{token}'"))

    return befunde, anker_zeilen


def _abhaengigkeiten(bestand: Bestand) -> list[Befund]:
    befunde: list[Befund] = []
    nach_id = {a.id: a for a in bestand.aufgaben}

    for a in bestand.aufgaben:
        for ziel in a.braucht:
            if ziel not in nach_id:
                befunde.append(Befund(a.datei, a.zeile, "fehler",
                                       f"@braucht:{ziel} zeigt auf keine bekannte Aufgabe"))

    # Kreise über @braucht — einfache Tiefensuche je Startknoten.
    gemeldet: set[frozenset] = set()
    for start in bestand.aufgaben:
        pfad: list[str] = []
        besucht: set[str] = set()

        def suche(a) -> None:
            if a.id in pfad:
                zyklus = pfad[pfad.index(a.id):] + [a.id]
                schluessel = frozenset(zyklus)
                if schluessel not in gemeldet:
                    gemeldet.add(schluessel)
                    ursprung = nach_id[pfad[0]]
                    befunde.append(Befund(
                        ursprung.datei, ursprung.zeile, "fehler",
                        f"Abhängigkeitskreis: {' -> '.join(zyklus)}"))
                return
            if a.id in besucht:
                return
            besucht.add(a.id)
            pfad.append(a.id)
            for ziel in a.braucht:
                folge = nach_id.get(ziel)
                if folge is not None:
                    suche(folge)
            pfad.pop()

        suche(start)

    return befunde


def _anker_eindeutig(je_datei: dict[str, list[tuple[str, int]]]) -> list[Befund]:
    """Globale Eindeutigkeit über alle Bereichsdateien hinweg."""
    befunde: list[Befund] = []
    vorkommen: dict[str, list[tuple[str, int]]] = {}
    for rel, anker_zeilen in je_datei.items():
        for anker, nr in anker_zeilen:
            vorkommen.setdefault(anker, []).append((rel, nr))

    for anker, stellen in vorkommen.items():
        if len(stellen) > 1:
            for rel, nr in stellen[1:]:
                befunde.append(Befund(rel, nr, "fehler",
                                       f"Anker ^{anker} ist nicht eindeutig"))
    return befunde


# --------------------------------------------------------------- Querverweise

def _querverweise(bestand: Bestand) -> list[Befund]:
    return [Befund(q.datei, q.zeile, "warnung",
                    f"Querverweis [[{q.ziel}]] ohne Ziel")
            for q in bestand.querverweise if q.ziel_typ is None]


# --------------------------------------------------- Entscheidungen & Co.

_ANLEITUNG_ABSCHNITTE = ["Material", "Werkzeug", "Schritte"]
_RECHERCHE_ABSCHNITTE = ["Frage", "Quellen", "Ergebnis"]


def _seiten_struktur() -> list[Befund]:
    befunde: list[Befund] = []
    for ordner, erwartet in (
        (common.ANLEITUNGEN_DIR, _ANLEITUNG_ABSCHNITTE),
        (common.RECHERCHE_DIR, _RECHERCHE_ABSCHNITTE),
    ):
        if not ordner.exists():
            continue
        for datei in sorted(ordner.glob("*.md")):
            text = common.read_text(datei)
            rel = _rel(datei, common.VAULT.parent)
            befunde += _abschnitte_pruefen(rel, text, erwartet)
    return befunde


# --------------------------------------------------------------------- CSV

def _csv_pruefen(pfad, rel_name: str, felder: list[str],
                 aufgaben_ids: set[str], entscheidung_titel: set[str],
                 teil_ids: set[str] | None = None) -> list[Befund]:
    befunde: list[Befund] = []
    if not pfad.exists():
        return befunde

    zeilen_roh = pfad.read_text(encoding="utf-8").splitlines()
    if not zeilen_roh:
        return befunde

    kopf = zeilen_roh[0].split(",")
    if kopf != felder:
        befunde.append(Befund(rel_name, 1, "fehler",
                               "Kopfzeile weicht von den vorgeschriebenen Spalten ab"))

    gesehene_ids: dict[str, int] = {}
    with pfad.open(encoding="utf-8", newline="") as fh:
        for nr, row in enumerate(csv.DictReader(fh), start=2):
            werte = {f: (row.get(f) or "") for f in felder}
            rid = werte.get("id", "")
            if rid:
                if rid in gesehene_ids:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"id '{rid}' ist nicht eindeutig"))
                else:
                    gesehene_ids[rid] = nr

            if "status" in werte and felder is TEIL_FELDER and werte["status"] \
                    and werte["status"] not in common.PART_STATUS:
                befunde.append(Befund(rel_name, nr, "fehler",
                                       f"status '{werte['status']}' ist nicht erlaubt"))
            if felder is TEIL_FELDER:
                if werte["prioritaet"] and werte["prioritaet"] not in common.PART_PRIO:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"prioritaet '{werte['prioritaet']}' ist nicht erlaubt"))
                if werte["kategorie"] and werte["kategorie"] not in common.PART_KATEGORIEN:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"kategorie '{werte['kategorie']}' ist nicht erlaubt"))
                for feld in ("menge", "preis", "gewicht_kg"):
                    wert = werte[feld]
                    if wert and not _ZAHL.match(wert.strip()):
                        befunde.append(Befund(rel_name, nr, "fehler",
                                               f"{feld} '{wert}' ist keine Zahl"))
                if werte["gekauft_am"] and not _DATUM.match(werte["gekauft_am"].strip()):
                    befunde.append(Befund(rel_name, nr, "warnung",
                                           f"gekauft_am '{werte['gekauft_am']}' ist kein Datum (JJJJ-MM-TT)"))
                if werte["fuer_aufgabe"] and werte["fuer_aufgabe"] not in aufgaben_ids:
                    befunde.append(Befund(rel_name, nr, "warnung",
                                           f"fuer_aufgabe '{werte['fuer_aufgabe']}' zeigt auf keine bekannte Aufgabe"))
                if werte["entscheidung"] and werte["entscheidung"] not in entscheidung_titel:
                    befunde.append(Befund(rel_name, nr, "warnung",
                                           f"entscheidung '{werte['entscheidung']}' zeigt auf keine bekannte Seite"))

            if felder is EINZELTEIL_FELDER:
                if werte["art"] and werte["art"] not in common.BAUTEIL_ART:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"art '{werte['art']}' ist nicht erlaubt"))
                if werte["massquelle"] and werte["massquelle"] not in common.MASSQUELLE:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"massquelle '{werte['massquelle']}' ist nicht erlaubt"))
                if werte["status"] and werte["status"] not in common.BAUTEIL_STATUS:
                    befunde.append(Befund(rel_name, nr, "fehler",
                                           f"status '{werte['status']}' ist nicht erlaubt"))
                for feld in ("laenge_mm", "breite_mm", "dicke_mm", "anzahl"):
                    wert = werte[feld]
                    if wert and not _ZAHL.match(wert.strip()):
                        befunde.append(Befund(rel_name, nr, "fehler",
                                               f"{feld} '{wert}' ist keine Zahl"))
                if werte["fuer_aufgabe"] and werte["fuer_aufgabe"] not in aufgaben_ids:
                    befunde.append(Befund(rel_name, nr, "warnung",
                                           f"fuer_aufgabe '{werte['fuer_aufgabe']}' zeigt auf keine bekannte Aufgabe"))
                if teil_ids is not None and werte["teil_id"] and werte["teil_id"] not in teil_ids:
                    befunde.append(Befund(rel_name, nr, "warnung",
                                           f"teil_id '{werte['teil_id']}' zeigt auf kein bekanntes Teil"))

    return befunde


# ------------------------------------------------------------------- Kern

def pruefen(bestand: Bestand | None = None) -> list[Befund]:
    """Alle Formatregeln aus FORMAT.md prüfen, Befunde mit Datei und Zeile."""
    if bestand is None:
        bestand = lesen.laden()

    befunde: list[Befund] = []

    # Bereichsdateien: Kopf, Abschnitte, Aufgabenzeilen.
    anker_je_datei: dict[str, list[tuple[str, int]]] = {}
    if common.BEREICHE_DIR.exists():
        for pfad in sorted(common.BEREICHE_DIR.glob("*.md")):
            text = common.read_text(pfad)
            zeilen = text.splitlines()
            rel = _rel(pfad, common.BEREICHE_DIR.parent.parent)

            befunde += _bereichskopf(rel, zeilen, pfad.stem)
            befunde += _abschnitte_pruefen(rel, text, common.BEREICH_ABSCHNITTE)

            aufgaben_befunde, anker_zeilen = _aufgaben_roh(rel, zeilen)
            befunde += aufgaben_befunde
            anker_je_datei[rel] = anker_zeilen

    befunde += _anker_eindeutig(anker_je_datei)
    befunde += _abhaengigkeiten(bestand)
    befunde += _querverweise(bestand)
    befunde += _seiten_struktur()

    aufgaben_ids = {a.id for a in bestand.aufgaben}
    entscheidung_titel = {s.titel for s in bestand.entscheidungen}
    teil_ids = {t.id for t in bestand.teile if t.id}

    befunde += _csv_pruefen(common.PARTS_CSV, "data/parts.csv", TEIL_FELDER,
                            aufgaben_ids, entscheidung_titel)
    befunde += _csv_pruefen(common.BAUTEILE_CSV, "data/bauteile.csv", EINZELTEIL_FELDER,
                            aufgaben_ids, entscheidung_titel, teil_ids=teil_ids)

    return befunde
