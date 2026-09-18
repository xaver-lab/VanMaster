"""Live-Aktualisierung (UMBAU.md Phase 4): Quelldateien per mtime+Größe
überwachen, Änderungen als Server-Sent Events an verbundene Browser.

``Waechter`` kennt nur "Datei geändert" — Hash und Versionsschutz bleiben
in ``kern.datei``. Zwei Wege zu einem Ereignis:

- ``takt()``: ein Poll-Takt (aus dem Hintergrund-Thread, alle ``intervall``
  Sekunden). Mehrere Änderungen im selben Takt werden gebündelt, Quelle
  ``"extern"``.
- ``melden(datei_rel)``: sofortige Meldung einer eigenen Schreibaktion der
  App (Einhängepunkt ``app.state.nach_schreiben``), Quelle ``"web"`` — der
  Browser, der selbst geschrieben hat, soll das nicht als fremden Konflikt
  lesen. Aktualisiert den Stand sofort, damit der nächste Poll-Takt dieselbe
  Änderung nicht noch einmal als ``"extern"`` meldet.

Verbindung zu FastAPI (SSE) über ``sse_stream()`` — reine asyncio/Standard-
bibliothek, kein FastAPI-Import nötig, damit ``Waechter`` selbst ohne
laufende Event-Loop testbar bleibt (``beobachten()`` nimmt einen simplen
synchronen Callback).
"""
from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Callable

from .. import common
from ..kern import datei as kern_datei

HEARTBEAT_INTERVALL = 15.0


def _quelldateien() -> dict[str, Path]:
    """Alle überwachten Dateien, Pfade frisch über ``tools.common`` gelesen
    (nicht beim Import gebunden), damit Tests die Pfadkonstanten umbiegen
    können (tests/conftest.py)."""
    dateien: dict[str, Path] = {}
    for ordner in (
        common.BEREICHE_DIR, common.ENTSCHEIDUNGEN_DIR,
        common.ANLEITUNGEN_DIR, common.RECHERCHE_DIR,
    ):
        if ordner.is_dir():
            for pfad in sorted(ordner.glob("*.md")):
                dateien[kern_datei.rel(pfad)] = pfad
    for csv_pfad in (common.PARTS_CSV, common.BAUTEILE_CSV):
        if csv_pfad.exists():
            dateien[kern_datei.rel(csv_pfad)] = csv_pfad
    if common.MEDIEN_DIR.is_dir():
        for pfad in sorted(common.MEDIEN_DIR.rglob("*")):
            if pfad.is_file():
                dateien[kern_datei.rel(pfad)] = pfad
    return dateien


def _sse_paket(ereignis: str, daten: dict) -> str:
    return f"event: {ereignis}\ndata: {json.dumps(daten, ensure_ascii=False)}\n\n"


def _sse_kommentar(text: str) -> str:
    return f": {text}\n\n"


class Waechter:
    """Pollt Quelldateien in einem Hintergrund-Thread. Verbindungslos zu
    FastAPI — ``beobachten``/``nicht_mehr_beobachten`` nehmen einfache
    synchrone Callbacks, die ein fertiges SSE-Textpaket bekommen."""

    def __init__(self, intervall: float = 1.0):
        self.intervall = intervall
        self.heartbeat_intervall = HEARTBEAT_INTERVALL
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._stand: dict[str, tuple[float, int]] = {}
        self._beobachter: list[Callable[[str], None]] = []

    # ------------------------------------------------------------- Lebenszyklus

    def start(self) -> None:
        with self._lock:
            self._stand = self._erfassen()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._schleife, daemon=True, name="vanmaster-live-wache")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _schleife(self) -> None:
        while not self._stop.wait(self.intervall):
            self.takt()

    # ------------------------------------------------------------------ Melden

    def beobachten(self, callback: Callable[[str], None]) -> None:
        with self._lock:
            self._beobachter.append(callback)

    def nicht_mehr_beobachten(self, callback: Callable[[str], None]) -> None:
        with self._lock:
            if callback in self._beobachter:
                self._beobachter.remove(callback)

    def melden(self, datei_rel: str) -> None:
        """Einhängepunkt für ``app.state.nach_schreiben``: eigener
        Schreibvorgang der App, sofort mit ``quelle="web"``."""
        pfad = kern_datei.pfad(datei_rel)
        with self._lock:
            self._stand[datei_rel] = self._stat(pfad)
        self._sende([{"datei": datei_rel, "version": kern_datei.version(pfad)}],
                    quelle="web")

    def takt(self) -> None:
        """Ein Poll-Takt: vergleicht mtime+Größe gegen den letzten Stand,
        meldet alle Änderungen des Takts gebündelt als ein Ereignis."""
        neu = self._erfassen()
        with self._lock:
            alt = self._stand
            geaendert = sorted(
                (set(alt) | set(neu))
                - {rel for rel in (set(alt) & set(neu)) if alt[rel] == neu[rel]}
            )
            self._stand = neu
        if not geaendert:
            return
        dateien = [
            {"datei": rel, "version": kern_datei.version(kern_datei.pfad(rel))}
            for rel in geaendert
        ]
        self._sende(dateien, quelle="extern")

    def _sende(self, dateien: list[dict], quelle: str) -> None:
        payload = _sse_paket("aenderung", {"dateien": dateien, "quelle": quelle})
        with self._lock:
            beobachter = list(self._beobachter)
        for cb in beobachter:
            cb(payload)

    # --------------------------------------------------------------------- Stand

    @staticmethod
    def _stat(pfad: Path) -> tuple[float, int] | None:
        try:
            st = pfad.stat()
            return (st.st_mtime, st.st_size)
        except FileNotFoundError:
            return None

    def _erfassen(self) -> dict[str, tuple[float, int]]:
        stand: dict[str, tuple[float, int]] = {}
        for rel, pfad in _quelldateien().items():
            wert = self._stat(pfad)
            if wert is not None:
                stand[rel] = wert
        return stand


async def sse_stream(wache: Waechter, ist_getrennt: Callable[[], "asyncio.Future[bool] | bool"]):
    """Async-Generator für die SSE-Antwort: erstes Paket sofort, danach
    Ereignisse des Wächters, Heartbeat-Kommentar ohne Ereignis, sauberes
    Abmelden beim Verbindungsabbruch (Prüfung über ``ist_getrennt``, i.d.R.
    ``request.is_disconnected``)."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def weiterleiten(payload: str) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, payload)

    wache.beobachten(weiterleiten)
    try:
        yield _sse_kommentar("verbunden")
        while True:
            getrennt = ist_getrennt()
            if asyncio.iscoroutine(getrennt):
                getrennt = await getrennt
            if getrennt:
                break
            try:
                payload = await asyncio.wait_for(
                    queue.get(), timeout=wache.heartbeat_intervall)
                yield payload
            except asyncio.TimeoutError:
                yield _sse_kommentar("heartbeat")
    finally:
        wache.nicht_mehr_beobachten(weiterleiten)
