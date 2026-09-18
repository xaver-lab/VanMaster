import pytest

from tools import common, kern
from tools.kern import aufgaben, datei


# --------------------------------------------------------------- Rundlauf

def test_rundlauf_alle_bereichsdateien_bytegleich(repo):
    for p in common.BEREICHE_DIR.glob("*.md"):
        roh = p.read_bytes()
        text, h = datei.lesen(p)
        datei.schreiben(p, text, h)
        assert p.read_bytes() == roh


# ------------------------------------------------------------------ anlegen

def test_anlegen_ans_ende_ohne_gruppe(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    vor = p.read_text(encoding="utf-8").splitlines()

    kennung, neuer_hash = aufgaben.anlegen("Elektrik", "Kabelkanal montieren", h)

    assert kennung == "kabelkanal-montieren"
    text_nachher, h2 = datei.lesen(p)
    assert h2 == neuer_hash
    nach = text_nachher.splitlines()
    # nur angehängt, nichts vorher Bestehendes verändert
    assert nach[: len(vor)] == vor
    assert f"^{kennung}" in nach[-1]
    assert nach[-1].startswith("- [ ] Kabelkanal montieren")

    bestand = kern.laden()
    neu = next(a for a in bestand.aufgaben if a.id == kennung)
    assert neu.titel == "Kabelkanal montieren"
    assert neu.status == "offen"
    assert neu.bereich == "Elektrik"


def test_anlegen_in_gruppe(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    vor = p.read_text(encoding="utf-8").splitlines()

    kennung, _ = aufgaben.anlegen(
        "Elektrik", "Sicherung prüfen", h, gruppe="Auslegung")

    nach = p.read_text(encoding="utf-8").splitlines()
    # eine Zeile mehr, eingefügt vor "### Einbau"
    idx_einbau = nach.index("### Einbau")
    assert nach[idx_einbau - 1].startswith("- [ ] Sicherung prüfen")
    assert f"^{kennung}" in nach[idx_einbau - 1]
    # der Rest der Datei bleibt gleich, nur eine Zeile eingeschoben
    assert nach[idx_einbau:] == vor[idx_einbau - 1:]


def test_anlegen_mit_status_prio_beschreibung(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)

    kennung, _ = aufgaben.anlegen(
        "Elektrik", "Testaufgabe", h,
        status="laeuft", prio="hoch", beschreibung="Erste Zeile\nZweite Zeile")

    bestand = kern.laden()
    neu = next(a for a in bestand.aufgaben if a.id == kennung)
    assert neu.status == "laeuft"
    assert neu.prio == "hoch"
    assert neu.beschreibung == "Erste Zeile\nZweite Zeile"


def test_anlegen_unter_eltern(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)

    kennung, _ = aufgaben.anlegen(
        "Elektrik", "Halterung streichen", h, eltern_id="batteriehalterung")

    text = p.read_text(encoding="utf-8")
    zeile = next(z for z in text.splitlines() if f"^{kennung}" in z)
    assert zeile.startswith("  - [ ]")

    bestand = kern.laden()
    eltern = next(a for a in bestand.aufgaben if a.id == "batteriehalterung")
    assert kennung in eltern.kinder
    neu = next(a for a in bestand.aufgaben if a.id == kennung)
    assert neu.eltern == "batteriehalterung"
    assert neu.ebene == 1


def test_anlegen_id_kollision_bekommt_zaehler(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)

    id1, h1 = aufgaben.anlegen("Elektrik", "Testding", h)
    id2, _ = aufgaben.anlegen("Elektrik", "Testding", h1)

    assert id1 == "testding"
    assert id2 == "testding-2"


def test_anlegen_unbekannter_bereich(repo):
    with pytest.raises(ValueError):
        aufgaben.anlegen("Nichtvorhanden", "X", None)


def test_anlegen_konflikt_bei_veraltetem_hash(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    aufgaben.anlegen("Elektrik", "Erste Änderung", h)
    with pytest.raises(datei.Konflikt):
        aufgaben.anlegen("Elektrik", "Zweite Änderung", h)


# -------------------------------------------------------------- status_setzen

def test_status_setzen_aendert_nur_die_box(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    text, h = datei.lesen(p)
    vor = text.splitlines()

    aufgaben.status_setzen("batteriehalterung", "erledigt", h)

    nach = p.read_text(encoding="utf-8").splitlines()
    diffs = [i for i in range(len(vor)) if vor[i] != nach[i]]
    assert len(diffs) == 1
    zeile = nach[diffs[0]]
    assert zeile.startswith("- [x]")
    assert "^batteriehalterung" in zeile

    bestand = kern.laden()
    a = next(a for a in bestand.aufgaben if a.id == "batteriehalterung")
    assert a.status == "erledigt"


def test_status_setzen_unbekannter_wert(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    with pytest.raises(ValueError):
        aufgaben.status_setzen("batteriehalterung", "fertig", h)


def test_status_setzen_unbekannte_id(repo):
    with pytest.raises(ValueError):
        aufgaben.status_setzen("gibt-es-nicht", "erledigt", None)


def test_status_setzen_konflikt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    aufgaben.status_setzen("batteriehalterung", "erledigt", h)
    with pytest.raises(datei.Konflikt):
        aufgaben.status_setzen("batteriehalterung", "laeuft", h)


# --------------------------------------------------------------- titel_setzen

def test_titel_setzen_behaelt_marken(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    text, h = datei.lesen(p)
    vor = text.splitlines()

    aufgaben.titel_setzen("batteriehalterung", "Halterung schweißen", h)

    nach = p.read_text(encoding="utf-8").splitlines()
    diffs = [i for i in range(len(vor)) if vor[i] != nach[i]]
    assert len(diffs) == 1
    zeile = nach[diffs[0]]
    assert zeile == "- [ ] Halterung schweißen ^batteriehalterung @braucht:batteriebank-entscheiden"

    bestand = kern.laden()
    a = next(a for a in bestand.aufgaben if a.id == "batteriehalterung")
    assert a.titel == "Halterung schweißen"
    assert a.braucht == ["batteriebank-entscheiden"]


def test_titel_setzen_ohne_marken(repo):
    # Beispiel ohne Marken über eine Mini-Datei, unabhängig vom realen Bestand
    datei_pfad = common.BEREICHE_DIR / "Mini.md"
    datei_pfad.write_text(
        "---\nbereich: Mini\n---\n\n# Mini\n\n## Aufgaben\n\n"
        "- [ ] Alter Titel ^mini-1\n",
        encoding="utf-8", newline="\n")
    _, h = datei.lesen(datei_pfad)

    aufgaben.titel_setzen("mini-1", "Neuer Titel", h)

    text = datei_pfad.read_text(encoding="utf-8")
    assert "- [ ] Neuer Titel ^mini-1\n" in text


# ---------------------------------------------------------- beschreibung_setzen

def test_beschreibung_setzen_neu(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    text, h = datei.lesen(p)
    vor = text.splitlines()

    aufgaben.beschreibung_setzen(
        "batteriehalterung", "Winkel aus 3mm Alu.\nAn Querträger schrauben.", h)

    nach = p.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, z in enumerate(nach) if "^batteriehalterung" in z)
    assert nach[idx + 1] == "  > Winkel aus 3mm Alu."
    assert nach[idx + 2] == "  > An Querträger schrauben."
    # alles davor unverändert
    assert nach[:idx + 1] == vor[:idx + 1]
    # alles danach (verschoben um die zwei neuen Zeilen) unverändert
    assert nach[idx + 3:] == vor[idx + 1:]

    bestand = kern.laden()
    a = next(a for a in bestand.aufgaben if a.id == "batteriehalterung")
    assert a.beschreibung == "Winkel aus 3mm Alu.\nAn Querträger schrauben."


def test_beschreibung_setzen_ersetzt_bestehende(repo):
    datei_pfad = common.BEREICHE_DIR / "Mini.md"
    datei_pfad.write_text(
        "---\nbereich: Mini\n---\n\n# Mini\n\n## Aufgaben\n\n"
        "- [ ] Titel ^mini-1\n  > Alte Beschreibung\n  - [ ] Unterpunkt ^mini-2\n",
        encoding="utf-8", newline="\n")
    _, h = datei.lesen(datei_pfad)

    aufgaben.beschreibung_setzen("mini-1", "Neue Beschreibung", h)

    text = datei_pfad.read_text(encoding="utf-8")
    zeilen = text.splitlines()
    assert "  > Alte Beschreibung" not in zeilen
    assert "  > Neue Beschreibung" in zeilen
    assert "  - [ ] Unterpunkt ^mini-2" in zeilen


def test_beschreibung_setzen_leer_entfernt(repo):
    datei_pfad = common.BEREICHE_DIR / "Mini.md"
    datei_pfad.write_text(
        "---\nbereich: Mini\n---\n\n# Mini\n\n## Aufgaben\n\n"
        "- [ ] Titel ^mini-1\n  > Beschreibung\n- [ ] Zweite ^mini-2\n",
        encoding="utf-8", newline="\n")
    _, h = datei.lesen(datei_pfad)

    aufgaben.beschreibung_setzen("mini-1", "", h)

    text = datei_pfad.read_text(encoding="utf-8")
    assert "> Beschreibung" not in text
    assert "- [ ] Titel ^mini-1\n- [ ] Zweite ^mini-2\n" in text


def test_beschreibung_setzen_crlf_datei(repo):
    datei_pfad = common.BEREICHE_DIR / "Mini.md"
    inhalt = (
        "---\r\nbereich: Mini\r\n---\r\n\r\n# Mini\r\n\r\n## Aufgaben\r\n\r\n"
        "- [ ] Titel ^mini-1\r\n")
    datei_pfad.write_bytes(inhalt.encode("utf-8"))
    _, h = datei.lesen(datei_pfad)

    aufgaben.beschreibung_setzen("mini-1", "Eine Zeile", h)

    roh = datei_pfad.read_bytes()
    assert b"\r\n  > Eine Zeile\r\n" in roh
    assert b"\n\n" not in roh.replace(b"\r\n", b"")  # keine nackten \n eingeschmuggelt
    assert roh.count(b"\r\n") == roh.count(b"\n")  # jede \n gehoert zu einem \r\n


# --------------------------------------------------------------- prio_setzen

def test_prio_setzen_neu(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    text, h = datei.lesen(p)
    vor = text.splitlines()

    aufgaben.prio_setzen("batteriehalterung", "hoch", h)

    nach = p.read_text(encoding="utf-8").splitlines()
    diffs = [i for i in range(len(vor)) if vor[i] != nach[i]]
    assert len(diffs) == 1
    assert nach[diffs[0]] == (
        "- [ ] Batteriehalterung bauen ^batteriehalterung "
        "@braucht:batteriebank-entscheiden #hoch")


def test_prio_setzen_ersetzt_bestehende(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)

    aufgaben.prio_setzen("strombilanz", "mittel", h)

    bestand = kern.laden()
    a = next(a for a in bestand.aufgaben if a.id == "strombilanz")
    assert a.prio == "mittel"


def test_prio_setzen_leer_entfernt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)

    aufgaben.prio_setzen("strombilanz", "", h)

    text = p.read_text(encoding="utf-8")
    zeile = next(z for z in text.splitlines() if "^strombilanz" in z)
    assert "#kritisch" not in zeile
    assert zeile == "- [/] Strombilanz rechnen (Verbraucher, Tagesbedarf) ^strombilanz"


def test_prio_setzen_unbekannter_wert(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    with pytest.raises(ValueError):
        aufgaben.prio_setzen("strombilanz", "dringend", h)


# ------------------------------------------------------------------- loeschen

def test_loeschen_einfache_aufgabe(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    text, h = datei.lesen(p)
    vor = text.splitlines()

    aufgaben.loeschen("verteilung", h)

    nach = p.read_text(encoding="utf-8").splitlines()
    assert not any("^verteilung" in z for z in nach)
    erwartet = [z for z in vor if "^verteilung" not in z]
    assert nach == erwartet

    bestand = kern.laden()
    assert not any(a.id == "verteilung" for a in bestand.aufgaben)


def test_loeschen_mit_unterpunkten(repo):
    datei_pfad = common.BEREICHE_DIR / "Mini.md"
    datei_pfad.write_text(
        "---\nbereich: Mini\n---\n\n# Mini\n\n## Aufgaben\n\n"
        "- [ ] Titel ^mini-1\n"
        "  > Beschreibung\n"
        "  - [ ] Unterpunkt eins ^mini-2\n"
        "  - [ ] Unterpunkt zwei ^mini-3\n"
        "- [ ] Danach ^mini-4\n",
        encoding="utf-8", newline="\n")
    _, h = datei.lesen(datei_pfad)

    aufgaben.loeschen("mini-1", h)

    text = datei_pfad.read_text(encoding="utf-8")
    assert "mini-1" not in text
    assert "mini-2" not in text
    assert "mini-3" not in text
    assert "- [ ] Danach ^mini-4" in text


def test_loeschen_unbekannte_id(repo):
    with pytest.raises(ValueError):
        aufgaben.loeschen("gibt-es-nicht", None)


def test_loeschen_konflikt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    aufgaben.status_setzen("verteilung", "erledigt", h)
    with pytest.raises(datei.Konflikt):
        aufgaben.loeschen("verteilung", h)
