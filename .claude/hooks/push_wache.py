#!/usr/bin/env python3
"""Push-Wache — hält Codeänderungen von main und damit von der Website fern.

Claude-Code-Hook (PreToolUse auf Bash, siehe .claude/settings.json). Erkennt
ein ``git push``, das auf ``main`` zielt, und schaut nach, was mitginge:

* nur ``vault/`` und ``data/`` — Inhalte, gehen durch. Das ist der Zweck der
  Kette: Dashboard-Änderung rein, Website neu gebaut.
* irgendetwas anderes — Code, Pipeline, Workflows. Wird gestoppt, damit der
  Nutzer den Stand erst ansieht.

Ein Push auf einen anderen Branch geht immer durch: der Branch *ist* der Weg,
auf dem der Nutzer Code zu sehen bekommt.

Das ist ein Geländer gegen automatisches Durchpushen, keine Sicherheitsgrenze:
wer den Befehl schreibt, kann sie mit VANMASTER_CODE_PUSH=1 auch öffnen. Die
harte Grenze ist der Branch-Schutz auf GitHub (siehe SICHERHEIT.md).

Geprüft wird der Befehlstext. Ein Befehl, der die Wortfolge nur erwähnt, wird
deshalb mitgeprüft — lieber einmal zu viel.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

#: Alles darunter ist Inhalt und darf ohne Rückfrage raus.
DATEN_PRAEFIXE = ("vault/", "data/")

#: Der Branch, von dem die Website gebaut wird.
WEBSITE_BRANCH = "main"

#: Wer das vor den Befehl schreibt, meint es ernst.
FREIGABE = "VANMASTER_CODE_PUSH=1"

_PUSH = re.compile(r"\bgit\b(?:\s+-[^\s]+(?:\s+[^\s]+)?)*\s+push\b")

#: main als ausdrückliches Ziel: "origin main", "HEAD:main", ":main"
_ZIEL_MAIN = re.compile(rf"(?::|\s){WEBSITE_BRANCH}\b")


def _git(*args: str) -> str | None:
    try:
        fertig = subprocess.run(["git", *args], check=True, capture_output=True,
                                text=True, timeout=30)
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return None
    return fertig.stdout.strip()


def zielt_auf_website(befehl: str, aktueller_branch: str | None) -> bool:
    """Geht dieser Push nach main? Entweder steht main im Befehl, oder wir
    stehen auf main und schieben den aktuellen Branch hoch."""
    if _ZIEL_MAIN.search(befehl):
        return True
    # Ein anderer Branch ist ausdrücklich genannt -> nicht main.
    if re.search(r"\bpush\b\s+\S+\s+\S", befehl):
        return False
    return aktueller_branch == WEBSITE_BRANCH


def _basis() -> str | None:
    """Wogegen vergleichen wir? Erst der Upstream, sonst origin/main."""
    upstream = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        return upstream
    if _git("rev-parse", "--verify", "--quiet", f"origin/{WEBSITE_BRANCH}") is not None:
        return f"origin/{WEBSITE_BRANCH}"
    return None


def code_dateien(basis: str) -> list[str]:
    geaendert = _git("diff", "--name-only", f"{basis}...HEAD")
    if not geaendert:
        return []
    return [z for z in geaendert.splitlines()
            if z and not z.startswith(DATEN_PRAEFIXE)]


def meldung(code: list[str], basis: str) -> str:
    liste = "\n".join(f"  - {d}" for d in code[:20])
    if len(code) > 20:
        liste += f"\n  … und {len(code) - 20} weitere"
    return (
        f"Push gestoppt: {len(code)} Code-Datei(en) würden nach {basis} gehen "
        f"und damit direkt auf die Website.\n"
        f"{liste}\n\n"
        "Codeänderungen werden gesammelt und vom Nutzer angesehen, bevor sie "
        "rausgehen (siehe CLAUDE.md, Abschnitt 'Git läuft nebenbei').\n"
        f"Stattdessen: auf einen eigenen Branch pushen, dem Nutzer "
        f"'git diff {basis}..HEAD' anbieten und auf seine Freigabe warten.\n"
        f"Hat er freigegeben, den Befehl mit '{FREIGABE} ' beginnen."
    )


def main() -> int:
    try:
        eingabe = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    if eingabe.get("tool_name") != "Bash":
        return 0
    befehl = (eingabe.get("tool_input") or {}).get("command", "")
    if not _PUSH.search(befehl) or FREIGABE in befehl:
        return 0

    if not zielt_auf_website(befehl, _git("rev-parse", "--abbrev-ref", "HEAD")):
        return 0

    basis = _basis()
    if basis is None:
        return 0

    code = code_dateien(basis)
    if not code:
        return 0

    print(meldung(code, basis), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
