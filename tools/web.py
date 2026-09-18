"""web/ bauen — Vite + Svelte 5 + TypeScript (UMBAU.md Phase 5).

    python camper.py web build   → web/dist erzeugen (npm install/ci bei Bedarf)
    python camper.py web dev     → Vite-Dev-Server (Proxy auf camper serve)
    python camper.py web check   → svelte-check (inkl. api-typen.ts)
    python camper.py web daten   → web/dist/data.json + medien/ (Lesemodus,
                                    z. B. GitHub Pages) — erst nach `web build`

npm-Suche: zuerst ``~/nodejs/npm.cmd`` (portable Node auf manchen Rechnern —
dann ``~/nodejs`` vorne in den PATH des Kindprozesses, sonst scheitert npm am
eigenen Node-Aufruf), sonst ``npm`` aus dem PATH.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .common import DOCS, ROOT, STANDARD_SORTIERUNG, fail, write_json

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


def daten_export(sortierung: str = STANDARD_SORTIERUNG) -> str:
    """web/dist/data.json + medien/ für den Lesemodus (GitHub Pages, UMBAU.md
    Phase 9). Dieselbe Struktur wie ``GET /api/daten``
    (``tools/server/daten.py:daten_json``); als Nebeneffekt davon aktualisiert
    ``media.web_export()`` auch ``docs/medien`` — von dort wird hierher
    kopiert. Läuft erst nach ``web build`` (braucht ``web/dist``)."""
    dist = WEB_DIR / "dist"
    if not (dist / "index.html").is_file():
        fail("web/dist fehlt — erst `camper web build` laufen lassen.")
    from fastapi.encoders import jsonable_encoder

    from .server import daten as server_daten  # spät, um Zyklen zu vermeiden

    # Gleiche Umwandlung wie FastAPI sie für GET /api/daten selbst macht
    # (Bereich & Co. sind Dataclasses, json.dumps kann sie nicht direkt).
    d = jsonable_encoder(server_daten.daten_json(sortierung))
    write_json(dist / "data.json", d)

    medien_ziel = dist / "medien"
    if medien_ziel.exists():
        shutil.rmtree(medien_ziel)
    quelle = DOCS / "medien"
    n = 0
    if quelle.exists():
        shutil.copytree(quelle, medien_ziel)
        n = sum(1 for p in medien_ziel.rglob("*") if p.is_file())
    return f"web/dist/data.json geschrieben, {n} Mediendateien nach web/dist/medien kopiert"


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
