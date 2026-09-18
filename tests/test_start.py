"""Tests für tools/server/start.py (UMBAU.md Phase 4) — Routenaufteilung
``/`` (neue Oberfläche/Hinweisseite), ``/alt/`` (altes Dashboard samt seiner
Schreibrouten) und ``/api/*`` (unverändert aus ``app_erstellen()``).

Läuft auf der ``repo``-Kopie von vault/ und data/ (tests/conftest.py) —
``common.ROOT`` zeigt dort auf ``tmp_path``, ``tools/server/start.py`` legt
``web/dist`` also unter ``tmp_path/web/dist`` an. Für die ``/alt/``-Tests wird
zusätzlich das reale ``docs/index.html`` + ``css``/``js`` in die Kopie
gespiegelt — ``conftest.py`` legt dort nur einen leeren Ordner an.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tools import common
from tools.kern import aufgaben_lesen
from tools.server.start import app_bauen

ECHT_DOCS = Path(__file__).resolve().parent.parent / "docs"


@pytest.fixture
def docs_repo(repo) -> Path:
    """``repo`` plus dem echten statischen Dashboard unter docs/ — für die
    ``/alt/``-Routen, die Handbau von index.html/css/js voraussetzen."""
    ziel = repo / "docs"
    shutil.copy2(ECHT_DOCS / "index.html", ziel / "index.html")
    shutil.copytree(ECHT_DOCS / "css", ziel / "css")
    shutil.copytree(ECHT_DOCS / "js", ziel / "js")
    return repo


def _client(**kwargs) -> TestClient:
    kwargs.setdefault("commit_ein", False)
    kwargs.setdefault("poll_intervall", 0)
    return TestClient(app_bauen(**kwargs))


# -------------------------------------------------------------- Neue Oberfläche

def test_wurzel_ohne_dist_zeigt_hinweisseite(repo):
    c = _client()
    r = c.get("/")
    assert r.status_code == 200
    assert "web/dist" in r.text
    assert "/alt/" in r.text


def test_wurzel_mit_dist_liefert_index(repo):
    dist = common.ROOT / "web" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html>neue Oberfläche</html>", encoding="utf-8")

    c = _client()
    r = c.get("/")
    assert r.status_code == 200
    assert "neue Oberfläche" in r.text


def test_spa_fallback_auf_index(repo):
    dist = common.ROOT / "web" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html>neue Oberfläche</html>", encoding="utf-8")

    c = _client()
    r = c.get("/irgendwas")
    assert r.status_code == 200
    assert "neue Oberfläche" in r.text


# -------------------------------------------------------------- Altes Dashboard

def test_alt_index_erreichbar(docs_repo):
    c = _client()
    r = c.get("/alt/index.html")
    assert r.status_code == 200
    assert "<html" in r.text.lower()


def test_api_daten_weiterhin_200(repo):
    c = _client()
    r = c.get("/api/daten")
    assert r.status_code == 200
    assert "bereiche" in r.json()


def test_alte_schreibroute_task_setzt_status(docs_repo):
    c = _client()
    vorher = next(a for a in aufgaben_lesen() if a.status == "offen")

    r = c.post("/alt/api/task", json={"id": vorher.id, "status": "laeuft"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert d["text"]

    nachher = next(a for a in aufgaben_lesen() if a.id == vorher.id)
    assert nachher.status == "laeuft"
    assert common.DASHBOARD_JSON.exists()


def test_alte_schreibroute_teil_setzt_feld(docs_repo):
    from tools import parts

    c = _client()
    zeile = parts.load()[0]

    r = c.post("/alt/api/teil", json={
        "id": zeile["id"], "feld": "notiz", "wert": "über /alt/api getestet",
    })
    assert r.status_code == 200, r.text

    neu = parts.find(zeile["id"])
    assert neu["notiz"] == "über /alt/api getestet"


def test_alte_schreibroute_unbekannte_aufgabe_500_statt_absturz(docs_repo):
    c = _client()
    r = c.post("/alt/api/task", json={"id": "keine-echte-id", "status": "laeuft"})
    assert r.status_code == 500
    assert r.json()["fehler"]
