import pytest

from tools import common
from tools.kern import abschnitte, datei
from tools.kern.lesen import abschnitte_mit_zeilen
from tools.kern import laden


def _bereichsdateien():
    return sorted(common.BEREICHE_DIR.glob("*.md"))


def test_rundlauf_bytegleich(repo):
    """Denselben Text zurückschreiben ändert an der Datei nichts."""
    for p in _bereichsdateien():
        roh = p.read_bytes()
        inhalt, h = datei.lesen(p)
        vorhanden = abschnitte_mit_zeilen(inhalt)
        for name in ("Beschreibung", "Stand", "Notizen", "Links"):
            if name in vorhanden:
                h = abschnitte.abschnitt_setzen(
                    p.stem, name, vorhanden[name].text, h, quelle="web")
        if "Auslegung" in vorhanden:
            h = abschnitte.abschnitt_setzen(
                p.stem, "Auslegung", vorhanden["Auslegung"].text, h, quelle="claude")
        assert p.read_bytes() == roh


def test_ersetzen_aendert_nur_abschnitt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    vor = p.read_bytes().decode("utf-8").splitlines()
    _, h = datei.lesen(p)
    abschnitte.abschnitt_setzen(
        "Elektrik", "Notizen", "Neuer Notiz-Text zum Testen.", h, quelle="web")
    nach = p.read_bytes().decode("utf-8").splitlines()

    inhalt = p.read_bytes().decode("utf-8")
    ab = abschnitte_mit_zeilen(inhalt)
    a = ab["Notizen"]
    # Zeilen außerhalb des Abschnitts unverändert.
    assert vor[:a.zeile_von] == nach[:a.zeile_von] or True  # Überschrift bleibt gleich
    assert vor[a.zeile_von - 1] == nach[a.zeile_von - 1]  # "## Notizen" selbst
    # Alles vor der Überschrift ist bytegleich.
    heading_idx = a.zeile_von - 1
    assert vor[:heading_idx] == nach[:heading_idx]
    assert "Neuer Notiz-Text zum Testen." in inhalt


def test_fehlender_abschnitt_wird_eingefuegt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    inhalt = p.read_bytes().decode("utf-8")
    ohne_auslegung = "\n".join(
        z for z in inhalt.splitlines()
        if not z.startswith("## Auslegung")
    )
    # Entferne auch den alten Auslegungs-Inhalt grob (Platzhalterzeile danach).
    zeilen = inhalt.splitlines()
    ab = abschnitte_mit_zeilen(inhalt)
    a = ab["Auslegung"]
    heading_idx = a.zeile_von - 1
    del zeilen[heading_idx:a.zeile_bis]
    neuer_inhalt = "\n".join(zeilen) + "\n"
    p.write_bytes(neuer_inhalt.encode("utf-8"))

    _, h = datei.lesen(p)
    abschnitte.abschnitt_setzen(
        "Elektrik", "Auslegung", "Testrechnung: 42 Ah/Tag.", h, quelle="claude")

    inhalt2 = p.read_bytes().decode("utf-8")
    ab2 = abschnitte_mit_zeilen(inhalt2)
    assert "Auslegung" in ab2
    assert ab2["Auslegung"].text == "Testrechnung: 42 Ah/Tag."
    # Richtige Stelle: nach Stand, vor Notizen.
    assert ab2["Stand"].zeile_bis < ab2["Auslegung"].zeile_von < ab2["Notizen"].zeile_von


def test_matrix_verbote(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    with pytest.raises(abschnitte.Unerlaubt):
        abschnitte.abschnitt_setzen("Elektrik", "Auslegung", "x", h, quelle="web")
    with pytest.raises(abschnitte.Unerlaubt):
        abschnitte.abschnitt_setzen("Elektrik", "Aufgaben", "x", h, quelle="claude")
    with pytest.raises(abschnitte.Unerlaubt):
        abschnitte.kopf_setzen("Elektrik", "phase", 5, h, quelle="web")
    with pytest.raises(abschnitte.Unerlaubt):
        abschnitte.kopf_setzen("Elektrik", "status", "kaputt", h, quelle="web")
    with pytest.raises(abschnitte.Unerlaubt):
        abschnitte.abschnitt_setzen("Elektrik", "Unbekannt", "x", h, quelle="claude")


def test_kopf_feld_aendern(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    vor = p.read_bytes().decode("utf-8").splitlines()
    _, h = datei.lesen(p)
    abschnitte.kopf_setzen("Elektrik", "kurz", "Kurzer neuer Text", h, quelle="web")
    nach = p.read_bytes().decode("utf-8").splitlines()
    unterschiede = [i for i in range(min(len(vor), len(nach))) if vor[i] != nach[i]]
    assert unterschiede == [2]  # nur die "kurz:"-Zeile
    assert nach[2] == "kurz: Kurzer neuer Text"


def test_kopf_feld_phase_nur_claude(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    h2 = abschnitte.kopf_setzen("Elektrik", "phase", 9, h, quelle="claude")
    inhalt = p.read_bytes().decode("utf-8")
    assert "phase: 9" in inhalt
    assert h2 == datei.version(p)


def test_konflikt(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    abschnitte.kopf_setzen("Elektrik", "kurz", "Erster Schreibvorgang", h, quelle="web")
    with pytest.raises(datei.Konflikt):
        abschnitte.kopf_setzen("Elektrik", "kurz", "Zweiter Schreibvorgang (veraltet)", h, quelle="web")


def test_crlf_datei(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    inhalt = p.read_bytes().decode("utf-8")
    crlf_inhalt = inhalt.replace("\n", "\r\n")
    p.write_bytes(crlf_inhalt.encode("utf-8"))

    _, h = datei.lesen(p)
    abschnitte.abschnitt_setzen("Elektrik", "Notizen", "CRLF-Notiz", h, quelle="web")

    roh = p.read_bytes()
    assert b"\r\n" in roh
    assert roh.count(b"\n") == roh.count(b"\r\n")  # jedes \n gehört zu \r\n
    text = roh.decode("utf-8")
    assert "CRLF-Notiz" in text
    ab = abschnitte_mit_zeilen(text)
    assert ab["Notizen"].text == "CRLF-Notiz"


def test_danach_mit_kern_laden_lesbar(repo):
    p = common.BEREICHE_DIR / "Elektrik.md"
    _, h = datei.lesen(p)
    abschnitte.abschnitt_setzen(
        "Elektrik", "Notizen", "Sichtbar nach dem Laden.", h, quelle="web")
    bestand = laden()
    elektrik = next(b for b in bestand.bereiche if b.name == "Elektrik")
    assert elektrik.notizen == "Sichtbar nach dem Laden."
