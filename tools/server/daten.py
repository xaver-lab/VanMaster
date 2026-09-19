"""``daten_json()`` — derselbe Bestand wie ``GET /api/daten``, als reines
Dict. Getrennt von ``app.py``, damit ihn später auch die GitHub Action
(statisches ``data.json`` für den Lesemodus, UMBAU.md Phase 9) ohne FastAPI
aufrufen kann.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .. import ablauf as ablauf_mod
from .. import budget as budget_mod
from .. import build, common
from .. import gewicht as gewicht_mod
from .. import parts
from .. import material as material_mod
from ..common import STANDARD_SORTIERUNG
from ..kern import abschnitte as kern_abschnitte
from ..kern import datei as kern_datei
from ..kern import laden
from ..kern.format import EINZELTEIL_FELDER, TEIL_FELDER


def _bereich_abschnitte_matrix() -> dict[str, dict[str, bool]]:
    web = kern_abschnitte._WEB_ABSCHNITTE
    claude_zusatz = kern_abschnitte._CLAUDE_ZUSATZ_ABSCHNITTE
    matrix: dict[str, dict[str, bool]] = {}
    for name in common.BEREICH_ABSCHNITTE:
        if name in kern_abschnitte._NIE:
            matrix[name] = {"web": False, "claude": False}
        else:
            matrix[name] = {
                "web": name in web,
                "claude": name in web or name in claude_zusatz,
            }
    return matrix


def _bereich_kopf_matrix() -> dict[str, dict[str, bool]]:
    web = kern_abschnitte._WEB_FELDER
    claude = kern_abschnitte._CLAUDE_FELDER
    return {feld: {"web": feld in web, "claude": True}
            for feld in sorted(web | claude)}


def _bearbeitbar() -> dict[str, Any]:
    """Matrix bearbeitbar (web) / nur Claude — FORMAT.md §8/§10, als Daten
    für die Oberfläche. Die Durchsetzung bleibt im Kern (``kern.abschnitte``,
    ``kern.tabellen``); hier steht nur, was die Matrix erlaubt."""
    return {
        "bereich_abschnitte": _bereich_abschnitte_matrix(),
        "bereich_kopf": _bereich_kopf_matrix(),
        "aufgaben": {
            "web": True, "claude": True,
            "felder": ["status", "titel", "beschreibung", "prio"],
            "anlegen": True, "loeschen": True,
        },
        "teil_felder": {
            feld: {"web": feld in _TEIL_WEB_FELDER, "claude": feld != "id"}
            for feld in TEIL_FELDER
        },
        "teil_anlegen": True,
        "teil_loeschen": True,
        "einzelteil_felder": {
            feld: {"web": feld != "id", "claude": feld != "id"}
            for feld in EINZELTEIL_FELDER
        },
        "einzelteil_anlegen": True,
        "einzelteil_loeschen": True,
        "nur_claude_seiten": ["entscheidungen", "anleitungen", "recherche"],
    }


# Web-editierbare Teile-Felder — dieselbe Liste wie ``kern.tabellen``
# (dort privat, hier für die Matrix-Ausgabe gespiegelt statt importiert,
# damit ``daten.py`` nicht von Kern-internen Namen abhängt).
_TEIL_WEB_FELDER = {
    "titel", "status", "prioritaet", "kategorie",
    "preis", "menge", "notiz", "link", "haendler", "gekauft_am",
}


def _vokabular() -> dict[str, list[str]]:
    """Erlaubte Werte der Auswahlfelder aus ``common`` — die Oberfläche
    verdrahtet sie nicht selbst."""
    return {
        "teil_status": common.PART_STATUS,
        "teil_prio": common.PART_PRIO,
        "teil_kategorien": common.PART_KATEGORIEN,
        "einzelteil_art": common.BAUTEIL_ART,
        "einzelteil_status": common.BAUTEIL_STATUS,
        "massquelle": common.MASSQUELLE,
    }


def _versionen(bestand) -> dict[str, str]:
    versionen: dict[str, str] = {}
    for b in bestand.bereiche:
        if b.datei:
            versionen[b.datei] = kern_datei.version(kern_datei.pfad(b.datei))
    for seite in bestand.entscheidungen + bestand.anleitungen + bestand.recherche:
        if seite.datei:
            versionen[seite.datei] = kern_datei.version(kern_datei.pfad(seite.datei))
    versionen[kern_datei.rel(common.PARTS_CSV)] = kern_datei.version(common.PARTS_CSV)
    versionen[kern_datei.rel(common.BAUTEILE_CSV)] = kern_datei.version(common.BAUTEILE_CSV)
    return versionen


def _material() -> list[dict]:
    """``camper material``, aber ohne die vollen Zuschnitt-Sätze: die stehen
    schon unter ``einzelteile``, hier reichen ihre IDs."""
    return [{"material": g["material"], "dicke_mm": g["dicke_mm"],
             "bedarf": g["bedarf"],
             "zuschnitte": [r.get("id", "") for r in g["zuschnitte"]]}
            for g in material_mod.liste()]


def daten_json(sortierung: str = STANDARD_SORTIERUNG) -> dict:
    """Kompletter Bestand — dieselbe Struktur wie ``GET /api/daten``."""
    bestand = laden()

    # Kennzahlen und Kategorien: dieselbe Logik wie `python camper.py status
    # --json` (tools/build.py:daten() → "kennzahlen"/"kategorien", das auf
    # tools/status.py und tasks/parts/bauteile aufsetzt) — hier
    # wiederverwendet, nicht neu gerechnet.
    bau = build.daten(sortierung)

    return {
        "erzeugt": datetime.now().isoformat(timespec="minutes"),
        "bereiche": bestand.bereiche,
        "aufgaben": bestand.aufgaben,
        "querverweise": bestand.querverweise,
        "entscheidungen": bestand.entscheidungen,
        "anleitungen": bestand.anleitungen,
        "recherche": bestand.recherche,
        "teile": bestand.teile,
        "einzelteile": bestand.einzelteile,
        "medien": bestand.medien,
        "versionen": _versionen(bestand),
        "kennzahlen": bau["kennzahlen"],
        "kategorien": bau["kategorien"],
        "budget": budget_mod.daten(),
        "gewicht": gewicht_mod.bilanz(),
        "material": _material(),
        "einkauf": parts.buy_daten(),
        "ablauf": ablauf_mod.plan(sortierung=sortierung),
        "bearbeitbar": _bearbeitbar(),
        "vokabular": _vokabular(),
    }
