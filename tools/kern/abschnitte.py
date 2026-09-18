"""Schreiben von Bereichsabschnitten und Kopf-Feldern (FORMAT.md §2, §8, §10).

Ersetzt nur den Rumpf eines ``## <Name>``-Abschnitts bzw. eine einzelne
Kopfzeile einer Bereichsdatei — alle anderen Zeilen der Datei bleiben
unverändert. Schreibt über ``tools.kern.datei`` mit Versionsschutz.

``## Aufgaben`` wird hier nie geschrieben (eigene Funktionen, FORMAT.md §2/§8).
"""
from __future__ import annotations

from .. import common
from . import datei
from .lesen import abschnitte_mit_zeilen


class Unerlaubt(Exception):
    """Ein Abschnitt/Kopf-Feld darf mit der gegebenen Quelle nicht geschrieben
    werden (FORMAT.md §8 Matrix, §10)."""


# Abschnitte, die mit quelle="web" geschrieben werden dürfen.
_WEB_ABSCHNITTE = {"Beschreibung", "Stand", "Notizen", "Links"}
# Zusätzlich mit quelle="claude" erlaubt.
_CLAUDE_ZUSATZ_ABSCHNITTE = {"Auslegung"}
# Nie über abschnitt_setzen — eigene Funktionen (FORMAT.md §2).
_NIE = {"Aufgaben"}

_WEB_FELDER = {"kurz", "status"}
_CLAUDE_FELDER = {"phase", "bereich"}


def _bereichsdatei(bereich: str):
    return common.BEREICHE_DIR / f"{bereich}.md"


def _quelle_pruefen(quelle: str) -> None:
    if quelle not in ("web", "claude"):
        raise Unerlaubt(f"Unbekannte Quelle '{quelle}' — erlaubt sind 'web', 'claude'.")


def _abschnitt_pruefen(name: str, quelle: str) -> None:
    _quelle_pruefen(quelle)
    if name in _NIE:
        raise Unerlaubt(
            f"Abschnitt '{name}' wird nicht über abschnitt_setzen geschrieben "
            "— dafür gibt es eigene Funktionen (FORMAT.md §2).")
    if name not in common.BEREICH_ABSCHNITTE:
        raise Unerlaubt(
            f"Unbekannter Abschnitt '{name}' — erlaubt sind {common.BEREICH_ABSCHNITTE}.")
    erlaubt = _WEB_ABSCHNITTE | (_CLAUDE_ZUSATZ_ABSCHNITTE if quelle == "claude" else set())
    if name not in erlaubt:
        raise Unerlaubt(
            f"Abschnitt '{name}' ist mit quelle='{quelle}' nicht schreibbar "
            "(FORMAT.md §8 Matrix).")


def _kopf_pruefen(feld: str, wert, quelle: str) -> None:
    _quelle_pruefen(quelle)
    if feld not in (_WEB_FELDER | _CLAUDE_FELDER):
        raise Unerlaubt(
            f"Unbekanntes Kopf-Feld '{feld}' — erlaubt sind "
            f"{sorted(_WEB_FELDER | _CLAUDE_FELDER)}.")
    if feld in _CLAUDE_FELDER and quelle != "claude":
        raise Unerlaubt(
            f"Kopf-Feld '{feld}' ist nur für Claude schreibbar "
            "(FORMAT.md §8 Matrix).")
    if feld == "status" and str(wert) not in common.BEREICH_STATUS:
        raise Unerlaubt(
            f"Status '{wert}' ist ungültig — erlaubt sind {common.BEREICH_STATUS}.")


def _rumpf_zeilen(text: str, hat_folgezeile: bool) -> list[str]:
    """Baut die Rumpf-Zeilen eines Abschnitts: Leerzeile, Inhalt, ggf.
    Leerzeile vor dem, was folgt — wie im Bestand üblich."""
    inhalt = text.strip()
    zeilen = [""] + (inhalt.splitlines() if inhalt else [])
    if hat_folgezeile:
        zeilen.append("")
    return zeilen


def _einfuegeposition(zeilen: list[str], name: str,
                       abschnitte: dict) -> int:
    """0-indexierte Position, an der ein fehlender Abschnitt eingefügt wird
    — vor dem nächsten vorhandenen Abschnitt der festen Reihenfolge, sonst
    nach dem letzten vorhandenen davor."""
    reihenfolge = common.BEREICH_ABSCHNITTE
    i = reihenfolge.index(name)
    for kandidat in reihenfolge[i + 1:]:
        if kandidat in abschnitte:
            return abschnitte[kandidat].zeile_von - 1
    for kandidat in reversed(reihenfolge[:i]):
        if kandidat in abschnitte:
            return abschnitte[kandidat].zeile_bis
    if "" in abschnitte:
        return abschnitte[""].zeile_bis
    return len(zeilen)


def _text_schreiben(zeilen: list[str], le: str, endet_mit_nl: bool) -> str:
    neuer_text = le.join(zeilen)
    if endet_mit_nl:
        neuer_text += le
    return neuer_text


def abschnitt_setzen(bereich: str, name: str, text: str, version: str,
                      quelle: str = "web") -> str:
    """Ersetzt den Rumpf von ``## <name>`` in der Bereichsdatei `bereich`
    (bzw. fügt ihn an der richtigen Stelle neu ein). Nur die betroffenen
    Zeilen ändern sich. Liefert den neuen Datei-Hash."""
    _abschnitt_pruefen(name, quelle)
    pfad = _bereichsdatei(bereich)
    inhalt, _ = datei.lesen(pfad)
    le = datei.zeilenende(inhalt)
    endet_mit_nl = inhalt.endswith("\n")
    zeilen = inhalt.splitlines()
    abschnitte = abschnitte_mit_zeilen(inhalt)

    if name in abschnitte:
        a = abschnitte[name]
        anfang = a.zeile_von  # 0-indexiert: erste Zeile nach der Überschrift
        ende = a.zeile_bis    # 0-indexiert, exklusiv (= letzte Zeile des Abschnitts)
        neuer_rumpf = _rumpf_zeilen(text, hat_folgezeile=ende < len(zeilen))
        zeilen[anfang:ende] = neuer_rumpf
    else:
        pos = _einfuegeposition(zeilen, name, abschnitte)
        neue_zeilen = [f"## {name}"] + _rumpf_zeilen(
            text, hat_folgezeile=pos < len(zeilen))
        zeilen[pos:pos] = neue_zeilen

    neuer_text = _text_schreiben(zeilen, le, endet_mit_nl)
    return datei.schreiben(pfad, neuer_text, version)


def kopf_setzen(bereich: str, feld: str, wert, version: str,
                 quelle: str = "web") -> str:
    """Ändert genau eine Kopfzeile (``feld: wert``) der Bereichsdatei
    `bereich`. Liefert den neuen Datei-Hash."""
    _kopf_pruefen(feld, wert, quelle)
    pfad = _bereichsdatei(bereich)
    inhalt, _ = datei.lesen(pfad)
    le = datei.zeilenende(inhalt)
    endet_mit_nl = inhalt.endswith("\n")
    zeilen = inhalt.splitlines()

    if not zeilen or zeilen[0].strip() != "---":
        raise Unerlaubt(f"'{bereich}.md' hat keinen YAML-Kopf.")
    ende = None
    for i in range(1, len(zeilen)):
        if zeilen[i].strip() == "---":
            ende = i
            break
    if ende is None:
        raise Unerlaubt(f"'{bereich}.md': YAML-Kopf nicht geschlossen (kein zweites '---').")

    zeile_index = None
    for i in range(1, ende):
        schluessel = zeilen[i].split(":", 1)[0].strip() if ":" in zeilen[i] else None
        if schluessel == feld:
            zeile_index = i
            break
    if zeile_index is None:
        raise Unerlaubt(f"Kopf-Feld '{feld}' existiert nicht in '{bereich}.md'.")

    zeilen[zeile_index] = f"{feld}: {wert}"
    neuer_text = _text_schreiben(zeilen, le, endet_mit_nl)
    return datei.schreiben(pfad, neuer_text, version)
