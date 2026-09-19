"""Tests für den Ablaufplan (``camper ablauf``) — Stufen, Schlüsselaufgaben
und Ringe aus den ``@braucht:``-Bezügen.

Die Fixture kopiert den echten Bestand, deshalb stellt jeder Test, der eine
bestimmte Lage braucht, sie selbst her (siehe HANDOFF.md).
"""
from __future__ import annotations

from tools import ablauf, tasks
from tools.kern.format import ERLEDIGT


def _offene_ids() -> set[str]:
    aufgaben = tasks.load()
    return {a["id"] for a in tasks.blaetter(aufgaben) if a["status"] not in ERLEDIGT}


def test_jede_offene_aufgabe_landet_genau_einmal(repo):
    d = ablauf.plan()
    gelistet = [a["id"] for s in d["stufen"] for a in s["aufgaben"]]
    gelistet += [a["id"] for a in d["ring"]]
    assert len(gelistet) == len(set(gelistet)), "keine Aufgabe doppelt"
    assert set(gelistet) == _offene_ids()
    assert d["offen_gesamt"] == len(_offene_ids())


def test_stufe_eins_hat_keine_offenen_blocker(repo):
    d = ablauf.plan()
    assert d["stufen"], "es gibt offene Aufgaben"
    assert d["stufen"][0]["stufe"] == 1
    for a in d["stufen"][0]["aufgaben"]:
        assert a["braucht"] == [], f"{a['id']} steht in Stufe 1, wartet aber"


def test_blocker_stehen_immer_in_einer_frueheren_stufe(repo):
    d = ablauf.plan()
    stufe_von = {a["id"]: s["stufe"] for s in d["stufen"] for a in s["aufgaben"]}
    for s in d["stufen"]:
        for a in s["aufgaben"]:
            for b in a["braucht"]:
                # Blocker im Ring stehen in keiner Stufe — die prüft der
                # Ring-Test.
                if b in stufe_von:
                    assert stufe_von[b] < s["stufe"], \
                        f"{a['id']} (Stufe {s['stufe']}) braucht {b} (Stufe {stufe_von[b]})"


def test_stufen_sind_lueckenlos_und_aufsteigend(repo):
    d = ablauf.plan()
    nummern = [s["stufe"] for s in d["stufen"]]
    assert nummern == sorted(nummern)
    assert nummern == list(range(1, len(nummern) + 1))
    assert d["tiefe"] == len(nummern)


def test_haelt_auf_zaehlt_die_ganze_kette(repo):
    """a ← b ← c: a hält zwei Aufgaben auf, b eine, c keine."""
    a = tasks.add("Elektrik", "Kette A")
    b = tasks.add("Elektrik", "Kette B")
    c = tasks.add("Elektrik", "Kette C")
    ids = {x["titel"]: x["id"] for x in tasks.load() if x["titel"].startswith("Kette ")}
    _braucht_setzen(ids["Kette B"], ids["Kette A"])
    _braucht_setzen(ids["Kette C"], ids["Kette B"])

    nach_id = {x["id"]: x for s in ablauf.plan()["stufen"] for x in s["aufgaben"]}
    assert nach_id[ids["Kette A"]]["haelt_auf"] == 2
    assert nach_id[ids["Kette B"]]["haelt_auf"] == 1
    assert nach_id[ids["Kette C"]]["haelt_auf"] == 0
    # …und die Reihenfolge stimmt
    stufe = {x["id"]: s["stufe"] for s in ablauf.plan()["stufen"] for x in s["aufgaben"]}
    assert stufe[ids["Kette A"]] < stufe[ids["Kette B"]] < stufe[ids["Kette C"]]
    assert a and b and c  # die Rückmeldungen selbst sind hier egal


def test_ring_wird_erkannt_und_nicht_einsortiert(repo):
    tasks.add("Elektrik", "Ring A")
    tasks.add("Elektrik", "Ring B")
    ids = {x["titel"]: x["id"] for x in tasks.load() if x["titel"].startswith("Ring ")}
    _braucht_setzen(ids["Ring A"], ids["Ring B"])
    _braucht_setzen(ids["Ring B"], ids["Ring A"])

    d = ablauf.plan()
    im_ring = {a["id"] for a in d["ring"]}
    assert im_ring == {ids["Ring A"], ids["Ring B"]}
    in_stufen = {a["id"] for s in d["stufen"] for a in s["aufgaben"]}
    assert not (im_ring & in_stufen), "Ringaufgaben stehen in keiner Stufe"
    assert "Ring" in ablauf.text()


def test_erledigte_blocker_halten_nicht_mehr_auf(repo):
    tasks.add("Elektrik", "Frei A")
    tasks.add("Elektrik", "Frei B")
    ids = {x["titel"]: x["id"] for x in tasks.load() if x["titel"].startswith("Frei ")}
    _braucht_setzen(ids["Frei B"], ids["Frei A"])

    stufe = {x["id"]: s["stufe"] for s in ablauf.plan()["stufen"] for x in s["aufgaben"]}
    assert stufe[ids["Frei B"]] > stufe[ids["Frei A"]]

    tasks.set_status(ids["Frei A"], "erledigt")
    d = ablauf.plan()
    nach_id = {x["id"]: x for s in d["stufen"] for x in s["aufgaben"]}
    assert ids["Frei A"] not in nach_id, "erledigt steht nicht mehr im Plan"
    assert nach_id[ids["Frei B"]]["braucht"] == []
    assert nach_id[ids["Frei B"]]["haelt_auf"] == 0


def test_bereichsfilter_zeigt_nur_diesen_bereich(repo):
    d = ablauf.plan(bereich="Elektrik")
    for s in d["stufen"]:
        for a in s["aufgaben"]:
            assert a["bereich"] == "Elektrik"
    for a in d["schluessel"]:
        assert a["bereich"] == "Elektrik"
    assert d["offen_gesamt"] <= ablauf.plan()["offen_gesamt"]


def test_bereichsfilter_behaelt_die_stufen_des_ganzen_plans(repo):
    """Gerechnet wird über alle Bereiche — sonst verschöbe ein Filter die
    Stufen, obwohl die Abhängigkeit bestehen bleibt."""
    ganz = {a["id"]: s["stufe"] for s in ablauf.plan()["stufen"] for a in s["aufgaben"]}
    teil = {a["id"]: s["stufe"]
            for s in ablauf.plan(bereich="Elektrik")["stufen"] for a in s["aufgaben"]}
    for tid, stufe in teil.items():
        assert ganz[tid] == stufe


def test_text_nennt_stufen_und_schluesselaufgaben(repo):
    t = ablauf.text()
    assert "Ablaufplan" in t
    assert "Stufe 1" in t
    if ablauf.plan()["schluessel"]:
        assert "Schlüsselaufgaben" in t


# ------------------------------------------------------------------ Hilfen

def _braucht_setzen(task_id: str, blocker_id: str) -> None:
    """`@braucht:` an eine Aufgabenzeile hängen. Es gibt dafür keinen Befehl —
    Abhängigkeiten pflegt der Nutzer im Vault —, deshalb hier direkt."""
    from tools import common
    from tools.kern import datei as kern_datei

    a = tasks.find(task_id)
    assert a is not None, task_id
    pfad = kern_datei.pfad(a["datei"])
    zeilen = common.read_text(pfad).split("\n")
    i = a["zeile"] - 1
    assert a["titel"] in zeilen[i], f"Zeile {a['zeile']} passt nicht: {zeilen[i]!r}"
    zeilen[i] = zeilen[i].rstrip() + f" @braucht:{blocker_id}"
    common.write_text(pfad, "\n".join(zeilen))
