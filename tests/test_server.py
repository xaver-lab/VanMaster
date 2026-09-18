"""Tests für tools/server (UMBAU.md Phase 4) — FastAPI über TestClient,
auf der ``repo``-Kopie von vault/ und data/ (tests/conftest.py)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tools import common
from tools.kern import aufgaben_lesen, bereiche_lesen, datei, einzelteile_lesen, teile_lesen
from tools.server import app_erstellen


@pytest.fixture
def client(repo):
    return TestClient(app_erstellen())


def _erste_aufgabe(status: str | None = None):
    for a in aufgaben_lesen():
        if status is None or a.status == status:
            return a
    raise AssertionError("keine passende Aufgabe im Bestand")


def _bereich_mit_abschnitt(name: str):
    for b in bereiche_lesen():
        if name in b.abschnitte:
            return b
    raise AssertionError(f"kein Bereich mit Abschnitt '{name}'")


# ------------------------------------------------------------------ /api/daten

def test_daten_vollstaendig(client, repo):
    r = client.get("/api/daten")
    assert r.status_code == 200
    d = r.json()
    for schluessel in (
        "erzeugt", "bereiche", "aufgaben", "querverweise", "entscheidungen",
        "anleitungen", "recherche", "teile", "einzelteile", "medien",
        "versionen", "kennzahlen", "bearbeitbar",
    ):
        assert schluessel in d
    assert len(d["bereiche"]) == len(bereiche_lesen())
    assert len(d["aufgaben"]) == len(aufgaben_lesen())
    assert len(d["teile"]) == len(teile_lesen())
    k = d["kennzahlen"]
    for feld in ("aufgaben_fertig", "aufgaben_gesamt", "teile", "kosten",
                 "kosten_bestellt", "gewicht", "offene_entscheidungen", "bauteile"):
        assert feld in k


def test_daten_versionen_stimmen_mit_datei_version(client, repo):
    d = client.get("/api/daten").json()
    versionen = d["versionen"]
    for b in bereiche_lesen():
        assert versionen[b.datei] == datei.version(datei.pfad(b.datei))
    parts_rel = datei.rel(common.PARTS_CSV)
    bauteile_rel = datei.rel(common.BAUTEILE_CSV)
    assert versionen[parts_rel] == datei.version(common.PARTS_CSV)
    assert versionen[bauteile_rel] == datei.version(common.BAUTEILE_CSV)


# -------------------------------------------------------------------- Aufgaben

def test_aufgabe_anlegen(client, repo):
    b = bereiche_lesen()[0]
    r = client.post("/api/aufgaben", json={
        "bereich": b.name, "titel": "Testaufgabe vom Server",
        "version": datei.version(datei.pfad(b.datei)),
    })
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert d["id"]
    assert any(a.id == d["id"] for a in aufgaben_lesen())


def test_aufgabe_patch_status_und_titel(client, repo):
    a = _erste_aufgabe()
    pfad = datei.pfad(a.datei)
    r = client.patch(f"/api/aufgaben/{a.id}", json={
        "version": datei.version(pfad), "status": "laeuft", "titel": "Neuer Titel",
    })
    assert r.status_code == 200, r.text
    neu = next(x for x in aufgaben_lesen() if x.id == a.id)
    assert neu.status == "laeuft"
    assert neu.titel == "Neuer Titel"


def test_aufgabe_loeschen(client, repo):
    a = _erste_aufgabe()
    pfad = datei.pfad(a.datei)
    r = client.delete(f"/api/aufgaben/{a.id}", params={"version": datei.version(pfad)})
    assert r.status_code == 200, r.text
    assert not any(x.id == a.id for x in aufgaben_lesen())


def test_aufgabe_konflikt(client, repo):
    a = _erste_aufgabe()
    r = client.patch(f"/api/aufgaben/{a.id}", json={
        "version": "veraltet-und-falsch", "status": "laeuft",
    })
    assert r.status_code == 409
    d = r.json()
    assert d["fehler"]
    assert d["datei"] == a.datei
    assert d["stand"]["id"] == a.id


def test_aufgabe_ungueltiger_status_422(client, repo):
    a = _erste_aufgabe()
    pfad = datei.pfad(a.datei)
    r = client.patch(f"/api/aufgaben/{a.id}", json={
        "version": datei.version(pfad), "status": "keine-echte-box",
    })
    assert r.status_code == 422


def test_aufgabe_unbekannte_id_404(client, repo):
    r = client.patch("/api/aufgaben/gibt-es-nicht", json={
        "version": "egal", "status": "laeuft",
    })
    assert r.status_code == 404


# -------------------------------------------------------------------- Bereiche

def test_abschnitt_setzen_web(client, repo):
    b = _bereich_mit_abschnitt("Notizen")
    pfad = datei.pfad(b.datei)
    r = client.put(f"/api/bereiche/{b.name}/abschnitte/Notizen", json={
        "text": "Neuer Text über den Server.", "version": datei.version(pfad),
    })
    assert r.status_code == 200, r.text
    neu = next(x for x in bereiche_lesen() if x.name == b.name)
    assert neu.notizen == "Neuer Text über den Server."


def test_abschnitt_setzen_matrix_verstoss_403(client, repo):
    """`Auslegung` ist laut FORMAT.md §8 nur für Claude schreibbar."""
    b = _bereich_mit_abschnitt("Auslegung")
    pfad = datei.pfad(b.datei)
    r = client.put(f"/api/bereiche/{b.name}/abschnitte/Auslegung", json={
        "text": "Verbotener Web-Text.", "version": datei.version(pfad),
    })
    assert r.status_code == 403


def test_kopf_setzen_web(client, repo):
    b = bereiche_lesen()[0]
    pfad = datei.pfad(b.datei)
    r = client.patch(f"/api/bereiche/{b.name}/kopf", json={
        "feld": "kurz", "wert": "Kurzbeschreibung vom Server",
        "version": datei.version(pfad),
    })
    assert r.status_code == 200, r.text
    neu = next(x for x in bereiche_lesen() if x.name == b.name)
    assert neu.kurz == "Kurzbeschreibung vom Server"


def test_kopf_setzen_phase_nur_claude_403(client, repo):
    b = bereiche_lesen()[0]
    pfad = datei.pfad(b.datei)
    r = client.patch(f"/api/bereiche/{b.name}/kopf", json={
        "feld": "phase", "wert": 5, "version": datei.version(pfad),
    })
    assert r.status_code == 403


def test_bereich_unbekannt_404(client, repo):
    r = client.put("/api/bereiche/Gibtsnicht/abschnitte/Notizen", json={
        "text": "x", "version": "egal",
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------- Teile

def test_teil_anlegen(client, repo):
    version = datei.version(common.PARTS_CSV)
    r = client.post("/api/teile", json={
        "felder": {"titel": "Testteil vom Server", "kategorie": "Werkzeug"},
        "version": version,
    })
    assert r.status_code == 200, r.text
    d = r.json()
    assert any(t.id == d["id"] for t in teile_lesen())


def test_teil_patch(client, repo):
    t = teile_lesen()[0]
    version = datei.version(common.PARTS_CSV)
    r = client.patch(f"/api/teile/{t.id}", json={
        "feld": "status", "wert": "Bestellt", "version": version,
    })
    assert r.status_code == 200, r.text
    neu = next(x for x in teile_lesen() if x.id == t.id)
    assert neu.status == "Bestellt"


def test_teil_patch_matrix_verstoss_403_wird_422(client, repo):
    """`kennwerte` ist laut FORMAT.md §8 nur für Claude schreibbar — der Kern
    meldet das als `Ungueltig` (kein eigener Matrix-Fehlertyp bei Tabellen),
    die Route liefert dafür 422."""
    t = teile_lesen()[0]
    version = datei.version(common.PARTS_CSV)
    r = client.patch(f"/api/teile/{t.id}", json={
        "feld": "kennwerte", "wert": "1,5 mm", "version": version,
    })
    assert r.status_code == 422


def test_teil_loeschen(client, repo):
    t = teile_lesen()[0]
    version = datei.version(common.PARTS_CSV)
    r = client.delete(f"/api/teile/{t.id}", params={"version": version})
    assert r.status_code == 200, r.text
    assert not any(x.id == t.id for x in teile_lesen())


def test_teil_konflikt_409_mit_stand(client, repo):
    t = teile_lesen()[0]
    r = client.patch(f"/api/teile/{t.id}", json={
        "feld": "status", "wert": "Bestellt", "version": "veraltet",
    })
    assert r.status_code == 409
    d = r.json()
    assert d["stand"]["id"] == t.id


def test_teil_unbekannte_id_404(client, repo):
    version = datei.version(common.PARTS_CSV)
    r = client.patch("/api/teile/gibt-es-nicht", json={
        "feld": "status", "wert": "Bestellt", "version": version,
    })
    assert r.status_code == 404


# ----------------------------------------------------------------- Einzelteile

def test_einzelteil_anlegen_und_patch_und_loeschen(client, repo):
    version = datei.version(common.BAUTEILE_CSV)
    r = client.post("/api/einzelteile", json={
        "felder": {"titel": "Testleiste", "bereich": "Möbel"},
        "version": version,
    })
    assert r.status_code == 200, r.text
    neu_id = r.json()["id"]

    version = datei.version(common.BAUTEILE_CSV)
    r = client.patch(f"/api/einzelteile/{neu_id}", json={
        "feld": "laenge_mm", "wert": "800", "version": version,
    })
    assert r.status_code == 200, r.text
    neu = next(x for x in einzelteile_lesen() if x.id == neu_id)
    assert neu.laenge_mm == "800"

    version = datei.version(common.BAUTEILE_CSV)
    r = client.delete(f"/api/einzelteile/{neu_id}", params={"version": version})
    assert r.status_code == 200, r.text
    assert not any(x.id == neu_id for x in einzelteile_lesen())


def test_einzelteil_unbekannte_id_404(client, repo):
    version = datei.version(common.BAUTEILE_CSV)
    r = client.delete("/api/einzelteile/gibt-es-nicht", params={"version": version})
    assert r.status_code == 404
