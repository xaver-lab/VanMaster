# VanMaster — Projektregeln

Renault Master 2013, Selbstausbau zum Vollzeit-Campervan.
Gesamtplan: `PLAN.md`. Diese Datei gilt für alles unterhalb von `Camper/`.

## Vorrang vor der übergeordneten CLAUDE.md

Die Regeln des übergeordneten Schreibprojekts (`Privat/CLAUDE.md`) gelten hier
**nicht**. Konkret:

- Eigene Websuche ist erwünscht, nicht nur Suchvorschläge.
- Texte dürfen geschrieben, umformuliert und strukturiert werden.

## Datenhaltung

- Einzige Wahrheit: `data/parts.csv`, `data/bauteile.csv` und die
  Markdown-Dateien in `vault/`.
- Ein Bereich ist ein Arbeitsraum: `vault/Bereiche/<Name>.md` mit den festen
  Abschnitten Beschreibung, Stand, Auslegung, Notizen, Links, Aufgaben — in
  dieser Reihenfolge. Aufgaben werden nur unter `## Aufgaben` gelesen.
- Im Kopf der Bereichsdatei steht `phase: <n>`, die Nummer des Bauabschnitts
  (1 = zuerst). Daraus entsteht die Sortierung "Bauabschnitt"; ohne das Feld
  sortiert das Thema hinten. Die Reihenfolge selbst legt der Nutzer fest.
- `parts.csv` ist, was gekauft wird. `bauteile.csv` ist, was daraus gebaut
  wird — Bretter, Leisten, Zuschnitte mit Maßen in mm. Ein Holzbrett gehört
  nicht in die Stückliste.
- Alles unter `data/generated/`, `vault/Stückliste/` und `docs/data.json` wird
  erzeugt. Nie von Hand ändern — Änderungen gehen beim nächsten `sync` verloren.
- Die CSVs nicht direkt editieren: `camper parts excel` → in Excel arbeiten →
  `camper parts import` (zeigt erst einen Vergleich). Für die Einzelteile
  genauso mit `camper bauteile excel` / `import`.
- Nach inhaltlichen Änderungen einmal `python camper.py sync` laufen lassen.

## Befehle

`python camper.py <befehl>` — Übersicht mit `python camper.py --help`.
Wo Themen in Reihe stehen, gilt `--sortierung baustellen|phase|name`
(Voreinstellung `baustellen`) — dieselbe Reihenfolge wie im Dashboard.
Jeder Befehl gibt kompakten, antwortfertigen Text aus; `--json` liefert Rohdaten.
`python camper.py serve` startet das Dashboard mit Schreibzugriff — dort
abgehakte Aufgaben landen direkt im Vault, Statuswechsel in `parts.csv`.

## Python-Umgebung

Python 3.13, User-Scope (keine Adminrechte). Abhängigkeiten: `openpyxl`, `Pillow`.
Installation nur mit `pip install --user`.

## Git läuft nebenbei

Nach abgeschlossenen Arbeitsschritten selbst committen und pushen — nicht
nachfragen. Commit-Nachricht: eine Zeile, was passiert ist. Kein Fließtext,
keine Aufzählungen, keine Begründungen. Abschluss mit
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## Räumliche Planung macht der Nutzer

Wo Möbel und Geräte sitzen, entwirft der Nutzer selbst. Maße, Materialstärken,
Zuschnitte und Berechnungen sind dagegen unsere Aufgabe. Liegt ein Layout-Plan
vor, wird damit gearbeitet.

## Sparsam mit dem Kontext

- `docs/data.json` und `docs/data.js` nie lesen oder durchsuchen — erzeugt,
  riesig, `data.js` ist eine einzige Zeile.
- Dashboard-Arbeit: nur die Dateien der betroffenen Ansicht unter `docs/js/`
  und `docs/css/`, erst suchen, dann Ausschnitte lesen. Details im Skill
  `master-dev`.
- Breite Suchen und Browser-Prüfungen über mehrere Ansichten an Subagenten,
  die nur einen kurzen Befund zurückgeben.
- Keine Screenshots bei Zwischenschritten, höchstens einer am Ende.
- Handy-Ansicht ist zurückgestellt — nur auf ausdrücklichen Anstoß des
  Nutzers daran arbeiten.

## Direkt arbeiten oder delegieren

- Direkt: Feinschliff und alles, wozu der Nutzer Rückmeldung gibt.
- Delegieren an einen Subagenten: klar beschriebene Aufgaben mit viel
  Lesearbeit (neue Ansicht nach fertiger Beschreibung, Recherche, Input-Ordner
  einarbeiten, Browser-Prüfung über alle Ansichten). Er meldet nur Ergebnis
  und offene Fragen zurück.
- Fachliches wird im selben Chat mit dem Skill `master` geklärt, nicht über
  einen eigenen Agenten. Kein Manager-Agent.
- Wechselt das Thema, dem Nutzer einen neuen Chat empfehlen.

## Skills

- `master` — führt das Projekt, Standardfall.
- `master-dev` — baut und repariert die Pipeline.
- `master-research` — bringt Wissen herein, schreibt es in den Vault.

## Smart Home

Nebenprojekt, eigener Ast (`smarthome/`, `camper smarthome ...`). Mischt sich
nicht mit der Ausbau-Pipeline und nicht in deren Fortschrittszahlen.
