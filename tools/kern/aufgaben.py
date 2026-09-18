"""Schreibt Aufgaben in Bereichsdateien: anlegen, Status/Titel/Beschreibung/
Priorität ändern, löschen — nach FORMAT.md Abschnitt 3.

Jede Funktion sucht die betroffene Aufgabe über ``lesen.aufgaben_lesen()``
(IDs sind global eindeutig), liest genau die eine Bereichsdatei über
``datei.lesen`` und schreibt sie über ``datei.schreiben`` zurück — dort
entsteht bei veraltetem ``version``-Hash ein ``datei.Konflikt``. Geändert
werden nur die betroffenen Zeilen; Zeilenende und Einzug der Datei bleiben
erhalten (``datei.zeilenende``).
"""
from __future__ import annotations

from .. import common
from . import datei
from .format import ANKER, BOX_ZEICHEN, MARKE, PRIO, PRIOS, ZEILE
from .lesen import aufgaben_lesen


# --------------------------------------------------------------- Werkzeug

def _terminator(zeile: str) -> tuple[str, str]:
    """Zerlegt eine Zeile (mit Endezeichen) in Inhalt und Endezeichen."""
    for t in ("\r\n", "\n", "\r"):
        if zeile.endswith(t):
            return zeile[: -len(t)], t
    return zeile, ""


def _einfuegen(zeilen: list[str], eol: str, idx: int, inhalte: list[str]) -> None:
    """Fügt `inhalte` (ohne Endezeichen) an Position `idx` ein, mit `eol`."""
    if not inhalte:
        return
    if idx == len(zeilen) and zeilen:
        letzter_inhalt, term = _terminator(zeilen[-1])
        if not term:
            zeilen[-1] = letzter_inhalt + eol
    zeilen[idx:idx] = [z + eol for z in inhalte]


def _finde(aufgabe_id: str):
    for a in aufgaben_lesen():
        if a.id == aufgabe_id:
            return a
    raise ValueError(f"Aufgabe '{aufgabe_id}' nicht gefunden")


def _einzug_von_zeile(zeile: str) -> str:
    treffer = ZEILE.match(_terminator(zeile)[0])
    return treffer.group("einzug") if treffer else ""


def _erste_marke_start(rest: str) -> int:
    """Position der am weitesten links stehenden Marke (^id/#prio/@…) in `rest`."""
    positionen = [m.start() for m in ANKER.finditer(rest)]
    positionen += [m.start() for m in PRIO.finditer(rest)]
    positionen += [m.start() for m in MARKE.finditer(rest)]
    return min(positionen) if positionen else len(rest)


def _aufgaben_abschnitt(zeilen: list[str]) -> tuple[int, int]:
    """0-indexierte (start, ende)-Grenze von ``## Aufgaben`` (Ende exklusiv)."""
    start = None
    ende = len(zeilen)
    for i, roh in enumerate(zeilen):
        zeile = _terminator(roh)[0]
        if zeile.startswith("## ") and not zeile.startswith("### "):
            if start is not None:
                ende = i
                break
            if zeile[3:].strip().lower() == "aufgaben":
                start = i + 1
    if start is None:
        raise ValueError("Datei hat keinen Abschnitt '## Aufgaben'")
    return start, ende


def _gruppe_ende(zeilen: list[str], start: int, ende: int, gruppe: str) -> int:
    """0-indexiertes Ende (exklusiv) der Gruppe `gruppe` innerhalb [start, ende)."""
    gruppe_start = None
    gruppe_ende_ = ende
    for i in range(start, ende):
        zeile = _terminator(zeilen[i])[0]
        if zeile.startswith("#"):
            if gruppe_start is not None:
                gruppe_ende_ = i
                break
            if zeile.lstrip("#").strip() == gruppe:
                gruppe_start = i + 1
    if gruppe_start is None:
        raise ValueError(f"Gruppe '{gruppe}' nicht gefunden")
    return gruppe_ende_


# ------------------------------------------------------------------ anlegen

def anlegen(bereich: str, titel: str, version: str | None, *,
            status: str = "offen", beschreibung: str = "", prio: str = "",
            gruppe: str | None = None, eltern_id: str | None = None,
            ) -> tuple[str, str]:
    """Legt eine neue Aufgabe in `bereich` an, ans Ende von Abschnitt/Gruppe/
    Elternaufgabe. Liefert (neue_id, neuer_hash)."""
    if status not in BOX_ZEICHEN:
        raise ValueError(f"unbekannter Status: {status}")
    prio = (prio or "").strip().lower()
    if prio and prio not in PRIOS:
        raise ValueError(f"unbekannte Priorität: {prio}")
    if gruppe and eltern_id:
        raise ValueError("Gruppe und Eltern-Aufgabe schließen sich aus")

    pfad = common.BEREICHE_DIR / f"{bereich}.md"
    if not pfad.exists():
        raise ValueError(f"Bereich '{bereich}' nicht gefunden")
    rel = datei.rel(pfad)

    vorhandene = aufgaben_lesen()
    vorhandene_ids = {a.id for a in vorhandene}
    basis = common.slug(titel) or "aufgabe"
    kennung = basis
    i = 2
    while kennung in vorhandene_ids:
        kennung = f"{basis}-{i}"
        i += 1

    text, _ = datei.lesen(pfad)
    eol = datei.zeilenende(text)
    zeilen = text.splitlines(keepends=True)

    if eltern_id:
        eltern = next((a for a in vorhandene if a.id == eltern_id), None)
        if eltern is None:
            raise ValueError(f"Eltern-Aufgabe '{eltern_id}' nicht gefunden")
        if eltern.datei != rel:
            raise ValueError("Eltern-Aufgabe liegt in einem anderen Bereich")
        einzug = _einzug_von_zeile(zeilen[eltern.zeile - 1]) + "  "
        einfuege_idx = eltern.block_bis
    else:
        start, ende = _aufgaben_abschnitt(zeilen)
        einfuege_idx = _gruppe_ende(zeilen, start, ende, gruppe) if gruppe else ende
        einzug = ""

    box = BOX_ZEICHEN[status]
    kopf = f"{einzug}- [{box}] {titel.strip()} ^{kennung}"
    if prio:
        kopf += f" #{prio}"
    inhalte = [kopf]

    beschreibung_klar = beschreibung.strip()
    if beschreibung_klar:
        besch_einzug = einzug + "  "
        for z in beschreibung_klar.split("\n"):
            inhalte.append(f"{besch_einzug}> {z}" if z else f"{besch_einzug}>")

    _einfuegen(zeilen, eol, einfuege_idx, inhalte)
    neuer_hash = datei.schreiben(pfad, "".join(zeilen), version)
    return kennung, neuer_hash


# -------------------------------------------------------------- Änderungen

def status_setzen(aufgabe_id: str, status: str, version: str | None) -> str:
    if status not in BOX_ZEICHEN:
        raise ValueError(f"unbekannter Status: {status}")
    a = _finde(aufgabe_id)
    pfad = datei.pfad(a.datei)
    text, _ = datei.lesen(pfad)
    zeilen = text.splitlines(keepends=True)
    inhalt, term = _terminator(zeilen[a.zeile - 1])
    treffer = ZEILE.match(inhalt)
    if not treffer:
        raise ValueError(f"Zeile {a.zeile} in {a.datei} ist keine Aufgabenzeile")
    neu = (inhalt[: treffer.start("box")] + BOX_ZEICHEN[status]
           + inhalt[treffer.end("box"):])
    zeilen[a.zeile - 1] = neu + term
    return datei.schreiben(pfad, "".join(zeilen), version)


def titel_setzen(aufgabe_id: str, titel: str, version: str | None) -> str:
    a = _finde(aufgabe_id)
    pfad = datei.pfad(a.datei)
    text, _ = datei.lesen(pfad)
    zeilen = text.splitlines(keepends=True)
    inhalt, term = _terminator(zeilen[a.zeile - 1])
    treffer = ZEILE.match(inhalt)
    if not treffer:
        raise ValueError(f"Zeile {a.zeile} in {a.datei} ist keine Aufgabenzeile")
    rest = treffer.group("rest")
    start = _erste_marke_start(rest)
    neuer_rest = titel.strip() + rest[start:]
    neue_zeile = inhalt[: treffer.start("rest")] + neuer_rest
    zeilen[a.zeile - 1] = neue_zeile + term
    return datei.schreiben(pfad, "".join(zeilen), version)


def beschreibung_setzen(aufgabe_id: str, beschreibung: str, version: str | None) -> str:
    """Leerer Text entfernt die Beschreibung. Mehrzeilig als `> `-Zeilen mit
    Einzug der Aufgabenzeile + 2 Leerzeichen."""
    a = _finde(aufgabe_id)
    pfad = datei.pfad(a.datei)
    text, _ = datei.lesen(pfad)
    eol = datei.zeilenende(text)
    zeilen = text.splitlines(keepends=True)

    einzug = _einzug_von_zeile(zeilen[a.zeile - 1]) + "  "
    beschreibung_klar = beschreibung.strip()
    neue_zeilen = []
    if beschreibung_klar:
        for z in beschreibung_klar.split("\n"):
            neue_zeilen.append(f"{einzug}> {z}" if z else f"{einzug}>")

    if a.beschreibung_von is not None:
        einfuege_idx = a.beschreibung_von - 1
        del zeilen[einfuege_idx: a.beschreibung_bis]
    else:
        einfuege_idx = a.zeile

    _einfuegen(zeilen, eol, einfuege_idx, neue_zeilen)
    return datei.schreiben(pfad, "".join(zeilen), version)


def prio_setzen(aufgabe_id: str, prio: str, version: str | None) -> str:
    """Leerer Text entfernt die Priorität."""
    prio = (prio or "").strip().lower()
    if prio and prio not in PRIOS:
        raise ValueError(f"unbekannte Priorität: {prio}")
    a = _finde(aufgabe_id)
    pfad = datei.pfad(a.datei)
    text, _ = datei.lesen(pfad)
    zeilen = text.splitlines(keepends=True)
    inhalt, term = _terminator(zeilen[a.zeile - 1])
    treffer = ZEILE.match(inhalt)
    if not treffer:
        raise ValueError(f"Zeile {a.zeile} in {a.datei} ist keine Aufgabenzeile")
    rest = treffer.group("rest")
    bestehend = PRIO.search(rest)

    if prio:
        if bestehend:
            neuer_rest = rest[: bestehend.start(1)] + prio + rest[bestehend.end(1):]
        else:
            neuer_rest = rest.rstrip() + f" #{prio}"
    else:
        neuer_rest = rest[: bestehend.start()] + rest[bestehend.end():] if bestehend else rest

    neue_zeile = inhalt[: treffer.start("rest")] + neuer_rest
    zeilen[a.zeile - 1] = neue_zeile + term
    return datei.schreiben(pfad, "".join(zeilen), version)


def loeschen(aufgabe_id: str, version: str | None) -> str:
    """Entfernt die Aufgabenzeile, ihre Beschreibung und alle Unterpunkte."""
    a = _finde(aufgabe_id)
    pfad = datei.pfad(a.datei)
    text, _ = datei.lesen(pfad)
    zeilen = text.splitlines(keepends=True)
    del zeilen[a.zeile - 1: a.block_bis]
    return datei.schreiben(pfad, "".join(zeilen), version)
