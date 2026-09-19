"""Tests für ``tools.gewicht`` und den Befehl ``camper gewicht``.

Ungeprüft in dieser Sitzung — hier gibt es kein pytest/openpyxl. Sorgfältig
im Stil der übrigen Tests geschrieben (Fixture ``repo``), aber noch nicht
selbst ausgeführt.
"""
from __future__ import annotations

import camper
from tools import bauteile, common, gewicht


def _camper_md_kopf_setzen(zeilen: list[str]) -> None:
    text = common.CAMPER_MD.read_text(encoding="utf-8")
    kopf, rest = text.split("\n---", 1)
    neuer_kopf = kopf + "\n" + "\n".join(zeilen) + "\n---" + rest
    common.CAMPER_MD.write_text(neuer_kopf, encoding="utf-8", newline="\n")


def _einzelteil_anlegen(**felder):
    titel = felder.pop("titel", "Testteil")
    bereich = felder.pop("bereich", "Möbel")
    bauteile.add(titel, bereich, **felder)


# ------------------------------------------------------------------ fahrzeug

def test_fahrzeug_fehlt_ohne_camper_md_felder(repo):
    f = gewicht.fahrzeug()
    assert f["leergewicht_kg"] is None
    assert f["zul_gesamtgewicht_kg"] is None


def test_fahrzeug_liest_beide_felder(repo):
    _camper_md_kopf_setzen(["leergewicht_kg: 2100", "zul_gesamtgewicht_kg: 3500"])
    f = gewicht.fahrzeug()
    assert f["leergewicht_kg"] == 2100.0
    assert f["zul_gesamtgewicht_kg"] == 3500.0


def test_fahrzeug_akzeptiert_komma(repo):
    _camper_md_kopf_setzen(["leergewicht_kg: 2100,5"])
    assert gewicht.fahrzeug()["leergewicht_kg"] == 2100.5


# -------------------------------------------------------------------- bilanz

def test_bilanz_ohne_fahrzeugdaten_liefert_trotzdem_summen(repo):
    d = gewicht.bilanz()
    assert d["zuladung_erlaubt_kg"] is None
    assert d["teile_kg"] >= 0
    assert d["ausbau_kg"] == round(d["teile_kg"] + d["bauteile_kg"], 1)


def test_bilanz_rechnet_zuladung_aus_fahrzeugdaten(repo):
    _camper_md_kopf_setzen(["leergewicht_kg: 2000", "zul_gesamtgewicht_kg: 3000"])
    d = gewicht.bilanz()
    assert d["zuladung_erlaubt_kg"] == 1000.0


def test_bilanz_zaehlt_einzelteile_ohne_gewicht(repo):
    _einzelteil_anlegen(titel="Winkel ohne Gewicht", bereich="Elektrik",
                        art="Beschlag")
    d = gewicht.bilanz()
    assert d["bauteile_gesamt"] == 1
    assert d["bauteile_fehlt"] == 1
    assert d["bauteile_kg"] == 0.0


def test_bilanz_berechnet_gewicht_aus_holzdichte(repo):
    _einzelteil_anlegen(titel="Bettboden", bereich="Möbel", art="Platte",
                        material="Multiplex-Birke",
                        laenge_mm="1000", breite_mm="1000", dicke_mm="15")
    d = gewicht.bilanz()
    assert d["bauteile_fehlt"] == 0
    # 1 m x 1 m x 0.015 m x 650 kg/m3 = 9.75 kg
    assert d["bauteile_kg"] == 9.75


def test_bilanz_nutzt_angegebenes_gewicht_vor_berechnung(repo):
    _einzelteil_anlegen(titel="Bettboden", bereich="Möbel", art="Platte",
                        material="Multiplex-Birke", gewicht_kg="5",
                        laenge_mm="1000", breite_mm="1000", dicke_mm="15")
    d = gewicht.bilanz()
    assert d["bauteile_kg"] == 5.0


# ---------------------------------------------------------------------- cmd

def test_cmd_gewicht_benennt_das_fehlende_feld(repo, capsys):
    # Im Bestand steht zul_gesamtgewicht_kg, aber kein leergewicht_kg.
    camper.main(["gewicht"])
    out = capsys.readouterr().out
    assert "Keine Zuladungsbilanz" in out
    assert "Leergewicht fehlt" in out
    assert "leergewicht_kg" in out


def test_cmd_gewicht_mit_fahrzeugdaten_zeigt_zuladung(repo, capsys):
    _camper_md_kopf_setzen(["leergewicht_kg: 2000", "zul_gesamtgewicht_kg: 3000"])
    camper.main(["gewicht"])
    out = capsys.readouterr().out
    assert "Zulässige Zuladung: 1000 kg" in out


def test_cmd_gewicht_json(repo, capsys):
    _camper_md_kopf_setzen(["leergewicht_kg: 2000", "zul_gesamtgewicht_kg: 3000"])
    camper.main(["gewicht", "--json"])
    out = capsys.readouterr().out
    import json
    daten = json.loads(out)
    assert daten["zuladung_erlaubt_kg"] == 1000.0


def test_cmd_gewicht_warnt_bei_ueberschreitung(repo, capsys):
    # Zuladung absichtlich winzig (1 kg) — die real vorhandene Stückliste
    # allein liegt schon darüber, unabhängig von ihrem genauen Gewicht.
    _camper_md_kopf_setzen(["leergewicht_kg: 2000", "zul_gesamtgewicht_kg: 2001"])
    camper.main(["gewicht"])
    out = capsys.readouterr().out
    assert "⚠" in out
