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
- Alles unter `data/generated/`, `vault/Stückliste/` und `web/dist/` wird
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
`python camper.py serve` startet das Dashboard (`web/`, FastAPI in
`tools/server/`) mit Schreibzugriff. Aufgaben, Bereichstexte, Teile und Einzelteile
landen direkt in Vault und CSVs, Web-Änderungen werden gesammelt committet.
Nach Änderungen in `web/src` neu bauen: `python camper.py web build`.
Fürs Handy: GitHub Pages, nur lesend, baut sich bei jedem Push selbst.
Aufgaben anlegen/umbenennen/löschen: `task add <Bereich> "<Titel>"`,
`task rename <id> "<Titel>"`, `task delete <id>`. Bereichstexte und Kopffelder:
`bereich set <Bereich> <Abschnitt> --text "…"` bzw.
`bereich set <Bereich> --kopf feld=wert`. Formatprüfung: `camper check`,
Prüfung auf sensible Daten: `camper geheim`.

## Python-Umgebung

Python 3.13, User-Scope (keine Adminrechte). Abhängigkeiten in `requirements.txt`
(`openpyxl`, `Pillow`, `fastapi`, `uvicorn`, `httpx`, `pytest`).
Installation nur mit `pip install --user -r requirements.txt`.

## Git läuft nebenbei — Daten sofort, Code erst nach Sichtung

Ein Push auf `main` baut die Website neu. Deshalb zwei Geschwindigkeiten:

- **Daten** (`vault/`, `data/`) — Aufgaben, Bereichstexte, Teile, Einzelteile,
  Medien: nach dem Arbeitsschritt selbst committen **und pushen**, nicht
  nachfragen. Das ist der Zweck der Kette.
- **Code** (alles andere: `camper.py`, `tools/`, `web/`, `tests/`,
  `.github/`, `.claude/`, die Regel- und Planungsdateien): lokal committen,
  **nicht pushen**. Am Ende des Arbeitsschritts sagen, was geändert wurde,
  und `git diff origin/main..HEAD` anbieten. Erst auf ausdrückliche Freigabe
  des Nutzers pushen.

Gemischt geändert: in zwei Commits trennen, den Daten-Commit pushen, den
Code-Commit liegen lassen.

Die Push-Wache (`.claude/hooks/push_wache.py`) stoppt einen Push mit
Codeänderungen. Sie ist ein Geländer, kein Ersatz für die Regel.

Commit-Nachricht: eine Zeile, was passiert ist. Kein Fließtext, keine
Aufzählungen, keine Begründungen. Abschluss mit
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## Was nicht geht, wird mitgeschrieben

Scheitert ein Schritt an etwas, das nur der Nutzer freimachen kann — gesperrte
Rechte, fehlende Zugangsdaten, eine Anmeldung im Browser, ein Dienst, den es im
Container nicht gibt —, dann kommt ein Eintrag nach `BLOCKIERT.md`, oben an.
Nicht erst am Ende, nicht nur im Chat: der Chat ist weg, die Datei bleibt.

Jeder Eintrag nennt Datum, was versucht wurde, was blockiert hat, den Stand der
Arbeit und was es freimachen würde. Ist ein Punkt erledigt, wird der Eintrag
gelöscht, nicht abgehakt — `BLOCKIERT.md` zeigt nur Offenes.

Weiterarbeiten, so weit es ohne den blockierten Schritt geht. Ein Hänger ist
kein Grund, den Rest liegen zu lassen.

## Keine sensiblen Daten ins Repo

Repo und Website sind kein privater Ort. Was einmal gepusht ist, steht in der
Historie, auch nach dem Löschen. Nie ins Repo, auch nicht „nur kurz":

- Zugangsdaten jeder Art: Passwörter, API-Schlüssel, Tokens, private
  Schlüssel, WLAN-Passwörter, Cloudflare- und GitHub-Tokens. Die gehören in
  Umgebungsvariablen oder GitHub-Secrets.
- Fahrzeugdaten: Fahrgestellnummer, Kennzeichen, Versicherungs- und
  Zulassungsunterlagen.
- Persönliches: Anschrift, Telefonnummer, Geburtsdatum, Bankverbindung,
  Rechnungen und Lieferscheine mit Klarnamen oder Kontodaten.
- Genaue Standorte: Koordinaten von Stellplätzen, Wohn- oder Werkstattadresse.
  Der Ort reicht.

Preise, Bauteile, Maße, Datenblätter und Fotos vom Ausbau sind unkritisch.
Fotos vorher ansehen: Kennzeichen, Papiere und Hausnummern kommen ungewollt
mit aufs Bild.

Geprüft wird mit `python camper.py geheim`. Der `pre-commit`-Hook
(`.githooks/`) fährt denselben Scan über das, was zum Commit vorgemerkt ist,
und bricht bei einem Fund ab. Falscher Alarm: `geheim-ok` in die Zeile
schreiben. Echter Fund, schon gepusht: erst das Geheimnis zurückziehen
(neues Token, neues Passwort), dann aufräumen — Löschen allein reicht nicht.

## Räumliche Planung macht der Nutzer

Wo Möbel und Geräte sitzen, entwirft der Nutzer selbst. Maße, Materialstärken,
Zuschnitte und Berechnungen sind dagegen unsere Aufgabe. Liegt ein Layout-Plan
vor, wird damit gearbeitet.

## Sparsam mit dem Kontext

- `web/dist/` und `web/src/lib/api-schema.json` nie lesen oder durchsuchen —
  erzeugt und groß. Daten lieber über `python camper.py <befehl> --json`.
- Dashboard-Arbeit: nur die Dateien der betroffenen Ansicht unter
  `web/src/lib/<ansicht>/` bzw. `web/src/routen/`, erst suchen, dann
  Ausschnitte lesen. Details im Skill `master-dev`.
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
