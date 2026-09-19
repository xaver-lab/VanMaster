"""Tests für tools/kern/pruefen.py — echter Bestand fehlerfrei, je Regel ein
kaputtes Beispiel im tmp-Repo (Fixture ``repo``)."""
from __future__ import annotations

import csv

from tools import common
import importlib

# Das Modul, nicht die gleichnamige Funktion aus tools.kern.
pruefen = importlib.import_module("tools.kern.pruefen")


def _schreiben(pfad, text: str) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(text, encoding="utf-8", newline="\n")


def _csv_erste_datenzeile_aendern(pfad, feld: str, wert: str) -> None:
    """Ändert `feld` in der ersten Datenzeile (Zeile 2), CSV-sicher (Anführung)."""
    with pfad.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    kopf = rows[0]
    idx = kopf.index(feld)
    rows[1][idx] = wert
    with pfad.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def _bereichsdatei(name: str, *, kopf_bereich: str | None = "Test",
                   status: str = "geplant", phase: str = "1",
                   aufgaben: str = "") -> str:
    kopf_zeilen = ["---"]
    if kopf_bereich is not None:
        kopf_zeilen.append(f"bereich: {kopf_bereich}")
    kopf_zeilen.append(f"status: {status}")
    kopf_zeilen.append(f"phase: {phase}")
    kopf_zeilen.append("---")
    kopf = "\n".join(kopf_zeilen)
    return (
        f"{kopf}\n\n# {name}\n\n"
        "## Beschreibung\n\ntext\n\n"
        "## Stand\n\ntext\n\n"
        "## Auslegung\n\ntext\n\n"
        "## Notizen\n\ntext\n\n"
        "## Links\n\ntext\n\n"
        f"## Aufgaben\n\n{aufgaben}\n"
    )


def _befund(befunde, teiltext: str):
    treffer = [b for b in befunde if teiltext in b.meldung]
    assert treffer, f"kein Befund mit '{teiltext}' in {[b.meldung for b in befunde]}"
    return treffer[0]


# --------------------------------------------------------------- echter Bestand

def test_echter_bestand_ohne_fehler(repo):
    befunde = pruefen.pruefen()
    fehler = [b for b in befunde if b.art == "fehler"]
    assert fehler == []


# ------------------------------------------------------------------ Bereichskopf

def test_bereich_fehlt_im_kopf(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", kopf_bereich=None))
    b = _befund(pruefen.pruefen(), "bereich fehlt")
    assert b.datei == "vault/Bereiche/Test.md"
    assert b.art == "fehler"


def test_bereich_passt_nicht_zum_dateinamen(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", kopf_bereich="Anders"))
    b = _befund(pruefen.pruefen(), "passt nicht zum Dateinamen")
    assert b.datei == "vault/Bereiche/Test.md"
    assert b.zeile == 2


def test_status_ungueltig(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", status="fertigish"))
    b = _befund(pruefen.pruefen(), "status 'fertigish'")
    assert b.zeile == 3


def test_phase_keine_ganze_zahl(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", phase="bald"))
    b = _befund(pruefen.pruefen(), "phase muss eine ganze Zahl sein")
    assert b.zeile == 4


# --------------------------------------------------------------------- Abschnitte

def test_abschnitt_fehlt(repo):
    p = common.BEREICHE_DIR / "Test.md"
    text = _bereichsdatei("Test").replace("## Links\n\ntext\n\n", "")
    _schreiben(p, text)
    _befund(pruefen.pruefen(), "'## Links' fehlt")


def test_abschnitt_fremd(repo):
    p = common.BEREICHE_DIR / "Test.md"
    text = _bereichsdatei("Test").replace(
        "## Notizen\n\ntext\n\n", "## Notizen\n\ntext\n\n## Sonstiges\n\ntext\n\n")
    _schreiben(p, text)
    _befund(pruefen.pruefen(), "unbekannter Abschnitt '## Sonstiges'")


def test_abschnitt_reihenfolge_falsch(repo):
    p = common.BEREICHE_DIR / "Test.md"
    kopf = "---\nbereich: Test\nstatus: geplant\nphase: 1\n---\n\n# Test\n\n"
    text = (
        kopf
        + "## Stand\n\ntext\n\n"
        + "## Beschreibung\n\ntext\n\n"
        + "## Auslegung\n\ntext\n\n"
        + "## Notizen\n\ntext\n\n"
        + "## Links\n\ntext\n\n"
        + "## Aufgaben\n\n\n"
    )
    _schreiben(p, text)
    _befund(pruefen.pruefen(), "Reihenfolge")


# ----------------------------------------------------------------------- Aufgaben

def test_anker_fehlt(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", aufgaben="- [ ] Ohne Anker\n"))
    b = _befund(pruefen.pruefen(), "Anker (^id) fehlt")
    assert b.zeile > 0


def test_anker_nicht_eindeutig(repo):
    p = common.BEREICHE_DIR / "Test.md"
    aufgaben = "- [ ] Eins ^dupliziert\n- [ ] Zwei ^dupliziert\n"
    _schreiben(p, _bereichsdatei("Test", aufgaben=aufgaben))
    _befund(pruefen.pruefen(), "Anker ^dupliziert ist nicht eindeutig")


def test_unbekanntes_kaestchenzeichen(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", aufgaben="- [?] Kaputt ^kaputt\n"))
    _befund(pruefen.pruefen(), "unbekanntes Kästchenzeichen '?'")


def test_ungueltige_prioritaet(repo):
    p = common.BEREICHE_DIR / "Test.md"
    _schreiben(p, _bereichsdatei("Test", aufgaben="- [ ] Text ^prio #dringend\n"))
    _befund(pruefen.pruefen(), "ungültige Priorität '#dringend'")


def test_einzug_nicht_in_zweierschritten(repo):
    p = common.BEREICHE_DIR / "Test.md"
    aufgaben = "- [ ] Oben ^oben\n   - [ ] Unten ^unten\n"  # 3 Leerzeichen Einzug
    _schreiben(p, _bereichsdatei("Test", aufgaben=aufgaben))
    _befund(pruefen.pruefen(), "Einzug ist nicht in Zweierschritten")


def test_braucht_zeigt_auf_unbekannte_aufgabe(repo):
    p = common.BEREICHE_DIR / "Test.md"
    aufgaben = "- [ ] Text ^eigene @braucht:nichtvorhanden\n"
    _schreiben(p, _bereichsdatei("Test", aufgaben=aufgaben))
    _befund(pruefen.pruefen(), "@braucht:nichtvorhanden zeigt auf keine bekannte Aufgabe")


def test_abhaengigkeitskreis(repo):
    p = common.BEREICHE_DIR / "Test.md"
    aufgaben = (
        "- [ ] Eins ^eins @braucht:zwei\n"
        "- [ ] Zwei ^zwei @braucht:eins\n"
    )
    _schreiben(p, _bereichsdatei("Test", aufgaben=aufgaben))
    _befund(pruefen.pruefen(), "Abhängigkeitskreis")


# ------------------------------------------------------------------ Querverweise

def test_querverweis_ohne_ziel(repo):
    p = common.BEREICHE_DIR / "Test.md"
    text = _bereichsdatei("Test").replace(
        "## Notizen\n\ntext\n\n", "## Notizen\n\nSiehe [[Nirgendwo]].\n\n")
    _schreiben(p, text)
    b = _befund(pruefen.pruefen(), "Querverweis [[Nirgendwo]] ohne Ziel")
    assert b.art == "warnung"


# ----------------------------------------------------- Anleitungen/Recherche

def test_anleitung_abschnitt_fehlt(repo):
    p = common.ANLEITUNGEN_DIR / "Testanleitung.md"
    _schreiben(p, "---\nstatus: offen\nbereich: Test\n---\n\n"
                  "# Testanleitung\n\n## Material\n\ntext\n\n## Schritte\n\ntext\n")
    _befund(pruefen.pruefen(), "'## Werkzeug' fehlt")


def test_recherche_abschnitt_reihenfolge(repo):
    p = common.RECHERCHE_DIR / "Testrecherche.md"
    _schreiben(p, "---\nstatus: offen\nbereich: Test\n---\n\n"
                  "# Testrecherche\n\n## Quellen\n\ntext\n\n"
                  "## Frage\n\ntext\n\n## Ergebnis\n\ntext\n")
    _befund(pruefen.pruefen(), "Reihenfolge")


# --------------------------------------------------------------------------- CSV

def test_csv_kopfzeile_falsch(repo):
    zeilen = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    zeilen[0] = zeilen[0].replace("titel", "name")
    common.PARTS_CSV.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")
    b = _befund(pruefen.pruefen(), "Kopfzeile weicht")
    assert b.datei == "data/parts.csv"
    assert b.zeile == 1


def test_csv_id_nicht_eindeutig(repo):
    with common.PARTS_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    rows[1][0] = "doppel-id"
    rows[2][0] = "doppel-id"
    with common.PARTS_CSV.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    b = _befund(pruefen.pruefen(), "id 'doppel-id' ist nicht eindeutig")
    assert b.zeile == 3


def test_csv_status_ungueltig(repo):
    _csv_erste_datenzeile_aendern(common.PARTS_CSV, "status", "Kaputt")
    _befund(pruefen.pruefen(), "status 'Kaputt' ist nicht erlaubt")


def test_csv_menge_keine_zahl(repo):
    _csv_erste_datenzeile_aendern(common.PARTS_CSV, "menge", "viele")
    _befund(pruefen.pruefen(), "menge 'viele' ist keine Zahl")


def test_csv_fuer_aufgabe_unbekannt(repo):
    _csv_erste_datenzeile_aendern(common.PARTS_CSV, "fuer_aufgabe", "nichtvorhanden")
    b = _befund(pruefen.pruefen(), "fuer_aufgabe 'nichtvorhanden'")
    assert b.art == "warnung"


def test_bauteile_art_ungueltig(repo):
    zeile = ("testbauteil,Test,Möbel,Kaputtart,Multiplex,100,50,15,1,,,gemessen,"
             "Idee,,\n")
    with common.BAUTEILE_CSV.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(zeile)
    _befund(pruefen.pruefen(), "art 'Kaputtart' ist nicht erlaubt")


def test_bauteile_teil_id_unbekannt(repo):
    zeile = ("testbauteil2,Test,Möbel,Platte,Multiplex,100,50,15,1,"
             "nichtvorhanden,,gemessen,Idee,,\n")
    with common.BAUTEILE_CSV.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(zeile)
    b = _befund(pruefen.pruefen(), "teil_id 'nichtvorhanden'")
    assert b.art == "warnung"


def test_bauteile_gewicht_kg_keine_zahl(repo):
    zeile = ("testbauteil3,Test,Möbel,Platte,Multiplex,100,50,15,1,,,gemessen,"
             "Idee,viel,\n")
    with common.BAUTEILE_CSV.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(zeile)
    _befund(pruefen.pruefen(), "gewicht_kg 'viel' ist keine Zahl")
