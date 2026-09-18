"""Auto-Commit für Web-Änderungen (UMBAU.md Phase 4).

``Sammler`` hängt sich an ``app.state.nach_schreiben`` (siehe ``app.py``):
jede Schreibroute meldet die geänderte, repo-relative Datei. Der Sammler
wartet ``ruhe_sekunden`` ohne weitere Meldung ab und committet dann genau
die gesammelten Dateien mit einer Zeile Nachricht. Kein Push.

Einhängen (macht der Serve-Punkt beim echten Serverstart, nicht diese
Datei): ``sammler = anmelden(app)``; beim Herunterfahren zusätzlich
``sammler.jetzt_committen()`` aufrufen, damit nichts Ungesichertes liegen
bleibt.
"""
from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path

from .. import common

log = logging.getLogger(__name__)


class Sammler:
    """Sammelt Dateipfade und committet sie nach einer Ruhephase."""

    def __init__(self, ruhe_sekunden: float = 180, repo: Path | None = None):
        self.ruhe_sekunden = ruhe_sekunden
        self._repo = repo
        self._dateien: dict[str, str | None] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def _repo_pfad(self) -> Path:
        return self._repo if self._repo is not None else common.ROOT

    # -------------------------------------------------------------- Melden

    def melden(self, datei: str) -> None:
        """Callback-Signatur für ``app.state.nach_schreiben``."""
        with self._lock:
            self._dateien.setdefault(datei, None)
            self._timer_neu_starten()

    def vermerken(self, datei: str, was: str) -> None:
        """Optionale kurze Beschreibung zu einer bereits gemeldeten (oder
        noch zu meldenden) Datei, z. B. ein Aufgaben- oder Teilname."""
        with self._lock:
            self._dateien[datei] = was

    def _timer_neu_starten(self) -> None:
        # Läuft unter self._lock.
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self.ruhe_sekunden, self._timer_ausgeloest)
        self._timer.daemon = True
        self._timer.start()

    def _timer_ausgeloest(self) -> None:
        self._commit_sicher()

    # ------------------------------------------------------------- Commit

    def jetzt_committen(self) -> None:
        """Committet sofort, ohne auf die Ruhephase zu warten (z. B. beim
        Herunterfahren)."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        self._commit_sicher()

    def _commit_sicher(self) -> None:
        try:
            self._commit()
        except Exception:
            log.exception("Auto-Commit fehlgeschlagen")

    def _commit(self) -> None:
        with self._lock:
            dateien = dict(self._dateien)
            self._dateien.clear()
            self._timer = None
        if not dateien:
            return

        repo = self._repo_pfad()
        pfade = list(dateien.keys())

        try:
            status = subprocess.run(
                ["git", "status", "--porcelain", "--", *pfade],
                cwd=repo, capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            log.warning("git status fehlgeschlagen: %s", exc)
            return

        geaendert = _geaenderte_dateien(status.stdout, pfade)
        if not geaendert:
            return

        try:
            subprocess.run(
                ["git", "add", "--", *geaendert],
                cwd=repo, capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", _nachricht(geaendert, dateien)],
                cwd=repo, capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            log.warning("git add/commit fehlgeschlagen: %s", exc)
            return


def _geaenderte_dateien(status_ausgabe: str, gemeldete: list[str]) -> list[str]:
    """Welche der gemeldeten Dateien laut ``git status --porcelain`` wirklich
    geändert sind, in der Reihenfolge von ``gemeldete``."""
    gefunden: set[str] = set()
    for zeile in status_ausgabe.splitlines():
        if len(zeile) < 4:
            continue
        pfad = zeile[3:].strip()
        # Bei Umbenennung steht "alt -> neu" in der Ausgabe.
        if " -> " in pfad:
            pfad = pfad.split(" -> ", 1)[1]
        pfad = pfad.strip('"')
        gefunden.add(pfad)
    return [p for p in gemeldete if p in gefunden]


def _nachricht(geaendert: list[str], beschreibungen: dict[str, str | None]) -> str:
    labels: list[str] = []
    for datei in geaendert:
        was = beschreibungen.get(datei)
        label = was if was else Path(datei).stem
        if label not in labels:
            labels.append(label)
    return f"Web: {', '.join(labels)} geändert"


def anmelden(app, ruhe_sekunden: float = 180, repo: Path | None = None) -> Sammler:
    """Hängt einen neuen ``Sammler`` an ``app.state.nach_schreiben``. Gibt
    den Sammler zurück, damit der Aufrufer bei Bedarf ``vermerken`` oder
    (beim Herunterfahren) ``jetzt_committen`` aufrufen kann."""
    sammler = Sammler(ruhe_sekunden=ruhe_sekunden, repo=repo)
    app.state.nach_schreiben.append(sammler.melden)
    return sammler
