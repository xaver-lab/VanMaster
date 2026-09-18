"""Format-Grammatik: Aufgabenzeile, Bereichskopf, CSV-Spalten.

Einzige Stelle, die das Format kennt (FORMAT.md, UMBAU.md Phase 2). Die
alten Module (tools/tasks.py, tools/bereiche.py, tools/parts.py,
tools/bauteile.py) beziehen ihre Grammatik-Konstanten von hier — sie
fallen in Phase 9 weg, der Kern bleibt. Hängt selbst nur von der
Standardbibliothek ab, nicht von den alten Modulen.
"""
from __future__ import annotations

import re

# --------------------------------------------------------------- Aufgabenzeile

BOX = {" ": "offen", "/": "laeuft", "x": "erledigt", "X": "erledigt",
       "-": "verworfen", "!": "blockiert"}
BOX_ZEICHEN = {"offen": " ", "laeuft": "/", "erledigt": "x",
              "verworfen": "-", "blockiert": "!"}
ERLEDIGT = ("erledigt", "verworfen")

PRIOS = {"kritisch": 0, "hoch": 1, "mittel": 2, "nice": 3}

ZEILE = re.compile(r"^(?P<einzug>[ \t]*)- \[(?P<box>[ xX/\-!])\] (?P<rest>.*)$")
BESCHREIBUNG = re.compile(r"^[ \t]+>\s?(?P<text>.*)$")
ANKER = re.compile(r"(?:^|\s)\^([A-Za-z0-9\-_]+)")
PRIO = re.compile(r"(?:^|\s)#(kritisch|hoch|mittel|nice)\b", re.I)
MARKE = re.compile(r"(?:^|\s)@(braucht|dauer):([^\s]+)")


def ebene(einzug: str) -> int:
    return (einzug.replace("\t", "  ").count(" ")) // 2


# ----------------------------------------------------------------- Bereichskopf

LEER = re.compile(r"^_\(.*\)_$")

# - [Titel](url) — Zusatz   ·   der Zusatz ist freiwillig
LINK = re.compile(r"^\s*-\s*\[(?P<titel>[^\]]+)\]\((?P<url>[^)]+)\)\s*(?:[—-]\s*(?P<zusatz>.*))?$")


def phase(wert) -> int | None:
    """`phase: 2` aus dem Kopf — alles Unbrauchbare zählt als nicht gesetzt."""
    try:
        return int(str(wert).strip())
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- CSV

TEIL_FELDER = [
    "id", "titel", "beschreibung", "kategorie",
    "menge", "einheit", "preis", "status", "prioritaet",
    "link", "haendler", "fuer_aufgabe", "entscheidung",
    "kennwerte", "gewicht_kg", "notiz", "gekauft_am",
]
TEIL_BERECHNET = ["gesamt"]

EINZELTEIL_FELDER = [
    "id", "titel", "bereich", "art", "material",
    "laenge_mm", "breite_mm", "dicke_mm", "anzahl",
    "teil_id", "fuer_aufgabe", "massquelle", "status", "notiz",
]
EINZELTEIL_BERECHNET = ["flaeche_m2", "laufmeter"]
