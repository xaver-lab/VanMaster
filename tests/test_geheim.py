"""Geheimnis-Wache: schlägt sie an, und schweigt sie beim Rest?

Die Beispiele hier sind erfunden. Jede Zeile mit einem Muster trägt die
Freigabe, damit die Wache sich nicht an ihren eigenen Testdaten verschluckt.
"""
from __future__ import annotations

import subprocess

import pytest

from tools import geheim


def _arten(text: str) -> set[str]:
    return {f.muster for f in geheim.text_pruefen(text, "probe.md")}


# ----------------------------------------------------------- schlägt an

@pytest.mark.parametrize("zeile, muster", [
    ("-----BEGIN RSA PRIVATE KEY-----", "Privater Schlüssel"),  # geheim-ok
    ("ghp_" + "A" * 36, "GitHub-Token"),  # geheim-ok
    ("AKIA" + "B" * 16, "AWS-Schlüssel"),  # geheim-ok
    ('api_key = "abcd1234efgh5678"', "Zugangsdaten-Zuweisung"),  # geheim-ok
    ("passwort: sommer2024xyz", "Zugangsdaten-Zuweisung"),  # geheim-ok
    ("Konto DE02 1203 0000 0000 2020 51", "IBAN"),  # geheim-ok
    ("Fahrgestellnummer: VF1MA000012345678", "Fahrgestellnummer"),  # geheim-ok
    ("Kennzeichen: M-XY 1234", "Kennzeichen"),  # geheim-ok
    ("Telefon: +49 170 1234567", "Telefonnummer"),  # geheim-ok
    ("Stellplatz Koordinaten 47.80123, 13.04567", "Standortkoordinaten"),  # geheim-ok
])
def test_muster_schlaegt_an(zeile, muster):
    assert muster in _arten(zeile)


def test_fehler_und_warnung_getrennt():
    funde = geheim.text_pruefen("AKIA" + "C" * 16, "p.md")  # geheim-ok
    assert [f.art for f in funde] == ["fehler"]
    funde = geheim.text_pruefen("Kennzeichen: S-AB 99", "p.md")  # geheim-ok
    assert [f.art for f in funde] == ["warnung"]


def test_auszug_zeigt_das_geheimnis_nicht():
    token = "ghp_" + "D" * 36  # geheim-ok
    fund, = geheim.text_pruefen(token, "p.md")
    assert token not in fund.auszug
    assert token not in geheim.bericht([fund])
    assert fund.auszug.startswith("ghp")


# ---------------------------------------------------------- schweigt zu

@pytest.mark.parametrize("zeile", [
    "Die Batterie hat 280 Ah bei 12,8 V.",
    "- [ ] Kabel 25 mm² bestellen #hoch",
    "Preis: 1234,56 EUR bei Amazon",
    "Brett 1200 x 600 x 18 mm",
    "token = tokens.pop()",
    "passwort: ",
    'api_key = os.environ["API_KEY"]',
    "commit 4f3a2b1c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a",
])
def test_kein_falscher_alarm(zeile):
    assert geheim.text_pruefen(zeile, "p.md") == []


@pytest.mark.parametrize("zeile", [
    # (?i) galt einmal fürs ganze Muster; dann matchte [A-HJ-NPR-Z0-9]{17}
    # auch Kleinbuchstaben und jeder Fließtext nach dem Schlüsselwort schlug an.
    "Fahrgestellnummer steht im Fahrzeugschein hinten links",
    "Kennzeichen: siehe zulassung",
    "Versicherungsnummer: steht auf der police",
])
def test_schluesselwort_ohne_kennung_ist_still(zeile):
    assert geheim.text_pruefen(zeile, "p.md") == []


def test_freigabe_schaltet_zeile_stumm():
    zeile = "AKIA" + "E" * 16 + "  # " + geheim.FREIGABE
    assert geheim.text_pruefen(zeile, "p.md") == []


def test_erzeugtes_wird_uebersprungen():
    assert geheim._ueberspringen("web/dist/index.js")
    assert geheim._ueberspringen("data/generated/medien/a.jpg")
    assert geheim._ueberspringen("vault/Medien/foto.jpg")
    assert not geheim._ueberspringen("vault/Bereiche/Elektrik.md")


# -------------------------------------------------------- im echten git

@pytest.fixture
def git_repo(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True)
    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    return tmp_path, git


def test_staged_liest_den_index(git_repo):
    pfad, git = git_repo
    datei = pfad / "notiz.md"
    datei.write_text("AKIA" + "F" * 16 + "\n", encoding="utf-8")  # geheim-ok
    git("add", "notiz.md")
    # Arbeitsbaum danach bereinigen — der Index zählt, nicht die Datei.
    datei.write_text("harmlos\n", encoding="utf-8")

    funde = geheim.staged_pruefen(pfad)
    assert [f.muster for f in funde] == ["AWS-Schlüssel"]
    assert funde[0].datei == "notiz.md"


def test_versioniert_findet_nur_verwaltete_dateien(git_repo):
    pfad, git = git_repo
    (pfad / "drin.md").write_text("AKIA" + "G" * 16 + "\n", encoding="utf-8")  # geheim-ok
    (pfad / "draussen.md").write_text("AKIA" + "H" * 16 + "\n", encoding="utf-8")  # geheim-ok
    git("add", "drin.md")
    git("commit", "-q", "-m", "drin")

    funde = geheim.versioniert_pruefen(pfad)
    assert {f.datei for f in funde} == {"drin.md"}


def test_ohne_git_keine_ausnahme(tmp_path):
    assert geheim.versioniert_pruefen(tmp_path) == []
    assert geheim.staged_pruefen(tmp_path) == []
