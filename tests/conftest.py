"""Testgerüst: jeder Test arbeitet auf einer Kopie von vault/ und data/.

Die Pfadkonstanten in allen geladenen `tools`-Modulen werden auf die Kopie
umgebogen, damit kein Test das echte Repo berührt.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib  # noqa: E402
import pkgutil  # noqa: E402

import tools  # noqa: E402
from tools import common  # noqa: E402

# Alle Module vorab laden, damit ihre Pfadkonstanten mit umgebogen werden.
# ui braucht ein Fenster und bleibt draußen.
for _info in pkgutil.walk_packages(tools.__path__, "tools."):
    if _info.name != "tools.ui":
        importlib.import_module(_info.name)


def _tools_module():
    return [m for n, m in list(sys.modules.items())
            if m is not None and (n == "tools" or n.startswith("tools."))]


@pytest.fixture
def repo(tmp_path, monkeypatch) -> Path:
    """Kopie von vault/ und data/ unter tmp_path; liefert die neue Wurzel."""
    shutil.copytree(ROOT / "vault", tmp_path / "vault")
    shutil.copytree(ROOT / "data", tmp_path / "data",
                    ignore=shutil.ignore_patterns("generated"))
    (tmp_path / "data" / "generated").mkdir()
    (tmp_path / "_input").mkdir()

    echt = common.ROOT
    for modul in _tools_module():
        for name, wert in list(vars(modul).items()):
            if isinstance(wert, Path) and wert.is_relative_to(echt):
                monkeypatch.setattr(modul, name,
                                    tmp_path / wert.relative_to(echt))
    return tmp_path
