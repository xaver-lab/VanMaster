"""Baut und startet die neue Oberfläche unter ``web/`` (UMBAU.md Phase 5).

Ruft npm auf — portabel gesucht: zuerst die Windows-Installation des
Nutzers unter ``~/nodejs/npm.cmd``, dann ``~/nodejs/npm``, zuletzt ``npm``
aus dem PATH. Node selbst liegt portabel unter ``~/nodejs/`` (Version 24,
nicht im PATH) — dieses Modul braucht nur npm, ruft Node also nie direkt auf.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .common import ROOT, fail

WEB_DIR = ROOT / "web"
WEB_DIST = WEB_DIR / "dist"
WEB_NODE_MODULES = WEB_DIR / "node_modules"

_HINWEIS_NPM = (
    "kein npm gefunden. Portable Node-Installation unter ~/nodejs/ erwartet "
    "(Version 24, nicht im PATH) — dort muss npm.cmd (Windows) bzw. npm "
    "liegen. Alternativ npm über das PATH bereitstellen."
)
_HINWEIS_NODE_MODULES = (
    "web/node_modules fehlt — erst `camper web install` ausführen."
)


def npm_pfad() -> Path | None:
    """Sucht npm: zuerst die portable Installation des Nutzers unter
    ``~/nodejs/``, danach ``npm`` aus dem PATH. ``None``, wenn nichts
    gefunden wurde."""
    for kandidat in (Path.home() / "nodejs" / "npm.cmd",
                     Path.home() / "nodejs" / "npm"):
        if kandidat.exists():
            return kandidat
    gefunden = shutil.which("npm")
    return Path(gefunden) if gefunden else None


def _npm_lauf(npm: Path, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    """``npm.cmd`` ist unter Windows ein Skript, kein natives Programm —
    braucht eine Shell, um gefunden und ausgeführt zu werden."""
    braucht_shell = npm.suffix.lower() == ".cmd"
    befehl = f'"{npm}" {" ".join(argv)}' if braucht_shell else [str(npm), *argv]
    return subprocess.run(befehl, cwd=WEB_DIR, shell=braucht_shell, **kwargs)


def _npm_oder_fehler() -> Path:
    npm = npm_pfad()
    if npm is None:
        fail(_HINWEIS_NPM)
    return npm  # unerreichbar nach fail(), aber für den Typprüfer


def install() -> str:
    npm = _npm_oder_fehler()
    ergebnis = _npm_lauf(npm, ["install"])
    if ergebnis.returncode != 0:
        fail(f"npm install fehlgeschlagen (Exit-Code {ergebnis.returncode}).")
    return f"Abhängigkeiten installiert — {WEB_NODE_MODULES}"


def build() -> str:
    npm = _npm_oder_fehler()
    if not WEB_NODE_MODULES.exists():
        fail(_HINWEIS_NODE_MODULES)
    ergebnis = _npm_lauf(npm, ["run", "build"])
    if ergebnis.returncode != 0:
        fail(f"Build fehlgeschlagen (Exit-Code {ergebnis.returncode}).")
    return f"Oberfläche gebaut — {WEB_DIST}"


def dev() -> None:
    """Startet den Vite-Dev-Server im Vordergrund (blockiert, bis der
    Nutzer abbricht) — Ein-/Ausgabe gehen direkt an die Konsole."""
    npm = _npm_oder_fehler()
    if not WEB_NODE_MODULES.exists():
        fail(_HINWEIS_NODE_MODULES)
    _npm_lauf(npm, ["run", "dev"], stdout=sys.stdout, stderr=sys.stderr,
              stdin=sys.stdin)
