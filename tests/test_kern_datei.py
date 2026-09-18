import pytest

from tools import common
from tools.kern import datei


def test_rundlauf_bytegleich(repo):
    for p in common.BEREICHE_DIR.glob("*.md"):
        roh = p.read_bytes()
        text, h = datei.lesen(p)
        datei.schreiben(p, text, h)
        assert p.read_bytes() == roh


def test_veralteter_hash_wird_abgelehnt(repo):
    p = next(common.BEREICHE_DIR.glob("*.md"))
    text, h = datei.lesen(p)
    datei.schreiben(p, text + "x", h)
    with pytest.raises(datei.Konflikt) as e:
        datei.schreiben(p, text, h)
    assert e.value.aktuell == datei.version(p)


def test_neue_datei_mit_leerem_hash(repo):
    p = common.RECHERCHE_DIR / "neu.md"
    p.parent.mkdir(exist_ok=True)
    datei.schreiben(p, "# Neu\n", "")
    with pytest.raises(datei.Konflikt):
        datei.schreiben(p, "# Anders\n", "")


def test_rel_und_pfad(repo):
    p = common.PARTS_CSV
    assert datei.rel(p) == "data/parts.csv"
    assert datei.pfad("data/parts.csv") == p
