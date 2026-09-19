"""Tests für ``tools.material`` und den Befehl ``camper material``.

Ungeprüft in dieser Sitzung — hier gibt es kein pytest/openpyxl. Sorgfältig
im Stil der übrigen Tests geschrieben (Fixture ``repo``), aber noch nicht
selbst ausgeführt.
"""
from __future__ import annotations

import camper
from tools import bauteile, material


def _platte(titel, bereich="Möbel", material_="Multiplex-Birke", dicke="15",
           laenge="1000", breite="1000", anzahl="1"):
    bauteile.add(titel, bereich, art="Platte", material=material_,
                dicke_mm=dicke, laenge_mm=laenge, breite_mm=breite,
                anzahl=anzahl)


def _leiste(titel, bereich="Möbel", material_="Kiefer", dicke="20",
           laenge="1900", breite="40", anzahl="2"):
    bauteile.add(titel, bereich, art="Leiste", material=material_,
                dicke_mm=dicke, laenge_mm=laenge, breite_mm=breite,
                anzahl=anzahl)


def test_leer_ohne_einzelteile(repo):
    assert material.liste() == []


def test_gruppiert_nach_material_und_dicke(repo):
    _platte("Bettboden")
    _platte("Seitenwand", dicke="18")
    gruppen = material.liste()
    schluessel = {(g["material"], g["dicke_mm"]) for g in gruppen}
    assert ("Multiplex-Birke", "15") in schluessel
    assert ("Multiplex-Birke", "18") in schluessel


def test_bedarf_summiert_flaeche_bei_platten(repo):
    _platte("Bettboden", laenge="1000", breite="1000", anzahl="1")
    _platte("Seitenwand", laenge="600", breite="400", anzahl="2")
    gruppen = material.liste()
    [gruppe] = gruppen
    assert gruppe["bedarf"] == "1.48 m²"


def test_bedarf_summiert_laufmeter_bei_leisten(repo):
    _leiste("Rahmen", laenge="1900", anzahl="2")
    gruppen = material.liste()
    [gruppe] = gruppen
    assert gruppe["bedarf"] == "3.80 lfm"


def test_bereich_filtert(repo):
    _platte("Bettboden", bereich="Möbel")
    _platte("Werkbank", bereich="Karosserie")
    gruppen = material.liste(bereich="Karosserie")
    zuschnitte = [z["titel"] for g in gruppen for z in g["zuschnitte"]]
    assert zuschnitte == ["Werkbank"]


def test_cmd_material_ohne_einzelteile(repo, capsys):
    camper.main(["material"])
    out = capsys.readouterr().out
    assert "Keine Einzelteile" in out


def test_cmd_material_zeigt_gruppen(repo, capsys):
    _platte("Bettboden")
    camper.main(["material"])
    out = capsys.readouterr().out
    assert "Multiplex-Birke" in out
    assert "Bettboden" in out


def test_cmd_material_bereich_filter(repo, capsys):
    _platte("Bettboden", bereich="Möbel")
    _platte("Werkbank", bereich="Karosserie")
    camper.main(["material", "--bereich", "Karosserie"])
    out = capsys.readouterr().out
    assert "Werkbank" in out
    assert "Bettboden" not in out


def test_cmd_material_json(repo, capsys):
    _platte("Bettboden")
    camper.main(["material", "--json"])
    out = capsys.readouterr().out
    import json
    daten = json.loads(out)
    assert daten[0]["material"] == "Multiplex-Birke"
    assert daten[0]["zuschnitte"][0]["titel"] == "Bettboden"
