"""Tests für tools/web.py (UMBAU.md Phase 5) — npm-Suche und die statisch
erzeugten Konfigurationsdateien unter web/. Ruft npm nie wirklich auf."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import web

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


# ------------------------------------------------------------- npm-Suche

def test_npm_pfad_findet_windows_installation(monkeypatch, tmp_path):
    home = tmp_path / "home"
    npm_cmd = home / "nodejs" / "npm.cmd"
    npm_cmd.parent.mkdir(parents=True)
    npm_cmd.write_text("", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)
    assert web.npm_pfad() == npm_cmd


def test_npm_pfad_findet_unix_installation_vor_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    npm = home / "nodejs" / "npm"
    npm.parent.mkdir(parents=True)
    npm.write_text("", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(web.shutil, "which", lambda name: "/anderswo/npm")
    assert web.npm_pfad() == npm


def test_npm_pfad_faellt_auf_path_zurueck(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(web.shutil, "which", lambda name: "/usr/bin/npm")
    assert web.npm_pfad() == Path("/usr/bin/npm")


def test_npm_pfad_none_wenn_nichts_gefunden(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(web.shutil, "which", lambda name: None)
    assert web.npm_pfad() is None


def test_build_ohne_npm_gibt_klare_fehlermeldung(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(web.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as ausnahme:
        web.build()
    assert ausnahme.value.code == 1


def test_install_ohne_npm_gibt_klare_fehlermeldung(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(web.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as ausnahme:
        web.install()
    assert ausnahme.value.code == 1


def test_build_ohne_node_modules_gibt_hinweis_auf_install(monkeypatch, tmp_path):
    npm = tmp_path / "npm"
    npm.write_text("", encoding="utf-8")
    monkeypatch.setattr(web, "npm_pfad", lambda: npm)
    monkeypatch.setattr(web, "WEB_NODE_MODULES", tmp_path / "web-fehlt" / "node_modules")
    with pytest.raises(SystemExit):
        web.build()


def test_npm_lauf_nutzt_shell_nur_fuer_cmd_dateien(monkeypatch, tmp_path):
    aufrufe = []

    def falscher_run(befehl, cwd, shell, **kwargs):
        aufrufe.append((befehl, shell))
        class Ergebnis:
            returncode = 0
        return Ergebnis()

    monkeypatch.setattr(web.subprocess, "run", falscher_run)

    web._npm_lauf(Path("npm.cmd"), ["install"])
    web._npm_lauf(Path("/usr/bin/npm"), ["install"])

    (befehl_cmd, shell_cmd), (befehl_unix, shell_unix) = aufrufe
    assert shell_cmd is True
    assert isinstance(befehl_cmd, str)
    assert shell_unix is False
    assert befehl_unix == ["/usr/bin/npm", "install"]


# ------------------------------------------------------- erzeugte Dateien

def test_package_json_ist_gueltiges_json_und_hat_die_erwarteten_skripte():
    daten = json.loads((WEB_DIR / "package.json").read_text(encoding="utf-8"))
    assert daten["name"] == "vanmaster-web"
    assert daten["private"] is True
    assert daten["type"] == "module"
    for skript in ("dev", "build", "preview", "check"):
        assert skript in daten["scripts"]
    for paket in ("vite", "svelte", "svelte-check", "typescript",
                  "@sveltejs/vite-plugin-svelte", "@tsconfig/svelte"):
        assert paket in daten["devDependencies"], paket


def test_tsconfig_dateien_sind_gueltiges_json():
    for name in ("tsconfig.json", "tsconfig.node.json"):
        json.loads((WEB_DIR / name).read_text(encoding="utf-8"))


def test_tsconfig_erfasst_die_api_typen_und_erweitert_svelte_basis():
    daten = json.loads((WEB_DIR / "tsconfig.json").read_text(encoding="utf-8"))
    assert daten["extends"] == "@tsconfig/svelte/tsconfig.json"
    assert daten["compilerOptions"]["strict"] is True
    eingeschlossen = " ".join(daten["include"])
    assert "src/**/*.ts" in eingeschlossen
    assert "src/**/*.svelte" in eingeschlossen


def test_grundgeruest_dateien_vorhanden():
    for pfad in (
        "vite.config.ts", "svelte.config.js", "index.html",
        "src/main.ts", "src/App.svelte", "src/app.css",
        "src/vite-env.d.ts",
    ):
        assert (WEB_DIR / pfad).exists(), pfad


def test_lib_dateien_nicht_angefasst():
    # tools/server/schema.py erzeugt diese Dateien — sie werden hier nur
    # eingebunden, nicht verändert.
    assert (WEB_DIR / "src" / "lib" / "api-typen.ts").exists()
    schema = json.loads(
        (WEB_DIR / "src" / "lib" / "api-schema.json").read_text(encoding="utf-8")
    )
    assert isinstance(schema, dict)


def test_vite_config_hat_proxy_und_outdir():
    text = (WEB_DIR / "vite.config.ts").read_text(encoding="utf-8")
    assert "outDir: 'dist'" in text
    assert "/api" in text
    assert "127.0.0.1:8765" in text
