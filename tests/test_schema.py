"""Tests für tools/server/schema.py (UMBAU.md Phase 4) — TS-Erzeugung aus
den Pydantic-Modellen des Servers."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tools.server import app_erstellen
from tools.server.modelle import DatenAntwort
from tools.server.schema import erzeugen, schreiben


def test_erzeugung_laeuft_und_ist_deterministisch():
    a = erzeugen()
    b = erzeugen()
    assert a == b
    assert a.startswith("// erzeugt — nicht von Hand ändern")


def test_enthaelt_erwartete_typnamen():
    text = erzeugen()
    for name in (
        "DatenAntwort", "AufgabeAntwort", "BereichAntwort", "TeilAntwort",
        "EinzelteilAntwort", "SeiteAntwort", "QuerverweisAntwort",
        "MediumAntwort", "KennzahlenAntwort", "SchreibErfolg",
        "FehlerAntwort", "KonfliktAntwort", "AufgabeAnlegenAnfrage",
        "AufgabePatchAnfrage", "AbschnittAnfrage", "KopfAnfrage",
        "TeilAnlegenAnfrage", "TeilPatchAnfrage", "EinzelteilAnlegenAnfrage",
        "EinzelteilPatchAnfrage",
    ):
        assert f"interface {name} " in text or f"type {name} =" in text, name


def test_schreiben_legt_dateien_an(tmp_path):
    ts_pfad, json_pfad = schreiben(tmp_path)
    assert ts_pfad.exists()
    assert json_pfad is not None and json_pfad.exists()
    assert ts_pfad.read_text(encoding="utf-8") == erzeugen()


def test_daten_antwort_validiert_api_daten(repo):
    client = TestClient(app_erstellen())
    r = client.get("/api/daten")
    assert r.status_code == 200
    DatenAntwort.model_validate(r.json())
