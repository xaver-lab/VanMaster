"""Push-Wache: stoppt sie Code auf dem Weg nach main, und nur dort?

Der Hook liegt unter .claude/hooks/ und ist kein Paketmodul, wird hier also
über seinen Pfad geladen.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "push_wache", ROOT / ".claude" / "hooks" / "push_wache.py")
wache = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wache)

# Befehle werden zusammengesetzt, damit die Wache nicht über die eigene
# Testdatei stolpert, wenn sie einen Bash-Befehl mit diesem Inhalt sieht.
SCHIEBEN = "git " + "push"
WEBSITE = "main"
ZWEIG = "claude/neue-ansicht"


# ------------------------------------------------- erkennt sie einen Push?

@pytest.mark.parametrize("befehl", [
    SCHIEBEN,
    f"{SCHIEBEN} origin {WEBSITE}",
    f"{SCHIEBEN} -u origin {WEBSITE}",
    "git -C /pfad " + "push",
])
def test_push_erkannt(befehl):
    assert wache._PUSH.search(befehl)


@pytest.mark.parametrize("befehl", [
    "git status",
    "git log --oneline",
    "echo fertig",
    f"git pull origin {WEBSITE}",
])
def test_kein_push(befehl):
    assert not wache._PUSH.search(befehl)


# ----------------------------------------------------- zielt es auf main?

def test_main_im_befehl_zaehlt():
    assert wache.zielt_auf_website(f"{SCHIEBEN} origin {WEBSITE}", ZWEIG)
    assert wache.zielt_auf_website(f"{SCHIEBEN} origin HEAD:{WEBSITE}", ZWEIG)


def test_eigener_branch_geht_durch():
    assert not wache.zielt_auf_website(f"{SCHIEBEN} -u origin {ZWEIG}", ZWEIG)


def test_nacktes_push_folgt_dem_aktuellen_branch():
    assert wache.zielt_auf_website(SCHIEBEN, WEBSITE)
    assert not wache.zielt_auf_website(SCHIEBEN, ZWEIG)


# ------------------------------------------- was gilt als Code, was als Daten

def test_daten_und_code_getrennt(monkeypatch):
    monkeypatch.setattr(wache, "_git", lambda *a: "\n".join([
        "vault/Bereiche/Elektrik.md",
        "data/parts.csv",
        "tools/build.py",
        "web/src/lib/ui/Karte.svelte",
    ]))
    assert wache.code_dateien("origin/" + WEBSITE) == [
        "tools/build.py", "web/src/lib/ui/Karte.svelte"]


def test_nur_daten_ist_kein_code(monkeypatch):
    monkeypatch.setattr(wache, "_git", lambda *a: "\n".join([
        "vault/Aufgaben.md", "data/bauteile.csv"]))
    assert wache.code_dateien("origin/" + WEBSITE) == []


def test_meldung_verraet_den_weg():
    text = wache.meldung(["tools/build.py"], "origin/" + WEBSITE)
    assert "tools/build.py" in text
    assert wache.FREIGABE in text


def test_meldung_kuerzt_lange_listen():
    text = wache.meldung([f"tools/m{i}.py" for i in range(25)],
                         "origin/" + WEBSITE)
    assert "und 5 weitere" in text
