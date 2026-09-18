import pytest

from tools import common
from tools.kern import datei, laden
from tools.kern import tabellen
from tools import parts as parts_alt


def _version(pfad):
    return datei.lesen(pfad)[0], datei.version(pfad)


# --------------------------------------------------------------------- Teile

def test_teil_feld_aendern_rundlauf_bytegleich(repo):
    roh = common.PARTS_CSV.read_bytes()
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "notiz", "Angebot",
                              version, quelle="claude")
    assert common.PARTS_CSV.read_bytes() == roh


def test_teil_feld_aendern_beruehrt_genau_eine_zeile(repo):
    vorher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "status", "Bestellt",
                              version, quelle="web")
    nachher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    assert len(vorher) == len(nachher)
    unterschiede = [i for i, (a, b) in enumerate(zip(vorher, nachher)) if a != b]
    assert unterschiede == [
        i for i, z in enumerate(vorher) if z.startswith("aufbaubatterie-lifepo4,")
    ]
    assert len(unterschiede) == 1


def test_teil_feld_aendern_kopf_und_spaltenreihenfolge_unveraendert(repo):
    kopf_vorher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()[0]
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "status", "Bestellt",
                              version, quelle="web")
    kopf_nachher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()[0]
    assert kopf_vorher == kopf_nachher
    from tools.kern.format import TEIL_FELDER
    assert kopf_nachher.split(",") == TEIL_FELDER


def test_teil_anlegen(repo):
    _, version = _version(common.PARTS_CSV)
    vorher_zeilen = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    neue_id, neuer_hash = tabellen.teil_anlegen(
        {"titel": "Testschraube", "kategorie": "Werkzeug"}, version, quelle="web")
    assert neue_id == "testschraube"
    assert neuer_hash == datei.version(common.PARTS_CSV)
    nachher_zeilen = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    assert nachher_zeilen[:len(vorher_zeilen)] == vorher_zeilen
    assert len(nachher_zeilen) == len(vorher_zeilen) + 1
    zeile = nachher_zeilen[-1]
    assert zeile.startswith("testschraube,Testschraube,,Werkzeug,1,Stk,,Idee,Mittel,")

    bestand = laden()
    teil = next(t for t in bestand.teile if t.id == "testschraube")
    assert teil.titel == "Testschraube"
    alte = {r["id"] for r in parts_alt.load() if r["id"] != "testschraube"}
    rows = parts_alt.load()
    assert any(r["id"] == "testschraube" for r in rows)
    assert {r["id"] for r in rows} - alte == {"testschraube"}


def test_teil_anlegen_eindeutige_id(repo):
    _, version = _version(common.PARTS_CSV)
    neue_id, hash1 = tabellen.teil_anlegen(
        {"titel": "Dachfenster", "kategorie": "Möbel"}, version, quelle="claude")
    assert neue_id == "dachfenster-2"


def test_teil_loeschen(repo):
    _, version = _version(common.PARTS_CSV)
    vorher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    tabellen.teil_loeschen("eisenwinkel", version)
    nachher = common.PARTS_CSV.read_text(encoding="utf-8").splitlines()
    assert len(nachher) == len(vorher) - 1
    assert not any(z.startswith("eisenwinkel,") for z in nachher)
    rest = [z for z in vorher if not z.startswith("eisenwinkel,")]
    assert nachher == rest


def test_teil_validierungsfehler_status(repo):
    _, version = _version(common.PARTS_CSV)
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "status", "Quatsch",
                                  version, quelle="claude")


def test_teil_validierungsfehler_zahl_mit_komma(repo):
    _, version = _version(common.PARTS_CSV)
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "preis", "12,50",
                                  version, quelle="claude")


def test_teil_validierungsfehler_datum(repo):
    _, version = _version(common.PARTS_CSV)
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "gekauft_am",
                                  "18.9.2026", version, quelle="claude")


def test_teil_id_nie_aenderbar(repo):
    _, version = _version(common.PARTS_CSV)
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "id", "anders",
                                  version, quelle="claude")


def test_teil_matrix_verbot_web(repo):
    _, version = _version(common.PARTS_CSV)
    # 'beschreibung' ist laut FORMAT.md §8/§10 nur Claude editierbar.
    with pytest.raises(tabellen.Ungueltig):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "beschreibung",
                                  "Neuer Text", version, quelle="web")


def test_teil_matrix_erlaubt_fuer_claude(repo):
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "beschreibung",
                              "Neuer Text", version, quelle="claude")


def test_teil_konflikt(repo):
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "notiz", "Erstens",
                              version, quelle="claude")
    with pytest.raises(datei.Konflikt):
        tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "notiz", "Zweitens",
                                  version, quelle="claude")


# -------------------------------------------------------------- Einzelteile

def test_einzelteil_anlegen_in_leerer_datei(repo):
    _, version = _version(common.BAUTEILE_CSV)
    neue_id, neuer_hash = tabellen.einzelteil_anlegen(
        {"titel": "Bodenlatte", "bereich": "Dämmung", "art": "Leiste",
         "laenge_mm": "1200", "breite_mm": "40", "dicke_mm": "18"},
        version, quelle="web")
    assert neue_id == "bodenlatte"
    text = common.BAUTEILE_CSV.read_text(encoding="utf-8")
    zeilen = text.splitlines()
    assert len(zeilen) == 2
    from tools.kern.format import EINZELTEIL_FELDER
    assert zeilen[0].split(",") == EINZELTEIL_FELDER
    assert zeilen[1].startswith("bodenlatte,Bodenlatte,Dämmung,Leiste,,1200,40,18,1,")

    bestand = laden()
    assert len(bestand.einzelteile) == 1
    assert bestand.einzelteile[0].id == "bodenlatte"


def test_einzelteil_zweite_zeile_beruehrt_nur_diese(repo):
    _, version = _version(common.BAUTEILE_CSV)
    _, hash1 = tabellen.einzelteil_anlegen(
        {"titel": "Bodenlatte 1", "bereich": "Dämmung"}, version, quelle="web")
    _, hash2 = tabellen.einzelteil_anlegen(
        {"titel": "Bodenlatte 2", "bereich": "Dämmung"}, hash1, quelle="web")
    vorher = common.BAUTEILE_CSV.read_text(encoding="utf-8").splitlines()
    tabellen.einzelteil_feld_setzen("bodenlatte-1", "status", "Geplant",
                                    hash2, quelle="web")
    nachher = common.BAUTEILE_CSV.read_text(encoding="utf-8").splitlines()
    unterschiede = [i for i, (a, b) in enumerate(zip(vorher, nachher)) if a != b]
    assert len(unterschiede) == 1
    assert vorher[unterschiede[0]].startswith("bodenlatte-1,")


def test_einzelteil_komplett_bearbeitbar_im_web_ausser_id(repo):
    _, version = _version(common.BAUTEILE_CSV)
    _, hash1 = tabellen.einzelteil_anlegen(
        {"titel": "Regalbrett", "bereich": "Möbel"}, version, quelle="web")
    # jedes Feld außer id im Web änderbar:
    tabellen.einzelteil_feld_setzen("regalbrett", "material", "Multiplex",
                                    hash1, quelle="web")
    with pytest.raises(tabellen.Ungueltig):
        tabellen.einzelteil_feld_setzen("regalbrett", "id", "anders",
                                        datei.version(common.BAUTEILE_CSV),
                                        quelle="web")


def test_einzelteil_validierungsfehler_art(repo):
    _, version = _version(common.BAUTEILE_CSV)
    with pytest.raises(tabellen.Ungueltig):
        tabellen.einzelteil_anlegen(
            {"titel": "Regalbrett", "bereich": "Möbel", "art": "Quatsch"},
            version, quelle="web")


def test_einzelteil_loeschen(repo):
    _, version = _version(common.BAUTEILE_CSV)
    _, hash1 = tabellen.einzelteil_anlegen(
        {"titel": "Regalbrett", "bereich": "Möbel"}, version, quelle="web")
    tabellen.einzelteil_loeschen("regalbrett", hash1)
    text = common.BAUTEILE_CSV.read_text(encoding="utf-8")
    assert text.splitlines() == [
        common.BAUTEILE_CSV.read_text(encoding="utf-8").splitlines()[0]
    ]


def test_einzelteil_konflikt(repo):
    _, version = _version(common.BAUTEILE_CSV)
    tabellen.einzelteil_anlegen({"titel": "Regalbrett", "bereich": "Möbel"},
                                version, quelle="web")
    with pytest.raises(datei.Konflikt):
        tabellen.einzelteil_anlegen({"titel": "Zweites Brett", "bereich": "Möbel"},
                                    version, quelle="web")


# ------------------------------------------------------ weiterhin lesbar

def test_nach_schreiben_mit_altem_parts_modul_lesbar(repo):
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "status", "Bestellt",
                              version, quelle="web")
    rows = parts_alt.load()
    row = parts_alt.find("aufbaubatterie-lifepo4", rows)
    assert row is not None
    assert row["status"] == "Bestellt"


def test_nach_schreiben_mit_kern_laden_lesbar(repo):
    _, version = _version(common.PARTS_CSV)
    tabellen.teil_feld_setzen("aufbaubatterie-lifepo4", "status", "Bestellt",
                              version, quelle="web")
    bestand = laden()
    teil = next(t for t in bestand.teile if t.id == "aufbaubatterie-lifepo4")
    assert teil.status == "Bestellt"
