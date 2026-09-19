"""Tests für ``tools.budget`` und den Befehl ``camper budget``.

Ungeprüft in dieser Sitzung — hier gibt es kein pytest/openpyxl. Sorgfältig
im Stil der übrigen Tests geschrieben (Fixture ``repo``), aber noch nicht
selbst ausgeführt.
"""
from __future__ import annotations

import camper
from tools import budget, common


def _kopf_ohne(schluessel: set[str]) -> None:
    """Die genannten Kopffelder aus `vault/Camper.md` entfernen."""
    text = common.CAMPER_MD.read_text(encoding="utf-8")
    kopf, rest = text.split("\n---", 1)
    behalten = [z for z in kopf.splitlines()
                if z.split(":", 1)[0].strip() not in schluessel]
    common.CAMPER_MD.write_text("\n".join(behalten) + "\n---" + rest,
                                encoding="utf-8", newline="\n")


def _budget_kopf_setzen(zeilen: list[str]) -> None:
    _kopf_ohne({z.split(":", 1)[0].strip() for z in zeilen})
    text = common.CAMPER_MD.read_text(encoding="utf-8")
    kopf, rest = text.split("\n---", 1)
    neuer_kopf = kopf + "\n" + "\n".join(zeilen) + "\n---" + rest
    common.CAMPER_MD.write_text(neuer_kopf, encoding="utf-8", newline="\n")


def test_ziel_fehlt_ohne_camper_md_feld(repo):
    _kopf_ohne({"budget"})
    z = budget.ziel()
    assert z["gesamt"] is None
    assert z["kategorien"] == {}


def test_ziel_liest_gesamt_und_kategorie(repo):
    _budget_kopf_setzen(["budget: 25000", "budget_elektrik: 4000"])
    z = budget.ziel()
    assert z["gesamt"] == 25000.0
    assert z["kategorien"]["Elektrik"] == 4000.0


def test_ziel_akzeptiert_komma(repo):
    _budget_kopf_setzen(["budget: 12500,50"])
    assert budget.ziel()["gesamt"] == 12500.5


def test_daten_ohne_ziel_liefert_trotzdem_bezahlt_und_geplant(repo):
    _kopf_ohne({"budget"})
    d = budget.daten()
    assert d["ziel"] is None
    assert d["rest"] is None
    assert d["differenz_prognose"] is None
    assert d["bezahlt"] >= 0
    assert d["prognose"] == round(d["bezahlt"] + d["geplant"], 2)


def test_daten_mit_ziel_rechnet_rest_und_prognose(repo):
    _budget_kopf_setzen(["budget: 1000"])
    d = budget.daten()
    assert d["ziel"] == 1000.0
    assert d["rest"] == round(1000.0 - d["bezahlt"], 2)
    assert d["differenz_prognose"] == round(d["prognose"] - 1000.0, 2)


def test_kategorie_feld_slug():
    assert budget.kategorie_feld("Dämmung") == "budget_daemmung"
    assert budget.kategorie_feld("Küche") == "budget_kueche"


def test_cmd_budget_ohne_ziel_erklaert_eintrag(repo, capsys):
    _kopf_ohne({"budget"})
    camper.main(["budget"])
    out = capsys.readouterr().out
    assert "Kein Zielbudget gesetzt" in out
    assert "budget: 25000" in out


def test_cmd_budget_mit_ziel_zeigt_kennzahlen(repo, capsys):
    _budget_kopf_setzen(["budget: 5000"])
    camper.main(["budget"])
    out = capsys.readouterr().out
    assert "Ziel:" in out
    assert "Prognose:" in out


def test_cmd_budget_json(repo, capsys):
    _budget_kopf_setzen(["budget: 5000"])
    camper.main(["budget", "--json"])
    out = capsys.readouterr().out
    import json
    daten = json.loads(out)
    assert daten["ziel"] == 5000.0
    assert isinstance(daten["kategorien"], list)
