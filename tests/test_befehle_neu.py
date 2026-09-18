"""Tests für die neuen Befehle aus UMBAU.md Phase 3:
``task add/delete/rename``, ``bereich set``, ``camper check``.

Jeder Befehl wird über ``camper.main(argv)`` aufgerufen, wie ``camper.py``
es selbst tut — Fehlerfälle enden über ``tools.common.fail`` in einem
``SystemExit``.
"""
from __future__ import annotations

import json

import pytest

import camper
from tools import common
from tools.kern.lesen import aufgaben_lesen, bereiche_lesen


# ------------------------------------------------------------------- task add

def test_task_add_legt_aufgabe_an(repo, capsys):
    camper.main(["task", "add", "Elektrik", "Kabelkanal montieren", "--prio", "hoch"])
    out = capsys.readouterr().out
    assert "Angelegt:" in out
    assert "[kabelkanal-montieren]" in out

    aufgabe = next(a for a in aufgaben_lesen() if a.id == "kabelkanal-montieren")
    assert aufgabe.titel == "Kabelkanal montieren"
    assert aufgabe.status == "offen"
    assert aufgabe.prio == "hoch"
    assert aufgabe.bereich == "Elektrik"


def test_task_add_unter_eltern(repo, capsys):
    camper.main(["task", "add", "Elektrik", "Halterung streichen",
                "--unter", "batteriehalterung"])
    out = capsys.readouterr().out
    kennung = out.split("[")[1].split("]")[0]

    aufgabe = next(a for a in aufgaben_lesen() if a.id == kennung)
    assert aufgabe.eltern == "batteriehalterung"


def test_task_add_unbekannter_bereich_bricht_ab(repo, capsys):
    with pytest.raises(SystemExit) as fehler:
        camper.main(["task", "add", "Nirgendwo", "Testaufgabe"])
    assert fehler.value.code != 0
    assert "Nirgendwo" in capsys.readouterr().err


# ---------------------------------------------------------------- task delete

def test_task_delete_entfernt_aufgabe(repo, capsys):
    camper.main(["task", "add", "Elektrik", "Wird geloescht"])
    kennung = "wird-geloescht"
    camper.main(["task", "delete", kennung])
    out = capsys.readouterr().out
    assert "Gelöscht: Wird geloescht" in out
    assert "0 Unterpunkte" in out
    assert not any(a.id == kennung for a in aufgaben_lesen())


def test_task_delete_meldet_unterpunkte(repo, capsys):
    camper.main(["task", "add", "Elektrik", "Elternaufgabe"])
    camper.main(["task", "add", "Elektrik", "Kind eins", "--unter", "elternaufgabe"])
    camper.main(["task", "add", "Elektrik", "Kind zwei", "--unter", "elternaufgabe"])
    capsys.readouterr()

    eltern = next(a for a in aufgaben_lesen() if a.id == "elternaufgabe")
    anzahl_kinder = len(eltern.kinder)
    assert anzahl_kinder == 2

    camper.main(["task", "delete", eltern.id])
    out = capsys.readouterr().out
    assert f"({anzahl_kinder} " in out
    verbleibend = {a.id for a in aufgaben_lesen()}
    assert eltern.id not in verbleibend
    for kind_id in eltern.kinder:
        assert kind_id not in verbleibend


def test_task_delete_unbekannte_id_bricht_ab(repo, capsys):
    with pytest.raises(SystemExit) as fehler:
        camper.main(["task", "delete", "gibt-es-nicht"])
    assert fehler.value.code != 0
    assert "gibt-es-nicht" in capsys.readouterr().err


# ---------------------------------------------------------------- task rename

def test_task_rename_aendert_titel(repo, capsys):
    camper.main(["task", "add", "Elektrik", "Alter Titel"])
    camper.main(["task", "rename", "alter-titel", "Neuer Titel"])
    out = capsys.readouterr().out
    assert "Alter Titel → Neuer Titel" in out
    aufgabe = next(a for a in aufgaben_lesen() if a.id == "alter-titel")
    assert aufgabe.titel == "Neuer Titel"


def test_task_rename_unbekannte_id_bricht_ab(repo):
    with pytest.raises(SystemExit):
        camper.main(["task", "rename", "gibt-es-nicht", "Egal"])


# ------------------------------------------------------------------ task done

def test_task_bestehende_statuswechsel_funktionieren_weiter(repo, capsys):
    aufgabe = aufgaben_lesen()[0]
    camper.main(["task", "done", aufgabe.id])
    out = capsys.readouterr().out
    assert aufgabe.titel in out


# ------------------------------------------------------------------ bereich set

def test_bereich_set_abschnitt_ueber_text(repo, capsys):
    camper.main(["bereich", "set", "Elektrik", "Notizen", "--text", "Neue Notiz"])
    out = capsys.readouterr().out
    assert "Notizen" in out
    b = next(b for b in bereiche_lesen() if b.name == "Elektrik")
    assert b.notizen == "Neue Notiz"


def test_bereich_set_abschnitt_ueber_stdin(repo, capsys, monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("Von stdin gelesen"))
    camper.main(["bereich", "set", "Elektrik", "Notizen"])
    capsys.readouterr()
    b = next(b for b in bereiche_lesen() if b.name == "Elektrik")
    assert b.notizen == "Von stdin gelesen"


def test_bereich_set_auslegung_erlaubt_fuer_claude(repo, capsys):
    camper.main(["bereich", "set", "Elektrik", "Auslegung", "--text", "Neue Auslegung"])
    capsys.readouterr()
    b = next(b for b in bereiche_lesen() if b.name == "Elektrik")
    assert b.auslegung == "Neue Auslegung"


def test_bereich_set_kopf_feld(repo, capsys):
    camper.main(["bereich", "set", "Elektrik", "--kopf", "phase=9"])
    out = capsys.readouterr().out
    assert "phase = 9" in out
    b = next(b for b in bereiche_lesen() if b.name == "Elektrik")
    assert b.phase == 9


def test_bereich_set_unbekannter_bereich_bricht_ab(repo, capsys):
    with pytest.raises(SystemExit) as fehler:
        camper.main(["bereich", "set", "Nirgendwo", "Notizen", "--text", "x"])
    assert fehler.value.code != 0
    assert "Nirgendwo" in capsys.readouterr().err


def test_bereich_set_ungueltiger_status_bricht_ab(repo, capsys):
    with pytest.raises(SystemExit):
        camper.main(["bereich", "set", "Elektrik", "--kopf", "status=quatsch"])


def test_bereich_zeigen_funktioniert_weiterhin(repo, capsys):
    camper.main(["bereich", "Elektrik", "--json"])
    out = capsys.readouterr().out
    daten = json.loads(out)
    assert daten["name"] == "Elektrik"


# ---------------------------------------------------------------------- check

def test_check_ohne_befunde(repo, capsys):
    camper.main(["check"])
    out = capsys.readouterr().out
    assert "Keine Abweichungen" in out


def test_check_json_liefert_liste(repo, capsys):
    camper.main(["check", "--json"])
    out = capsys.readouterr().out
    daten = json.loads(out)
    assert daten == []


def test_check_meldet_fehler_mit_exit_code(repo, capsys):
    pfad = common.BEREICHE_DIR / "Elektrik.md"
    text = pfad.read_text(encoding="utf-8")
    kaputt = text.replace("- [ ] ", "- [q] ", 1)
    assert kaputt != text
    pfad.write_text(kaputt, encoding="utf-8", newline="\n")

    with pytest.raises(SystemExit) as fehler:
        camper.main(["check"])
    assert fehler.value.code == 1
    out = capsys.readouterr().out
    assert "fehler" in out
    assert "Elektrik.md" in out
