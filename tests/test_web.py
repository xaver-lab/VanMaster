"""Tests für tools/web.py — nur die npm-Suche, kein echter Build (UMBAU.md
Phase 5). monkeypatcht ``Path.home`` und ``shutil.which``, damit nichts vom
echten Rechner (portables Node unter ~/nodejs/ oder System-npm) den Test
beeinflusst."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import web


def test_findet_portables_npm_vor_pfad(tmp_path, monkeypatch):
    """~/nodejs/npm.cmd geht vor, und sein Ordner landet vorne im PATH des
    Kindprozesses — sonst scheitert npm am eigenen Node-Aufruf."""
    nodejs = tmp_path / "nodejs"
    nodejs.mkdir()
    npm_cmd = nodejs / "npm.cmd"
    npm_cmd.write_text("", encoding="utf-8")

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(web.shutil, "which", lambda name: None)
    monkeypatch.setenv("PATH", r"C:\Windows\System32")

    pfad, env = web.npm_pfad()

    assert pfad == npm_cmd
    assert env["PATH"].startswith(str(nodejs))
    assert r"C:\Windows\System32" in env["PATH"]


def test_faellt_auf_system_npm_zurueck(tmp_path, monkeypatch):
    """Kein ~/nodejs/ vorhanden → shutil.which('npm') aus dem PATH."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # kein nodejs/ hier
    system_npm = r"C:\Program Files\nodejs\npm.cmd"
    monkeypatch.setattr(web.shutil, "which",
                        lambda name: system_npm if name == "npm" else None)

    pfad, env = web.npm_pfad()

    assert pfad == Path(system_npm)


def test_ohne_npm_klare_fehlermeldung(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(web.shutil, "which", lambda name: None)

    with pytest.raises(SystemExit):
        web.npm_pfad()

    fehler = capsys.readouterr().err
    assert "npm" in fehler


def test_daten_export_ohne_dist_bricht_ab(repo, capsys):
    """`web daten` setzt einen fertigen `web build` voraus (UMBAU.md Phase 9,
    Lesemodus/GitHub Pages)."""
    with pytest.raises(SystemExit):
        web.daten_export()
    assert "web build" in capsys.readouterr().err


def test_daten_export_schreibt_data_json_und_kopiert_medien(repo):
    """Schreibt web/dist/data.json (gleiche Struktur wie GET /api/daten) und
    kopiert die Web-Bildkopien aus docs/medien (Nebeneffekt von
    media.web_export() innerhalb von daten_json()) nach web/dist/medien."""
    import json as _json

    (web.WEB_DIR / "dist").mkdir(parents=True)
    (web.WEB_DIR / "dist" / "index.html").write_text("<html></html>",
                                                       encoding="utf-8")

    meldung = web.daten_export()

    ziel = web.WEB_DIR / "dist" / "data.json"
    assert ziel.is_file()
    daten = _json.loads(ziel.read_text(encoding="utf-8"))
    assert "bereiche" in daten and "teile" in daten and "medien" in daten

    medien_ziel = web.WEB_DIR / "dist" / "medien"
    assert medien_ziel.is_dir()
    kopiert = [p for p in medien_ziel.rglob("*") if p.is_file()]
    assert len(kopiert) > 0
    assert "data.json geschrieben" in meldung
    assert "medien" in meldung
