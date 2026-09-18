"""Dateizugriff mit Versionsschutz.

Jede Datei hat einen Hash über ihre Bytes. Wer schreibt, gibt den Hash mit,
den er beim Lesen gesehen hat. Hat sich die Datei inzwischen geändert (Claude,
anderer Browser-Tab, Hand), wird das Schreiben abgelehnt.

Texte werden ohne Zeilenende-Umwandlung gelesen und geschrieben, damit ein
Rundlauf bytegleich bleibt.
"""
from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

from .. import common

_SPERRE = threading.Lock()


class Konflikt(Exception):
    """Die Datei hat sich seit dem Lesen geändert."""

    def __init__(self, pfad: Path, erwartet: str, aktuell: str):
        super().__init__(f"{rel(pfad)} wurde inzwischen geändert")
        self.pfad = pfad
        self.erwartet = erwartet
        self.aktuell = aktuell


def rel(pfad: Path) -> str:
    """Pfad relativ zur Repo-Wurzel, mit `/`."""
    return Path(pfad).resolve().relative_to(common.ROOT.resolve()).as_posix()


def pfad(relativ: str) -> Path:
    """Umkehrung von `rel`."""
    return common.ROOT / relativ


def hash_von(daten: bytes) -> str:
    return hashlib.sha256(daten).hexdigest()[:16]


def version(pfad: Path) -> str:
    """Aktueller Hash der Datei; leerer Text, wenn es sie nicht gibt."""
    try:
        return hash_von(Path(pfad).read_bytes())
    except FileNotFoundError:
        return ""


def lesen(pfad: Path) -> tuple[str, str]:
    """Text und Hash der Datei."""
    daten = Path(pfad).read_bytes()
    return daten.decode("utf-8"), hash_von(daten)


def schreiben(pfad: Path, text: str, erwartet: str | None) -> str:
    """Schreibt `text`, wenn die Datei noch den Hash `erwartet` hat.

    `erwartet=None` schreibt ohne Prüfung (nur für Befehle, die selbst eben
    gelesen haben). Liefert den neuen Hash. Schreibt atomar über eine
    Zwischendatei.
    """
    pfad = Path(pfad)
    daten = text.encode("utf-8")
    with _SPERRE:
        aktuell = version(pfad)
        if erwartet is not None and erwartet != aktuell:
            raise Konflikt(pfad, erwartet, aktuell)
        zwischen = pfad.with_name(pfad.name + ".tmp")
        zwischen.write_bytes(daten)
        os.replace(zwischen, pfad)
    return hash_von(daten)


def zeilenende(text: str) -> str:
    """Zeilenende, das die Datei benutzt (für neu eingefügte Zeilen)."""
    return "\r\n" if "\r\n" in text else "\n"
