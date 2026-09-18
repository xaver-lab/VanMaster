"""Datenkern: einzige Stelle, die vault/ und data/ typisiert liest (und
später schreibt). Öffentliche Schnittstelle — Details stehen in
``lesen.py`` (Parser) und ``modelle.py`` (Datenklassen).
"""
from __future__ import annotations

from .lesen import (
    aufgaben_lesen, bereiche_lesen, einzelteile_lesen, laden, medien_lesen,
    querverweise_lesen, seiten_lesen, teile_lesen,
)
from .modelle import (
    Abschnitt, Aufgabe, Bereich, Bestand, Einzelteil, Medium, Querverweis,
    Seite, Teil,
)

__all__ = [
    "laden",
    "bereiche_lesen", "aufgaben_lesen", "seiten_lesen", "teile_lesen",
    "einzelteile_lesen", "medien_lesen", "querverweise_lesen",
    "Bestand", "Bereich", "Abschnitt", "Aufgabe", "Querverweis", "Seite",
    "Teil", "Einzelteil", "Medium",
]
