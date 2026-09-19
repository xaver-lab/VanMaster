#!/usr/bin/env python3
"""Push-Wache — trennt Datenänderungen von Codeänderungen.

Claude-Code-Hook (PreToolUse auf Bash, siehe .claude/settings.json). Erkennt
ein ``git push`` und schaut nach, was damit auf main und damit auf die Website
ginge:

* nur ``vault/`` und ``data/`` — Inhalte, gehen durch.
* irgendetwas anderes — Code, Pipeline, Workflows. Wird gestoppt, damit der
  Nutzer den Stand erst ansieht.

Das ist ein Geländer gegen automatisches Durchpushen, keine Sicherheitsgrenze:
wer den Befehl schreibt, kann sie mit VANMASTER_CODE_PUSH=1 auch öffnen. Die
harte Grenze ist der Branch-Schutz auf GitHub (siehe SICHERHEIT.md).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

#: Alles darunter ist Inhalt und darf ohne Rückfrage raus.
DATEN_PRAEFIXE = ("vault/", "data/")

#: Wer das vor den Befehl schreibt, meint es ernst.
FREIGABE = "VANMASTER_CODE_PUSH=1"

_PUSH = re.compile(r"\bgit\b(?:\s+-[^\s]+(?:\s+[^\s]+)?)*\s+push\b")


def _git(*args: str) -> str | None:
    try:
        fertig = subprocess.run(["git", *args], check=True, capture_output=True,
                                text=True, timeout=30)
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return None
    return fertig.stdout.strip()


def _basis() -> str | None:
    """Wogegen vergleichen wir? Erst der Upstream, sonst origin/main."""
    upstream = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        return upstream
    if _git("rev-parse", "--verify", "--quiet", "origin/main") is not None:
        return "origin/main"
    return None


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

    basis = _basis()
    if basis is None:
        # Neuer Branch ohne Upstream und ohne origin/main: nichts zu vergleichen.
        return 0

    geaendert = _git("diff", "--name-only", f"{basis}...HEAD")
    if not geaendert:
        return 0

    dateien = [z for z in geaendert.splitlines() if z]
    code = [d for d in dateien if not d.startswith(DATEN_PRAEFIXE)]
    if not code:
        return 0

    liste = "\n".join(f"  - {d}" for d in code[:20])
    if len(code) > 20:
        liste += f"\n  … und {len(code) - 20} weitere"
    print(
        f"Push gestoppt: {len(code)} Code-Datei(en) würden nach {basis} gehen "
        f"und damit direkt auf die Website.\n"
        f"{liste}\n\n"
        "Codeänderungen werden gesammelt und vom Nutzer angesehen, bevor sie "
        "rausgehen (siehe CLAUDE.md, Abschnitt 'Git läuft nebenbei').\n"
        "Stattdessen: lokal committen, dem Nutzer 'git diff "
        f"{basis}..HEAD' anbieten und auf seine Freigabe warten.\n"
        f"Hat er freigegeben, den Befehl mit '{FREIGABE} ' beginnen.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
