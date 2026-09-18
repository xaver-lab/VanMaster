"""Test des Datenkerns (tools/kern/): lesen ohne Fehler, gleiches Ergebnis
wie die heutigen tools/tasks.py, tools/parts.py, tools/bauteile.py,
tools/bereiche.py, plus gezielte Fälle mit kleinen Beispieldateien.
"""
from __future__ import annotations

from tools import bauteile, bereiche, common, parts, tasks
from tools.kern import lesen


# ---------------------------------------------------------- echter Bestand

def test_alle_echten_dateien_lesen_ohne_fehler(repo):
    bestand = lesen.laden()
    assert bestand.bereiche
    assert bestand.aufgaben
    assert bestand.teile


def test_aufgaben_wie_tasks_py(repo):
    alt = tasks.load()
    neu = lesen.aufgaben_lesen()
    assert len(neu) == len(alt)

    nach_id_alt = {a["id"]: a for a in alt}
    nach_id_neu = {a.id: a for a in neu}
    assert set(nach_id_alt) == set(nach_id_neu)

    for id_, a in nach_id_alt.items():
        n = nach_id_neu[id_]
        assert n.titel == a["titel"]
        assert n.status == a["status"]
        assert n.prio == a["prio"]
        assert n.dauer == a["dauer"]
        assert n.braucht == a["braucht"]
        assert n.gruppe == a["gruppe"]
        assert n.bereich == a["bereich"]
        assert n.ebene == a["ebene"]
        assert n.eltern == a["eltern"]
        assert sorted(n.kinder) == sorted(a["kinder"])
        assert n.beschreibung == a["beschreibung"]
        # tasks.py liefert den rohen OS-Pfadtrenner, der Kern normalisiert
        # alle datei-Felder einheitlich auf "/".
        assert n.datei == a["datei"].replace("\\", "/")
        assert n.zeile == a["zeile"]


def test_teile_wie_parts_py(repo):
    alt = parts.load()
    neu = lesen.teile_lesen()
    assert len(neu) == len(alt)
    for a, n in zip(alt, neu):
        assert n.id == a["id"]
        assert n.titel == a["titel"]
        assert n.kategorie == a["kategorie"]
        assert n.status == a["status"]
        assert n.prioritaet == a["prioritaet"]
        assert n.preis == a["preis"]
        assert n.menge == a["menge"]


def test_einzelteile_wie_bauteile_py(repo):
    alt = bauteile.load()
    neu = lesen.einzelteile_lesen()
    assert len(neu) == len(alt)
    for a, n in zip(alt, neu):
        assert n.id == a["id"]
        assert n.titel == a["titel"]
        assert n.bereich == a["bereich"]
        assert n.art == a["art"]
        assert n.status == a["status"]


def test_bereiche_wie_bereiche_py(repo):
    alt = bereiche.load()
    neu = lesen.bereiche_lesen()
    assert len(neu) == len(alt)

    nach_name_alt = {b["name"]: b for b in alt}
    nach_name_neu = {b.name: b for b in neu}
    assert set(nach_name_alt) == set(nach_name_neu)

    for name, b in nach_name_alt.items():
        n = nach_name_neu[name]
        assert n.kurz == b["kurz"]
        assert n.status == b["status"]
        assert n.phase == b["phase"]
        assert n.beschreibung == b["beschreibung"]
        assert n.stand == b["stand"]
        assert n.auslegung == b["auslegung"]
        assert n.notizen == b["notizen"]
        assert n.datei == b["datei"]
        assert [l["url"] for l in bereiche.links(n.links_text)] == \
            [l["url"] for l in b["links"]]


# --------------------------------------------------------- gezielte Fälle

def _schreiben(text: str, name: str = "Test.md") -> None:
    (common.BEREICHE_DIR / name).write_text(text, encoding="utf-8", newline="\n")


def test_verschachtelte_aufgabe_beschreibung_marken(repo):
    zeilen = [
        "---",                                                            # 1
        "bereich: Test",                                                  # 2
        "---",                                                            # 3
        "",                                                                # 4
        "# Test",                                                         # 5
        "",                                                                # 6
        "## Aufgaben",                                                    # 7
        "",                                                                # 8
        "- [ ] Hauptaufgabe ^haupt #hoch @braucht:a,b @dauer:2h",         # 9
        "  > Erste Zeile der Beschreibung.",                              # 10
        "  > Zweite Zeile.",                                              # 11
        "  - [x] Unterpunkt eins ^unter1",                                # 12
        "  - [!] Unterpunkt zwei ^unter2",                                # 13
        "- [/] Zweite Hauptaufgabe ^zweite",                              # 14
    ]
    _schreiben("\n".join(zeilen) + "\n")

    aufgaben = {a.id: a for a in lesen.aufgaben_lesen() if a.bereich == "Test"}

    haupt = aufgaben["haupt"]
    assert haupt.status == "offen"
    assert haupt.prio == "hoch"
    assert haupt.braucht == ["a", "b"]
    assert haupt.dauer == "2h"
    assert haupt.beschreibung == "Erste Zeile der Beschreibung.\nZweite Zeile."
    assert haupt.ebene == 0
    assert haupt.zeile == 9
    assert haupt.beschreibung_von == 10
    assert haupt.beschreibung_bis == 11
    assert sorted(haupt.kinder) == ["unter1", "unter2"]
    assert haupt.block_bis == 13

    unter1 = aufgaben["unter1"]
    assert unter1.status == "erledigt"
    assert unter1.ebene == 1
    assert unter1.eltern == "haupt"
    assert unter1.zeile == 12
    assert unter1.block_bis == 12

    unter2 = aufgaben["unter2"]
    assert unter2.status == "blockiert"
    assert unter2.eltern == "haupt"
    assert unter2.zeile == 13
    assert unter2.block_bis == 13

    zweite = aufgaben["zweite"]
    assert zweite.status == "laeuft"
    assert zweite.kinder == []
    assert zweite.zeile == 14
    assert zweite.block_bis == 14


def test_alle_kaestchenzeichen(repo):
    zeilen = [
        "---", "bereich: Kaestchen", "---", "", "# Kaestchen", "",
        "## Aufgaben", "",
        "- [ ] offen ^k-offen",
        "- [/] laeuft ^k-laeuft",
        "- [x] fertig-klein ^k-x",
        "- [X] fertig-gross ^k-X",
        "- [-] verworfen ^k-verworfen",
        "- [!] blockiert ^k-blockiert",
    ]
    _schreiben("\n".join(zeilen) + "\n", "Kaestchen.md")
    aufgaben = {a.id: a.status for a in lesen.aufgaben_lesen()
                if a.bereich == "Kaestchen"}
    assert aufgaben == {
        "k-offen": "offen", "k-laeuft": "laeuft",
        "k-x": "erledigt", "k-X": "erledigt",
        "k-verworfen": "verworfen", "k-blockiert": "blockiert",
    }


def test_querverweis_mit_und_ohne_anzeigetext(repo):
    zeilen = [
        "---", "bereich: Verweise", "---", "", "# Verweise", "",
        "## Notizen", "",
        "Siehe [[Elektrik]] und [[Kein Bereich|Anzeigename]].", "",
        "## Aufgaben", "",
        "- [ ] nix ^nix",
    ]
    _schreiben("\n".join(zeilen) + "\n", "Verweise.md")

    bestand = lesen.laden()
    treffer = [q for q in bestand.querverweise if q.datei.endswith("Verweise.md")]
    assert len(treffer) == 2

    ohne_text = next(q for q in treffer if q.ziel == "Elektrik")
    assert ohne_text.anzeigetext == "Elektrik"
    assert ohne_text.ziel_typ == "bereich"
    assert ohne_text.ziel_id == "Elektrik"

    mit_text = next(q for q in treffer if q.ziel == "Kein Bereich")
    assert mit_text.anzeigetext == "Anzeigename"
    assert mit_text.ziel_typ is None
    assert mit_text.ziel_id is None
    assert mit_text.zeile == ohne_text.zeile
