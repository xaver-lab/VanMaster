"""Schreiben in ``data/parts.csv`` und ``data/bauteile.csv``: Feld ändern,
Zeile anlegen, Zeile löschen (UMBAU.md Phase 2, „Schreiben CSV").

Fasst nur die betroffene Zeile an — die Kopfzeile und alle anderen Zeilen
bleiben bytegleich. Dafür wird die Datei zeilenweise behandelt statt mit
``csv.DictWriter`` komplett neu geschrieben: jede Datenzeile ist eine
CSV-Zeile ohne eingebettetes Newline (im Bestand unbelegt, siehe
FORMAT.md), eine neue/geänderte Zeile wird mit demselben Dialekt
(``QUOTE_MINIMAL``, wie ``tools/parts.py``/``tools/bauteile.py`` heute
schreiben) einzeln erzeugt und an ihrer Stelle eingesetzt.

Schreibt über ``kern.datei`` (Hash-Versionsschutz, ``datei.Konflikt`` bei
veralteter Version). Die Spaltenreihenfolge kommt aus ``kern.format``
(``TEIL_FELDER``/``EINZELTEIL_FELDER``) — einzige Stelle, die das Format
kennt.
"""
from __future__ import annotations

import csv
import io
import re

from .. import common
from . import datei
from .format import EINZELTEIL_FELDER, TEIL_FELDER


class Ungueltig(Exception):
    """Ein Feld, ein Wert oder eine Quelle ist nicht erlaubt."""


# ------------------------------------------------------------------- Prüfung

_ZAHL = re.compile(r"^-?\d+(\.\d+)?$")
_DATUM = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _zahl_pruefen(feld: str, wert: str) -> None:
    wert = wert.strip()
    if not wert:
        return
    if "," in wert:
        raise Ungueltig(
            f"{feld}: Dezimaltrennzeichen ist der Punkt, nicht das Komma "
            f"('{wert}') — Schreibweise wie im Bestand.")
    if not _ZAHL.match(wert):
        raise Ungueltig(f"{feld}: '{wert}' ist keine Zahl.")


def _datum_pruefen(feld: str, wert: str) -> None:
    wert = wert.strip()
    if not wert or _DATUM.match(wert):
        return
    raise Ungueltig(f"{feld}: '{wert}' ist kein Datum im Format JJJJ-MM-TT.")


def _teil_pruefen(feld: str, wert: str) -> None:
    if feld == "status" and wert not in common.PART_STATUS:
        raise Ungueltig(
            f"status muss einer von {', '.join(common.PART_STATUS)} sein, "
            f"nicht '{wert}'.")
    if feld == "prioritaet" and wert not in common.PART_PRIO:
        raise Ungueltig(
            f"prioritaet muss eine von {', '.join(common.PART_PRIO)} sein, "
            f"nicht '{wert}'.")
    if feld == "kategorie" and wert not in common.PART_KATEGORIEN:
        raise Ungueltig(
            f"kategorie muss eine von {', '.join(common.PART_KATEGORIEN)} "
            f"sein, nicht '{wert}'.")
    if feld in ("preis", "menge", "gewicht_kg"):
        _zahl_pruefen(feld, wert)
    if feld == "gekauft_am":
        _datum_pruefen(feld, wert)


def _einzelteil_pruefen(feld: str, wert: str) -> None:
    if feld == "status" and wert not in common.BAUTEIL_STATUS:
        raise Ungueltig(
            f"status muss einer von {', '.join(common.BAUTEIL_STATUS)} "
            f"sein, nicht '{wert}'.")
    if feld == "art" and wert not in common.BAUTEIL_ART:
        raise Ungueltig(
            f"art muss eine von {', '.join(common.BAUTEIL_ART)} sein, "
            f"nicht '{wert}'.")
    if feld == "massquelle" and wert not in common.MASSQUELLE:
        raise Ungueltig(
            f"massquelle muss eine von {', '.join(common.MASSQUELLE)} "
            f"sein, nicht '{wert}'.")
    if feld in ("laenge_mm", "breite_mm", "dicke_mm", "anzahl"):
        _zahl_pruefen(feld, wert)


# Web-bearbeitbare Felder, FORMAT.md §8/§10. `id` ist in keinem Fall
# änderbar, auch nicht über `quelle="claude"`.
_TEIL_WEB_FELDER = {
    "titel", "status", "prioritaet", "kategorie",
    "preis", "menge", "notiz", "link", "haendler", "gekauft_am",
}


def _web_erlaubt_teil(feld: str) -> bool:
    return feld in _TEIL_WEB_FELDER


def _web_erlaubt_einzelteil(feld: str) -> bool:
    # Einzelteile sind laut UMBAU.md im Web pauschal bearbeitbar außer id.
    return feld != "id"


# --------------------------------------------------------------- Zeilen-I/O
#
# Eine Datenzeile ist genau eine Zeile Text (kein eingebettetes Newline in
# einem Feld — im Bestand unbelegt). So lässt sich eine einzelne Zeile
# ersetzen, ohne die Datei komplett neu zu schreiben.

def _kopf_und_zeilen(text: str) -> tuple[str, list[str]]:
    zeilen = text.split("\n")
    if zeilen and zeilen[-1] == "":
        zeilen = zeilen[:-1]
    if not zeilen:
        return "", []
    return zeilen[0], zeilen[1:]


def _text_zusammenbauen(kopf: str, zeilen: list[str]) -> str:
    return "\n".join([kopf] + zeilen) + "\n"


def _werte_aus_zeile(zeile: str, felder: list[str]) -> dict:
    roh = next(csv.reader([zeile]))
    roh += [""] * (len(felder) - len(roh))
    return dict(zip(felder, roh))


def _zeile_aus_werten(werte: dict, felder: list[str]) -> str:
    puffer = io.StringIO()
    csv.writer(puffer, lineterminator="").writerow(
        [werte.get(f, "") for f in felder])
    return puffer.getvalue()


def _zeile_finden(zeilen: list[str], felder: list[str], id_: str) -> tuple[int, dict] | None:
    ziel = id_.strip().lower()
    for i, zeile in enumerate(zeilen):
        if not zeile.strip():
            continue
        werte = _werte_aus_zeile(zeile, felder)
        if werte.get("id", "").strip().lower() == ziel:
            return i, werte
    return None


def _alle_ids(zeilen: list[str], felder: list[str]) -> set[str]:
    return {_werte_aus_zeile(z, felder).get("id", "")
            for z in zeilen if z.strip()}


# --------------------------------------------------------------- Schreiben

def _feld_setzen(pfad, felder: list[str], id_: str, feld: str, wert: str,
                 version: str, quelle: str, pruefen, web_erlaubt) -> str:
    if feld == "id":
        raise Ungueltig("id ist nie änderbar.")
    if feld not in felder:
        raise Ungueltig(f"Unbekanntes Feld '{feld}'.")
    if quelle == "web" and not web_erlaubt(feld):
        raise Ungueltig(f"'{feld}' ist über die Quelle 'web' nicht bearbeitbar.")
    pruefen(feld, wert)

    text, _ = datei.lesen(pfad)
    kopf, zeilen = _kopf_und_zeilen(text)
    treffer = _zeile_finden(zeilen, felder, id_)
    if treffer is None:
        raise Ungueltig(f"Keine Zeile mit id '{id_}'.")
    i, werte = treffer
    werte[feld] = wert
    zeilen[i] = _zeile_aus_werten(werte, felder)
    return datei.schreiben(pfad, _text_zusammenbauen(kopf, zeilen), version)


def _anlegen(pfad, felder: list[str], standard: dict, pflicht: list[str],
            pruefen, web_erlaubt, eingabe: dict, version: str,
            quelle: str) -> tuple[str, str]:
    unbekannt = [f for f in eingabe if f == "id" or f not in felder]
    if unbekannt:
        raise Ungueltig(f"Unbekanntes Feld: {', '.join(unbekannt)}.")
    if quelle == "web":
        verboten = [f for f in eingabe if not web_erlaubt(f)]
        if verboten:
            raise Ungueltig(
                f"Über die Quelle 'web' nicht anlegbar: {', '.join(verboten)}.")
    for f in pflicht:
        if not str(eingabe.get(f, "")).strip():
            raise Ungueltig(f"'{f}' ist beim Anlegen Pflicht.")
    for f, wert in eingabe.items():
        pruefen(f, str(wert))

    text, _ = datei.lesen(pfad)
    kopf, zeilen = _kopf_und_zeilen(text)
    vorhandene = _alle_ids(zeilen, felder)
    basis = common.slug(str(eingabe.get("titel", ""))) or "eintrag"
    neue_id = basis
    i = 2
    while neue_id in vorhandene:
        neue_id = f"{basis}-{i}"
        i += 1

    werte = dict(standard)
    werte.update({f: str(w) for f, w in eingabe.items()})
    werte["id"] = neue_id
    zeilen.append(_zeile_aus_werten(werte, felder))
    neuer_hash = datei.schreiben(pfad, _text_zusammenbauen(kopf, zeilen), version)
    return neue_id, neuer_hash


def _loeschen(pfad, felder: list[str], id_: str, version: str) -> str:
    text, _ = datei.lesen(pfad)
    kopf, zeilen = _kopf_und_zeilen(text)
    treffer = _zeile_finden(zeilen, felder, id_)
    if treffer is None:
        raise Ungueltig(f"Keine Zeile mit id '{id_}'.")
    i, _ = treffer
    del zeilen[i]
    return datei.schreiben(pfad, _text_zusammenbauen(kopf, zeilen), version)


# --------------------------------------------------------------------- Teile

_TEIL_STANDARD = {
    "einheit": "Stk", "menge": "1", "status": "Idee", "prioritaet": "Mittel",
}
_TEIL_PFLICHT = ["titel", "kategorie"]


def teil_feld_setzen(id_: str, feld: str, wert: str, version: str,
                     quelle: str = "web") -> str:
    return _feld_setzen(common.PARTS_CSV, TEIL_FELDER, id_, feld, wert,
                        version, quelle, _teil_pruefen, _web_erlaubt_teil)


def teil_anlegen(felder: dict, version: str, quelle: str = "web") -> tuple[str, str]:
    return _anlegen(common.PARTS_CSV, TEIL_FELDER, _TEIL_STANDARD,
                    _TEIL_PFLICHT, _teil_pruefen, _web_erlaubt_teil,
                    felder, version, quelle)


def teil_loeschen(id_: str, version: str) -> str:
    return _loeschen(common.PARTS_CSV, TEIL_FELDER, id_, version)


# -------------------------------------------------------------- Einzelteile

_EINZELTEIL_STANDARD = {
    "art": "Sonstiges", "anzahl": "1", "status": "Idee",
    "massquelle": "geschaetzt",
}
_EINZELTEIL_PFLICHT = ["titel", "bereich"]


def einzelteil_feld_setzen(id_: str, feld: str, wert: str, version: str,
                           quelle: str = "web") -> str:
    return _feld_setzen(common.BAUTEILE_CSV, EINZELTEIL_FELDER, id_, feld,
                        wert, version, quelle, _einzelteil_pruefen,
                        _web_erlaubt_einzelteil)


def einzelteil_anlegen(felder: dict, version: str,
                       quelle: str = "web") -> tuple[str, str]:
    return _anlegen(common.BAUTEILE_CSV, EINZELTEIL_FELDER,
                    _EINZELTEIL_STANDARD, _EINZELTEIL_PFLICHT,
                    _einzelteil_pruefen, _web_erlaubt_einzelteil,
                    felder, version, quelle)


def einzelteil_loeschen(id_: str, version: str) -> str:
    return _loeschen(common.BAUTEILE_CSV, EINZELTEIL_FELDER, id_, version)
