"""FastAPI-Server auf dem Datenkern (UMBAU.md Phase 4).

``app_erstellen()`` (``app.py``) baut die Anwendung, ``daten_json()``
(``daten.py``) liefert denselben Bestand wie ``GET /api/daten`` als reines
Dict — auch für die künftige GitHub Action (Phase 9), ohne FastAPI-
Abhängigkeit dort.
"""
from __future__ import annotations

from .app import app_erstellen
from .daten import daten_json

__all__ = ["app_erstellen", "daten_json"]
