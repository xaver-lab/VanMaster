"""Datenkern: einzige Stelle, die vault/ und data/ typisiert liest und
schreibt. Öffentliche Schnittstelle — Details stehen in ``lesen.py``
(Parser), ``modelle.py`` (Datenklassen), ``datei.py`` (Versionsschutz),
``aufgaben.py``, ``abschnitte.py``, ``tabellen.py`` (Schreiben) und
``pruefen.py`` (Formatprüfung).
"""
from __future__ import annotations

from . import abschnitte, aufgaben, datei, tabellen
from .abschnitte import Unerlaubt
from .datei import Konflikt
from .lesen import (
    aufgaben_lesen, bereiche_lesen, einzelteile_lesen, laden, medien_lesen,
    querverweise_lesen, seiten_lesen, teile_lesen,
)
from .modelle import (
    Abschnitt, Aufgabe, Bereich, Bestand, Einzelteil, Medium, Querverweis,
    Seite, Teil,
)
from .pruefen import Befund, pruefen
from .tabellen import Ungueltig

__all__ = [
    "laden",
    "bereiche_lesen", "aufgaben_lesen", "seiten_lesen", "teile_lesen",
    "einzelteile_lesen", "medien_lesen", "querverweise_lesen",
    "Bestand", "Bereich", "Abschnitt", "Aufgabe", "Querverweis", "Seite",
    "Teil", "Einzelteil", "Medium",
    "aufgaben", "abschnitte", "tabellen", "datei",
    "pruefen", "Befund", "Konflikt", "Unerlaubt", "Ungueltig",
]
