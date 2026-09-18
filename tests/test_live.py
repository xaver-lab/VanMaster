"""Tests für die Live-Aktualisierung (UMBAU.md Phase 4, tools/server/live.py).

Wächter-Logik direkt (ohne Hintergrund-Thread, ``takt()``/``melden()`` von
Hand angestoßen) und die SSE-Route einmal über TestClient — mit Timeout,
damit kein Test hängt.
"""
from __future__ import annotations

import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from tools import common
from tools.kern import datei
from tools.server import app_erstellen
from tools.server.live import Waechter


def _ereignisse(zeilen: list[str]) -> list[tuple[str, dict]]:
    """Zerlegt gesammelte SSE-Textpakete in (ereignis, daten)-Paare."""
    ergebnis = []
    for paket in zeilen:
        if paket.startswith(":"):
            continue
        ereignis = "message"
        daten = None
        for zeile in paket.splitlines():
            if zeile.startswith("event: "):
                ereignis = zeile[len("event: "):]
            elif zeile.startswith("data: "):
                daten = json.loads(zeile[len("data: "):])
        ergebnis.append((ereignis, daten))
    return ergebnis


@pytest.fixture
def wache(repo):
    w = Waechter(intervall=999)  # kein automatischer Takt in diesem Test
    w._stand = w._erfassen()
    gesehen: list[str] = []
    w.beobachten(gesehen.append)
    return w, gesehen


def test_takt_erkennt_geaenderte_datei(repo, wache):
    w, gesehen = wache
    bereich_datei = next((common.BEREICHE_DIR).glob("*.md"))
    text = bereich_datei.read_text(encoding="utf-8")
    bereich_datei.write_text(text + "\nGeändert für den Test.\n", encoding="utf-8")

    w.takt()

    assert len(gesehen) == 1
    ereignis, daten = _ereignisse(gesehen)[0]
    assert ereignis == "aenderung"
    assert daten["quelle"] == "extern"
    rel = datei.rel(bereich_datei)
    treffer = [d for d in daten["dateien"] if d["datei"] == rel]
    assert len(treffer) == 1
    assert treffer[0]["version"] == datei.version(bereich_datei)


def test_takt_ohne_aenderung_meldet_nichts(repo, wache):
    w, gesehen = wache
    w.takt()
    assert gesehen == []


def test_takt_buendelt_mehrere_aenderungen(repo, wache):
    w, gesehen = wache
    bereiche = sorted(common.BEREICHE_DIR.glob("*.md"))
    assert len(bereiche) >= 2, "Testbestand braucht mindestens zwei Bereiche"
    for b in bereiche[:2]:
        b.write_text(b.read_text(encoding="utf-8") + "\nGeändert.\n", encoding="utf-8")

    w.takt()

    assert len(gesehen) == 1, "mehrere Änderungen in einem Takt -> ein Ereignis"
    _, daten = _ereignisse(gesehen)[0]
    gemeldete_dateien = {d["datei"] for d in daten["dateien"]}
    for b in bereiche[:2]:
        assert datei.rel(b) in gemeldete_dateien


def test_takt_erkennt_neue_datei(repo, wache):
    w, gesehen = wache
    neu = common.BEREICHE_DIR / "Testbereich.md"
    neu.write_text("---\nkurz: Test\n---\n\n## Notizen\n", encoding="utf-8")

    w.takt()

    _, daten = _ereignisse(gesehen)[0]
    rel = datei.rel(neu)
    treffer = [d for d in daten["dateien"] if d["datei"] == rel]
    assert len(treffer) == 1
    assert treffer[0]["version"] == datei.version(neu)


def test_takt_erkennt_geloeschte_datei(repo, wache):
    w, gesehen = wache
    ziel = sorted(common.BEREICHE_DIR.glob("*.md"))[0]
    rel = datei.rel(ziel)
    ziel.unlink()

    w.takt()

    _, daten = _ereignisse(gesehen)[0]
    treffer = [d for d in daten["dateien"] if d["datei"] == rel]
    assert len(treffer) == 1
    assert treffer[0]["version"] == ""  # Datei gibt es nicht mehr


def test_melden_ist_sofort_quelle_web(repo, wache):
    w, gesehen = wache
    bereich_datei = next(common.BEREICHE_DIR.glob("*.md"))
    text = bereich_datei.read_text(encoding="utf-8")
    bereich_datei.write_text(text + "\nÜber die App geschrieben.\n", encoding="utf-8")
    rel = datei.rel(bereich_datei)

    w.melden(rel)

    assert len(gesehen) == 1
    ereignis, daten = _ereignisse(gesehen)[0]
    assert ereignis == "aenderung"
    assert daten["quelle"] == "web"
    assert daten["dateien"] == [{"datei": rel, "version": datei.version(bereich_datei)}]


def test_melden_verhindert_doppelte_extern_meldung_im_naechsten_takt(repo, wache):
    w, gesehen = wache
    bereich_datei = next(common.BEREICHE_DIR.glob("*.md"))
    text = bereich_datei.read_text(encoding="utf-8")
    bereich_datei.write_text(text + "\nÜber die App geschrieben.\n", encoding="utf-8")
    rel = datei.rel(bereich_datei)

    w.melden(rel)
    gesehen.clear()
    w.takt()  # derselbe Stand -> kein weiteres Ereignis

    assert gesehen == []


# ------------------------------------------------------------------------ SSE


def test_live_route_ohne_waechter_503(repo):
    # poll_intervall=0 -> kein Hintergrund-Thread, die Route meldet das.
    with TestClient(app_erstellen(poll_intervall=0)) as client:
        r = client.get("/api/live")
        assert r.status_code == 503


def _freier_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_sse_route_liefert_erstes_paket_und_schliesst_sauber(repo):
    # Starlettes TestClient puffert SSE-Antworten vollständig, bevor
    # `client.stream()` zurückkehrt (bekannte Einschränkung der
    # httpx-ASGITransport-Anbindung) — für eine echte Teilübertragung
    # braucht es einen laufenden Server. Absicherung gegen Hänger: fester
    # Verbindungs-Timeout plus erzwungenes Server-Ende danach.
    port = _freier_port()
    app = app_erstellen(poll_intervall=60)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        else:
            raise AssertionError("Server ist nicht innerhalb der Frist gestartet")

        with httpx.stream(
            "GET", f"http://127.0.0.1:{port}/api/live", timeout=5
        ) as r:
            assert r.status_code == 200
            assert r.headers["content-type"].startswith("text/event-stream")
            erste_zeile = next(r.iter_lines())
            assert erste_zeile.startswith(":")  # Verbindungs-Kommentar
    finally:
        server.should_exit = True
        thread.join(timeout=5)
