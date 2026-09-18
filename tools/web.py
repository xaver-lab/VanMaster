"""web/ bauen — Vite + Svelte 5 + TypeScript (UMBAU.md Phase 5).

    python camper.py web build   → web/dist erzeugen (npm install/ci bei Bedarf)
    python camper.py web dev     → Vite-Dev-Server (Proxy auf camper serve)
    python camper.py web check   → svelte-check (inkl. api-typen.ts)

npm-Suche: zuerst ``~/nodejs/npm.cmd`` (portable Node auf manchen Rechnern —
dann ``~/nodejs`` vorne in den PATH des Kindprozesses, sonst scheitert npm am
eigenen Node-Aufruf), sonst ``npm`` aus dem PATH.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .common import ROOT, fail

WEB_DIR = ROOT / "web"


def npm_pfad() -> tuple[Path, dict[str, str]]:
    """Pfad zu npm plus die Umgebung, mit der es laufen muss."""
    env = os.environ.copy()
    portabel = Path.home() / "nodejs" / "npm.cmd"
    if portabel.is_file():
        env["PATH"] = str(portabel.parent) + os.pathsep + env.get("PATH", "")
        return portabel, env
    gefunden = shutil.which("npm")
    if gefunden:
        return Path(gefunden), env
    fail("npm nicht gefunden — weder ~/nodejs/npm.cmd noch npm im PATH. "
         "Node.js installieren oder ~/nodejs/ mit der portablen Version anlegen.")
    raise AssertionError("unreachable")  # für mypy/lint, fail hebt SystemExit


def _laufen(npm: Path, env: dict[str, str], *argumente: str,
            capture: bool = False) -> subprocess.CompletedProcess:
    befehl = [str(npm), *argumente]
    ergebnis = subprocess.run(
        befehl, cwd=WEB_DIR, env=env, shell=False,
        capture_output=capture, text=True)
    if ergebnis.returncode != 0:
        if capture:
            print(ergebnis.stdout)
            print(ergebnis.stderr)
        fail(f"npm {' '.join(argumente)} fehlgeschlagen "
             f"(Exit-Code {ergebnis.returncode}).")
    return ergebnis


def sicherstellen_installiert() -> str | None:
    """Installiert node_modules, wenn sie fehlen. Gibt eine Meldezeile zurück
    (oder None, wenn schon installiert war)."""
    if (WEB_DIR / "node_modules").exists():
        return None
    npm, env = npm_pfad()
    if (WEB_DIR / "package-lock.json").exists():
        _laufen(npm, env, "ci")
        return "npm ci gelaufen"
    _laufen(npm, env, "install")
    return "npm install gelaufen"


def _ordner_kb(pfad: Path) -> tuple[int, float]:
    dateien = [d for d in pfad.rglob("*") if d.is_file()]
    return len(dateien), sum(d.stat().st_size for d in dateien) / 1024


def build() -> str:
    if not WEB_DIR.is_dir():
        fail("web/ fehlt.")
    meldung = sicherstellen_installiert()
    npm, env = npm_pfad()
    _laufen(npm, env, "run", "build")
    dist = WEB_DIR / "dist"
    if not (dist / "index.html").is_file():
        fail("web/dist/index.html fehlt nach dem Build.")
    n, kb = _ordner_kb(dist)
    zeilen = []
    if meldung:
        zeilen.append(meldung)
    zeilen.append(f"web/dist gebaut ({n} Dateien, {kb:.0f} kB)")
    return "\n".join(zeilen)


def check() -> str:
    if not WEB_DIR.is_dir():
        fail("web/ fehlt.")
    meldung = sicherstellen_installiert()
    npm, env = npm_pfad()
    ergebnis = _laufen(npm, env, "run", "check", capture=True)
    zeilen = []
    if meldung:
        zeilen.append(meldung)
    ausgabe = (ergebnis.stdout or "").strip()
    if ausgabe:
        zeilen.append(ausgabe.splitlines()[-1])
    else:
        zeilen.append("svelte-check ohne Ausgabe (ok)")
    return "\n".join(zeilen)


def dev() -> None:
    """Startet den Vite-Dev-Server im Vordergrund (blockierend, wie ``camper
    serve``) — Ausgabe geht direkt an die Konsole."""
    if not WEB_DIR.is_dir():
        fail("web/ fehlt.")
    meldung = sicherstellen_installiert()
    if meldung:
        print(meldung)
    npm, env = npm_pfad()
    subprocess.run([str(npm), "run", "dev"], cwd=WEB_DIR, env=env, shell=False)
