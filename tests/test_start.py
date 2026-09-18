"""Tests für tools/server/start.py (UMBAU.md Phase 4/9) — Routenaufteilung
``/`` (neue Oberfläche/Hinweisseite), ``/medien`` (Web-Kopien der Bilder) und
``/api/*`` (unverändert aus ``app_erstellen()``). Das alte Dashboard unter
``/alt/`` ist mit UMBAU.md Phase 9 entfernt worden.

Läuft auf der ``repo``-Kopie von vault/ und data/ (tests/conftest.py) —
``common.ROOT`` zeigt dort auf ``tmp_path``, ``tools/server/start.py`` legt
``web/dist`` also unter ``tmp_path/web/dist`` an.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from tools import common
from tools.server.start import app_bauen


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


def test_api_daten_weiterhin_200(repo):
    c = _client()
    r = c.get("/api/daten")
    assert r.status_code == 200
    assert "bereiche" in r.json()


def test_altes_dashboard_gibt_es_nicht_mehr(repo):
    c = _client()
    r = c.get("/alt/index.html")
    assert r.status_code == 404


# ------------------------------------------------------------------- Medien

def test_medien_route_liefert_web_kopie(repo):
    ordner = common.MEDIEN_WEB_DIR / "kueche"
    ordner.mkdir(parents=True)
    (ordner / "skizze.png").write_bytes(b"\x89PNG-test")

    c = _client()
    r = c.get("/medien/kueche/skizze.png")
    assert r.status_code == 200
    assert r.content == b"\x89PNG-test"
    assert c.get("/medien/kueche/fehlt.png").status_code == 404
