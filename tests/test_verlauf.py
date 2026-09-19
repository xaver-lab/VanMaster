"""Tests für ``tools.verlauf`` und den Befehl ``camper verlauf``."""
from __future__ import annotations

import pytest

import camper
from tools import common, verlauf


@pytest.fixture(autouse=True)
def ohne_verlauf(repo):
    """Der Bestand bringt bereits eine `verlauf.csv` mit — hier zählt nur,
    was der Test selbst schreibt."""
    common.VERLAUF_CSV.unlink(missing_ok=True)


def test_erfassen_legt_datei_an(repo):
    assert not common.VERLAUF_CSV.exists()
    verlauf.erfassen(heute="2026-01-01")
    assert common.VERLAUF_CSV.exists()
    rows = verlauf.lesen()
    assert len(rows) == 1
    assert rows[0]["datum"] == "2026-01-01"


def test_erfassen_ersetzt_denselben_tag_statt_zu_duplizieren(repo):
    verlauf.erfassen(heute="2026-01-01")
    verlauf.erfassen(heute="2026-01-01")
    rows = verlauf.lesen()
    assert len(rows) == 1


def test_erfassen_haengt_neuen_tag_an(repo):
    verlauf.erfassen(heute="2026-01-01")
    verlauf.erfassen(heute="2026-01-02")
    rows = verlauf.lesen()
    assert [r["datum"] for r in rows] == ["2026-01-01", "2026-01-02"]


def test_text_ohne_verlauf_erklaert_ersten_aufruf(repo):
    assert "camper verlauf" in verlauf.text()


def test_text_zeigt_zeitreihe(repo):
    verlauf.erfassen(heute="2026-01-01")
    verlauf.erfassen(heute="2026-01-05")
    out = verlauf.text()
    assert "2026-01-01" in out
    assert "2026-01-05" in out
    assert "2 Datensätze" in out


def test_cmd_verlauf_schreibt_und_zeigt(repo, capsys):
    camper.main(["verlauf"])
    out = capsys.readouterr().out
    assert "Verlauf erfasst für" in out
    assert common.VERLAUF_CSV.exists()


def test_cmd_verlauf_zweimal_am_selben_tag_keine_dublette(repo, capsys):
    camper.main(["verlauf"])
    capsys.readouterr()
    camper.main(["verlauf"])
    capsys.readouterr()
    assert len(verlauf.lesen()) == 1


def test_daten_ohne_verlauf_ist_leer_aber_vollstaendig(repo):
    d = verlauf.daten()
    assert d["punkte"] == []
    assert d["anzahl"] == 0
    assert d["von"] is None
    assert d["delta_bezahlt"] == 0.0


def test_daten_liefert_zahlen_keine_zeichenketten(repo):
    verlauf.erfassen(heute="2026-01-01")
    p = verlauf.daten()["punkte"][0]
    assert isinstance(p["bezahlt"], float)
    assert isinstance(p["aufgaben_fertig"], int)
    assert p["gewicht_kg"] is None or isinstance(p["gewicht_kg"], float)


def test_daten_rechnet_die_veraenderung_ueber_den_ganzen_zeitraum(repo):
    verlauf.erfassen(heute="2026-01-01")
    verlauf.erfassen(heute="2026-01-02")
    verlauf.erfassen(heute="2026-01-03")
    d = verlauf.daten()
    assert d["anzahl"] == 3
    assert d["von"] == "2026-01-01"
    assert d["bis"] == "2026-01-03"
    # Gleicher Bestand an allen drei Tagen — also keine Veränderung.
    assert d["delta_bezahlt"] == 0.0
    assert d["delta_aufgaben_fertig"] == 0


def test_daten_limit_kuerzt_die_punkte_aber_nicht_die_veraenderung(repo):
    for tag in ("2026-01-01", "2026-01-02", "2026-01-03"):
        verlauf.erfassen(heute=tag)
    d = verlauf.daten(limit=2)
    assert [p["datum"] for p in d["punkte"]] == ["2026-01-02", "2026-01-03"]
    assert d["anzahl"] == 3
    assert d["von"] == "2026-01-01"


def test_daten_uebersteht_kaputte_zahlen_in_der_csv(repo):
    verlauf.erfassen(heute="2026-01-01")
    text = common.VERLAUF_CSV.read_text(encoding="utf-8")
    kopf, zeile = text.splitlines()[0], text.splitlines()[1]
    felder = zeile.split(",")
    felder[1] = "keine-zahl"
    common.VERLAUF_CSV.write_text(kopf + "\n" + ",".join(felder) + "\n", encoding="utf-8")
    assert verlauf.daten()["punkte"][0]["bezahlt"] == 0.0
