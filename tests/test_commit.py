"""Tests für tools/server/commit.py — eigenes Git-Repo in tmp_path, das
echte Repo wird nie berührt."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from tools.server.commit import Sammler, anmelden


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True,
    )


def _log_zeilen(repo: Path) -> list[str]:
    r = subprocess.run(
        ["git", "log", "--format=%s"], cwd=repo, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return []
    return r.stdout.splitlines()


@pytest.fixture
def git_repo(tmp_path) -> Path:
    repo = tmp_path
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "a.md").write_text("erste Version\n", encoding="utf-8")
    (repo / "b.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    (repo / "c.md").write_text("unberührt\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "Start")
    return repo


def test_buendelt_mehrere_aenderungen_zu_einem_commit(git_repo):
    sammler = Sammler(ruhe_sekunden=0.2, repo=git_repo)
    (git_repo / "a.md").write_text("zweite Version\n", encoding="utf-8")
    sammler.melden("a.md")
    time.sleep(0.05)
    (git_repo / "b.csv").write_text("x,y\n1,3\n", encoding="utf-8")
    sammler.melden("b.csv")

    time.sleep(0.6)

    zeilen = _log_zeilen(git_repo)
    assert len(zeilen) == 2  # Start + neuer Commit
    assert zeilen[0].startswith("Web:")
    assert "\n" not in zeilen[0]
    status = _git(git_repo, "status", "--porcelain").stdout
    assert status.strip() == ""


def test_nur_gesammelte_dateien_landen_im_commit(git_repo):
    sammler = Sammler(ruhe_sekunden=0.2, repo=git_repo)
    (git_repo / "a.md").write_text("zweite Version\n", encoding="utf-8")
    sammler.melden("a.md")
    # Fremde Änderung, nie gemeldet.
    (git_repo / "c.md").write_text("doch geändert\n", encoding="utf-8")

    time.sleep(0.6)

    status = _git(git_repo, "status", "--porcelain").stdout
    assert "c.md" in status
    assert "a.md" not in status
    zeilen = _log_zeilen(git_repo)
    assert len(zeilen) == 2
    letzter_commit = _git(git_repo, "show", "--name-only", "--format=", "HEAD").stdout
    assert "a.md" in letzter_commit
    assert "c.md" not in letzter_commit


def test_vermerken_liefert_beschreibung_in_der_nachricht(git_repo):
    sammler = Sammler(ruhe_sekunden=0.2, repo=git_repo)
    (git_repo / "a.md").write_text("zweite Version\n", encoding="utf-8")
    sammler.melden("a.md")
    sammler.vermerken("a.md", "Elektrik")

    time.sleep(0.6)

    zeilen = _log_zeilen(git_repo)
    assert "Elektrik" in zeilen[0]


def test_jetzt_committen_ohne_wartezeit(git_repo):
    sammler = Sammler(ruhe_sekunden=60, repo=git_repo)
    (git_repo / "a.md").write_text("zweite Version\n", encoding="utf-8")
    sammler.melden("a.md")

    sammler.jetzt_committen()

    zeilen = _log_zeilen(git_repo)
    assert len(zeilen) == 2


def test_keine_aenderung_kein_commit(git_repo):
    sammler = Sammler(ruhe_sekunden=0.2, repo=git_repo)
    # Meldet die Datei, ändert sie aber inhaltlich nicht.
    sammler.melden("a.md")

    time.sleep(0.6)

    zeilen = _log_zeilen(git_repo)
    assert len(zeilen) == 1


def test_git_fehler_fuehrt_nicht_zum_absturz(tmp_path):
    # Kein Git-Repo hier -> git status schlägt fehl.
    sammler = Sammler(ruhe_sekunden=0.2, repo=tmp_path)
    sammler.melden("irgendwas.md")
    time.sleep(0.5)  # darf nicht werfen / den Test abbrechen


def test_anmelden_haengt_sich_in_nach_schreiben_ein():
    class FakeState:
        nach_schreiben: list = []

    class FakeApp:
        state = FakeState()

    app = FakeApp()
    sammler = anmelden(app, ruhe_sekunden=60)
    assert sammler.melden in app.state.nach_schreiben
