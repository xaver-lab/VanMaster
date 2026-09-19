"""Tests für die Strombilanz (``camper strom``).

Die Verbraucher stehen in ``data/parts.csv`` (`watt`, `stunden_pro_tag`).
Die Fixture kopiert den echten Bestand, in dem beide Felder leer sind —
jeder Test setzt seine Werte deshalb selbst (siehe HANDOFF.md).
"""
from __future__ import annotations

import pytest

from tools import parts, strom


def _setzen(paare: dict[str, tuple[str, str]]) -> None:
    """`{teil_id: (watt, stunden_pro_tag)}` in die CSV schreiben."""
    rows = parts.load()
    for row in rows:
        if row["id"] in paare:
            row["watt"], row["stunden_pro_tag"] = paare[row["id"]]
    parts.save(rows)


def _erste_ids(n: int) -> list[str]:
    return [r["id"] for r in parts.load()[:n]]


def _kopf_setzen(repo, **felder) -> None:
    from tools import common

    text = common.read_text(common.CAMPER_MD)
    kopf, rest = text.split("---", 2)[1], text.split("---", 2)[2]
    zeilen = [z for z in kopf.strip().split("\n")
              if z.split(":")[0].strip() not in felder]
    zeilen += [f"{k}: {v}" for k, v in felder.items()]
    common.write_text(common.CAMPER_MD, "---\n" + "\n".join(zeilen) + "\n---" + rest)


# ------------------------------------------------------------------ leer

def test_ohne_werte_keine_verbraucher(repo):
    d = strom.bilanz()
    assert d["verbraucher"] == []
    assert d["wh_pro_tag"] == 0
    assert "Keine Verbraucher erfasst" in strom.text()


def test_nur_watt_ohne_stunden_zaehlt_nicht(repo):
    """Eines allein ergibt keinen Tagesverbrauch — geraten wird nicht."""
    tid = _erste_ids(1)[0]
    _setzen({tid: ("45", "")})
    d = strom.bilanz()
    assert d["verbraucher"] == []
    assert [u["id"] for u in d["unvollstaendig"]] == [tid]
    assert tid in str(d["unvollstaendig"])


def test_nur_stunden_ohne_watt_zaehlt_nicht(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("", "8")})
    d = strom.bilanz()
    assert d["verbraucher"] == []
    assert len(d["unvollstaendig"]) == 1


# ------------------------------------------------------------- Rechnung

def test_wh_und_ah_pro_tag(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("45", "8")})
    d = strom.bilanz()
    v = d["verbraucher"][0]
    menge = v["menge"]
    assert v["wh_pro_tag"] == pytest.approx(menge * 45 * 8)
    assert v["ah_pro_tag"] == pytest.approx(menge * 45 * 8 / 12, abs=0.01)
    assert d["wh_pro_tag"] == pytest.approx(v["wh_pro_tag"])
    assert d["ah_pro_tag"] == pytest.approx(v["ah_pro_tag"], abs=0.01)


def test_summe_ueber_mehrere_verbraucher(repo):
    a, b = _erste_ids(2)
    _setzen({a: ("10", "2"), b: ("20", "1")})
    d = strom.bilanz()
    assert len(d["verbraucher"]) == 2
    erwartet = sum(v["wh_pro_tag"] for v in d["verbraucher"])
    assert d["wh_pro_tag"] == pytest.approx(erwartet)


def test_verbraucher_stehen_nach_verbrauch_sortiert(repo):
    a, b, c = _erste_ids(3)
    _setzen({a: ("5", "1"), b: ("50", "1"), c: ("20", "1")})
    wh = [v["wh_pro_tag"] for v in strom.bilanz()["verbraucher"]]
    assert wh == sorted(wh, reverse=True)


def test_bordspannung_aus_dem_kopf(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("24", "1")})
    _kopf_setzen(repo, bordspannung_v=24)
    d = strom.bilanz()
    assert d["bordspannung_v"] == 24
    v = d["verbraucher"][0]
    assert v["ah_pro_tag"] == pytest.approx(v["wh_pro_tag"] / 24, abs=0.01)


# ------------------------------------------------------------ Reichweite

def test_ohne_batterie_keine_reichweite(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("45", "8")})
    d = strom.bilanz()
    assert d["batterie_ah"] is None
    assert d["reichweite_tage"] is None
    assert "batterie_ah" in strom.text()


def test_reichweite_aus_nutzbarer_kapazitaet(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("45", "8")})
    _kopf_setzen(repo, batterie_ah=200, bordspannung_v=12, batterie_nutzbar=0.8)
    d = strom.bilanz()
    assert d["nutzbar_ah"] == pytest.approx(160)
    assert d["reichweite_tage"] == pytest.approx(160 / d["ah_pro_tag_brutto"], abs=0.1)
    assert "Reichweite" in strom.text()


def test_wirkungsgrad_erhoeht_den_bedarf(repo):
    tid = _erste_ids(1)[0]
    _setzen({tid: ("45", "8")})
    _kopf_setzen(repo, batterie_ah=200, wirkungsgrad=0.85)
    d = strom.bilanz()
    assert d["ah_pro_tag_brutto"] == pytest.approx(d["ah_pro_tag"] / 0.85, abs=0.01)
    assert d["ah_pro_tag_brutto"] > d["ah_pro_tag"]


def test_knappe_reichweite_wird_gewarnt(repo):
    a, b = _erste_ids(2)
    _setzen({a: ("500", "12"), b: ("500", "12")})
    _kopf_setzen(repo, batterie_ah=100, batterie_nutzbar=0.8)
    d = strom.bilanz()
    assert d["reichweite_tage"] < strom.SCHWELLE_TAGE
    assert "zu knapp" in strom.text()


# ---------------------------------------------------------------- Format

def test_felder_stehen_in_der_csv(repo):
    from tools.kern.format import TEIL_FELDER

    assert "watt" in TEIL_FELDER
    assert "stunden_pro_tag" in TEIL_FELDER
    kopf = open(parts.PARTS_CSV, encoding="utf-8").readline().strip().split(",")
    assert kopf == TEIL_FELDER


def test_werte_werden_als_zahl_geprueft(repo):
    from tools.kern import tabellen

    tid = _erste_ids(1)[0]
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen(tid, "watt", "viel", None, quelle="claude")
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen(tid, "stunden_pro_tag", "den ganzen Tag", None,
                                  quelle="claude")
    # Beim Schreiben gilt der Punkt (wie bei preis/menge/gewicht_kg); das
    # Komma akzeptiert nur das Lesen.
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen(tid, "stunden_pro_tag", "1,5", None, quelle="claude")
    tabellen.teil_feld_setzen(tid, "stunden_pro_tag", "1.5", None, quelle="claude")
    assert parts.find(tid)["stunden_pro_tag"] == "1.5"
