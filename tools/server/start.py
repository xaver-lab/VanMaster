"""Serverstart der neuen App (UMBAU.md Phase 4).

    python camper.py serve                 → neue App, http://localhost:8765
    python camper.py serve --alt            → altes Dashboard (tools/serve.py)
    python camper.py serve --kein-commit    → Auto-Commit abschalten

Routenaufteilung:

- ``/api/*``  — kommt unverändert aus ``app_erstellen()`` (``app.py``).
- ``/alt/*``  — liefert ``docs/`` (altes Dashboard) statisch aus. Sein
  Schreibweg spricht ``api/task``/``api/teil``/``api/sync`` relativ an, landet
  unter ``/alt/`` also bei ``/alt/api/...`` — dieselbe Logik wie
  ``tools/serve.py:Handler``, hier als FastAPI-Routen nachgebaut, weil
  ``app.py`` und ``live.py`` nicht angefasst werden (anderer Agent arbeitet
  daran). Nach jedem Schreiben wird ``docs/data.json``/``data.js`` neu gebaut,
  wie der alte Server es tat.
- ``/``       — liefert ``web/dist`` mit SPA-Fallback auf ``index.html``.
  Existiert ``web/dist`` noch nicht (Phase 5), eine Hinweisseite mit Link auf
  ``/alt/``.

Dieses Modul fasst ``tools/server/app.py`` und ``tools/server/live.py`` nicht
an, sondern hängt sich nur über ``app_erstellen()`` und ``app.state`` ein.
"""
from __future__ import annotations

import socket
import webbrowser
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .. import build, common, parts, tasks
from ..common import STANDARD_SORTIERUNG
from ..kern import datei as kern_datei
from ..kern import tabellen as kern_tabellen
from . import commit
from .app import app_erstellen

_HINWEIS = """<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>VanMaster</title></head>
<body style="font-family: sans-serif; max-width: 32rem; margin: 4rem auto 0; padding: 0 1rem;">
<h1>Neue Oberfläche noch nicht gebaut</h1>
<p><code>web/dist</code> fehlt noch — sie kommt erst in Phase 5.</p>
<p><a href="/alt/">Zum alten Dashboard →</a></p>
</body>
</html>
"""

# Die Web-Schreibrouten des alten Dashboards vertragen kein gleichzeitiges
# Schreiben aus zwei Tabs — wie tools/serve.py:SCHLOSS.
_SCHLOSS = Lock()


def _melde(app: FastAPI, datei_rel: str) -> None:
    for hook in app.state.nach_schreiben:
        hook(datei_rel)


def _alt_antwort(app: FastAPI, sortierung: str, text: str,
                  datei_rel: str = "") -> JSONResponse:
    frisch = build.daten(sortierung)
    build.schreiben(frisch)      # docs/data.json + data.js nachziehen
    if datei_rel:
        _melde(app, datei_rel)
    return JSONResponse({"ok": True, "text": text, "daten": frisch,
                          "stand": round(common.DASHBOARD_JSON.stat().st_mtime, 3)})


def _alte_api_routen(app: FastAPI, sortierung: str) -> None:
    """Bildet die Schreibrouten aus ``tools/serve.py`` unter ``/alt/api/``
    nach, damit das unverändert ausgelieferte ``docs/`` seinen relativen
    Schreibweg dort findet."""

    @app.get("/alt/api/hallo", include_in_schema=False)
    def alt_hallo():
        stand = (common.DASHBOARD_JSON.stat().st_mtime
                 if common.DASHBOARD_JSON.exists() else 0)
        return {"schreiben": True, "stand": round(stand, 3)}

    @app.post("/alt/api/task", include_in_schema=False)
    async def alt_task(request: Request):
        with _SCHLOSS:
            try:
                nutzlast = await request.json()
                a = tasks.find(nutzlast["id"])
                if a is None:
                    raise ValueError(f"Keine Aufgabe zu '{nutzlast['id']}' gefunden.")
                if "beschreibung" in nutzlast:
                    text = tasks.set_description(nutzlast["id"], nutzlast["beschreibung"])
                else:
                    text = tasks.set_status(nutzlast["id"], nutzlast["status"])
            except KeyError as fehler:
                return JSONResponse({"fehler": f"Feld fehlt: {fehler}"}, status_code=400)
            except Exception as fehler:  # noqa: BLE001 — Fehler gehört in den Browser
                return JSONResponse({"fehler": str(fehler)}, status_code=500)
            return _alt_antwort(app, sortierung, text, a["datei"])

    @app.post("/alt/api/teil", include_in_schema=False)
    async def alt_teil(request: Request):
        with _SCHLOSS:
            try:
                nutzlast = await request.json()
                row = parts.find(nutzlast["id"])
                if row is None:
                    raise ValueError(
                        f"Kein Teil mit der Kennung '{nutzlast['id']}'.")
                alt = row.get(nutzlast["feld"], "")
                kern_tabellen.teil_feld_setzen(
                    row["id"], nutzlast["feld"], nutzlast["wert"],
                    None, quelle="web")
                text = (f"{row['titel']}: {nutzlast['feld']} {alt or '—'} "
                        f"→ {nutzlast['wert']}")
            except KeyError as fehler:
                return JSONResponse({"fehler": f"Feld fehlt: {fehler}"}, status_code=400)
            except Exception as fehler:  # noqa: BLE001
                return JSONResponse({"fehler": str(fehler)}, status_code=500)
            return _alt_antwort(app, sortierung, text, kern_datei.rel(common.PARTS_CSV))

    @app.post("/alt/api/sync", include_in_schema=False)
    def alt_sync():
        with _SCHLOSS:
            return _alt_antwort(app, sortierung, "neu gebaut")


def _statisch_neu(app: FastAPI) -> None:
    """``/`` → ``web/dist`` mit SPA-Fallback, sonst Hinweisseite. Muss nach
    allen anderen Routen angehängt werden — der Pfadfänger ``{pfad:path}``
    würde sonst auch ``/api/...`` und ``/alt/...`` an sich ziehen."""
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


def app_bauen(sortierung: str = STANDARD_SORTIERUNG, *, commit_ein: bool = True,
              ruhe_sekunden: float = 180, poll_intervall: float | None = None) -> FastAPI:
    """Baut die vollständige App: Kern-API, altes Dashboard unter ``/alt/``,
    neue Oberfläche (oder Hinweisseite) auf ``/``, optional Auto-Commit."""
    app = app_erstellen(poll_intervall)
    _alte_api_routen(app, sortierung)
    # Web-Kopien der Medien (tools/media.py: web_export) — eigene Route,
    # damit die neue Oberfläche nicht am alten Dashboard hängt.
    medien = common.DOCS / "medien"
    medien.mkdir(parents=True, exist_ok=True)
    app.mount("/medien", StaticFiles(directory=str(medien)), name="medien")
    app.mount("/alt", StaticFiles(directory=str(common.DOCS), html=True),
              name="alt-dashboard")
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
        sortierung: str = STANDARD_SORTIERUNG, kein_commit: bool = False) -> None:
    import uvicorn

    app = app_bauen(sortierung, commit_ein=not kein_commit)
    host = "0.0.0.0" if offen else "127.0.0.1"
    lokal = f"http://localhost:{port}/"
    print(f"Dashboard läuft — {lokal}")
    if offen:
        print(f"  am Handy im WLAN: http://{adresse()}:{port}/")
    print("  altes Dashboard weiter unter /alt/ · Strg+C beendet.")
    if oeffnen:
        webbrowser.open(lokal)
    uvicorn.run(app, host=host, port=port, log_level="warning")
