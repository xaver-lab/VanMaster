"""Serverstart der neuen App (UMBAU.md Phase 4).

    python camper.py serve                 → neue App, http://localhost:8765
    python camper.py serve --kein-commit    → Auto-Commit abschalten

Routenaufteilung:

- ``/api/*``  — kommt unverändert aus ``app_erstellen()`` (``app.py``).
- ``/medien`` — Web-Kopien der Bilder (``tools/media.py:web_export()``,
  ``data/generated/medien/``).
- ``/``       — liefert ``web/dist`` mit SPA-Fallback auf ``index.html``.
  Existiert ``web/dist`` noch nicht, eine Hinweisseite.

Dieses Modul fasst ``tools/server/app.py`` und ``tools/server/live.py`` nicht
an, sondern hängt sich nur über ``app_erstellen()`` und ``app.state`` ein.
"""
from __future__ import annotations

import socket
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .. import common
from . import commit
from .app import app_erstellen

_HINWEIS = """<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>VanMaster</title></head>
<body style="font-family: sans-serif; max-width: 32rem; margin: 4rem auto 0; padding: 0 1rem;">
<h1>Neue Oberfläche noch nicht gebaut</h1>
<p><code>web/dist</code> fehlt noch — <code>camper web build</code> laufen lassen.</p>
</body>
</html>
"""


def _statisch_neu(app: FastAPI) -> None:
    """``/`` → ``web/dist`` mit SPA-Fallback, sonst Hinweisseite. Muss nach
    allen anderen Routen angehängt werden — der Pfadfänger ``{pfad:path}``
    würde sonst auch ``/api/...`` an sich ziehen."""
    dist = common.ROOT / "web" / "dist"
    index = dist / "index.html"

    @app.get("/", include_in_schema=False)
    def wurzel():
        if index.is_file():
            return FileResponse(index)
        return HTMLResponse(_HINWEIS)

    if index.is_file():
        @app.get("/{voller_pfad:path}", include_in_schema=False)
        def spa(voller_pfad: str):
            ziel = dist / voller_pfad
            if ziel.is_file():
                return FileResponse(ziel)
            return FileResponse(index)
    else:
        @app.get("/{voller_pfad:path}", include_in_schema=False)
        def hinweis(voller_pfad: str):
            return HTMLResponse(_HINWEIS, status_code=404)


def app_bauen(*, commit_ein: bool = True,
              ruhe_sekunden: float = 180, poll_intervall: float | None = None) -> FastAPI:
    """Baut die vollständige App: Kern-API, Medien-Route, neue Oberfläche
    (oder Hinweisseite) auf ``/``, optional Auto-Commit."""
    app = app_erstellen(poll_intervall)
    # Web-Kopien der Medien (tools/media.py: web_export).
    common.MEDIEN_WEB_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/medien", StaticFiles(directory=str(common.MEDIEN_WEB_DIR)),
              name="medien")
    _statisch_neu(app)

    if commit_ein:
        sammler = commit.anmelden(app, ruhe_sekunden=ruhe_sekunden)
        basis_lebenszyklus = app.router.lifespan_context

        @asynccontextmanager
        async def lebenszyklus(app_: FastAPI):
            async with basis_lebenszyklus(app_):
                yield
            sammler.jetzt_committen()

        app.router.lifespan_context = lebenszyklus

    return app


# ------------------------------------------------------------------- Start

def adresse() -> str:
    """IP im WLAN — damit das Handy die Adresse abtippen kann."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def run(port: int = 8765, offen: bool = False, oeffnen: bool = True,
        kein_commit: bool = False) -> None:
    import uvicorn

    app = app_bauen(commit_ein=not kein_commit)
    host = "0.0.0.0" if offen else "127.0.0.1"
    lokal = f"http://localhost:{port}/"
    print(f"Dashboard läuft — {lokal}")
    if offen:
        print(f"  am Handy im WLAN: http://{adresse()}:{port}/")
    print("  Strg+C beendet.")
    if oeffnen:
        webbrowser.open(lokal)
    uvicorn.run(app, host=host, port=port, log_level="warning")
