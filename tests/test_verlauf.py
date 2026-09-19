"""Tests für ``tools.verlauf`` und den Befehl ``camper verlauf``.

Ungeprüft in dieser Sitzung — kein pytest verfügbar. Im Stil der übrigen
Tests geschrieben (Fixture ``repo``).
"""
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
