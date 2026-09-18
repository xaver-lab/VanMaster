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
