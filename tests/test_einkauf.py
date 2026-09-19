"""Tests für den Einkaufsvorschlag (``camper buy next``) — Daten und Text
kommen aus derselben Quelle, damit Befehl und Dashboard nicht auseinanderlaufen.
"""
from __future__ import annotations

from tools import parts


def _entschieden(repo):
    return [r for r in parts.load() if r["status"] == "Entschieden"]


def test_buy_daten_nimmt_nur_entschiedene(repo):
    d = parts.buy_daten()
    assert d["teile_gesamt"] == len(_entschieden(repo))
    gelistet = {tid for g in d["gruppen"] for tid in g["teile"]}
    assert gelistet == {r["id"] for r in _entschieden(repo)}


def test_buy_daten_sortiert_nach_prioritaet_dann_betrag(repo):
    from tools.common import PART_PRIO

    d = parts.buy_daten()
    nach_id = {r["id"]: r for r in parts.load()}
    reihe = [nach_id[tid] for g in d["gruppen"] for tid in g["teile"]]
    # Innerhalb einer Händlergruppe bleibt die Gesamtreihenfolge erhalten.
    for gruppe in d["gruppen"]:
        rows = [nach_id[tid] for tid in gruppe["teile"]]
        schluessel = [(PART_PRIO.index(r["prioritaet"]) if r["prioritaet"] in PART_PRIO else 9,
                       -parts.gesamt(r)) for r in rows]
        assert schluessel == sorted(schluessel)
    assert reihe  # es gibt überhaupt etwas zu bestellen


def test_buy_daten_summen_stimmen(repo):
    d = parts.buy_daten()
    nach_id = {r["id"]: r for r in parts.load()}
    for gruppe in d["gruppen"]:
        erwartet = parts.summe([nach_id[tid] for tid in gruppe["teile"]])
        assert gruppe["summe"] == round(erwartet, 2)
    assert d["summe"] == round(sum(g["summe"] for g in d["gruppen"]), 2)


def test_buy_daten_buendelt_nach_haendler(repo):
    d = parts.buy_daten()
    nach_id = {r["id"]: r for r in parts.load()}
    namen = [g["haendler"] for g in d["gruppen"]]
    assert len(namen) == len(set(namen)), "jeder Händler nur einmal"
    for gruppe in d["gruppen"]:
        for tid in gruppe["teile"]:
            roh = nach_id[tid]["haendler"] or parts.OHNE_HAENDLER
            assert roh == gruppe["haendler"]
    # Teuerster Korb zuerst — so steht es auch im Text.
    summen = [g["summe"] for g in d["gruppen"]]
    assert summen == sorted(summen, reverse=True)


def test_buy_limit_kuerzt_die_liste(repo):
    gesamt = parts.buy_daten()["teile_gesamt"]
    if gesamt < 2:
        return
    d = parts.buy_daten(limit=1)
    assert d["teile_gesamt"] == 1


def test_buy_next_text_nennt_haendler_und_summe(repo):
    d = parts.buy_daten()
    text = parts.buy_next()
    for gruppe in d["gruppen"]:
        assert gruppe["haendler"] in text
    assert "Summe:" in text


def test_buy_next_ohne_entschiedene_sagt_das(repo):
    for row in _entschieden(repo):
        parts.set_field(row["id"], "status", "Idee")
    assert "Nichts zu bestellen" in parts.buy_next()
    assert parts.buy_daten()["teile_gesamt"] == 0
