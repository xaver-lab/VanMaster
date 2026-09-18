# Umbau — Svelte-Dashboard, FastAPI, Datenkern

Abhakplan für den Umbau des Werkzeugs. Diese Datei ist das Gedächtnis des
Umbaus: Jeder neue Chat liest nur sie, arbeitet den nächsten offenen Punkt ab
und hakt ihn hier ab. Stand, Entscheidungen und offene Fragen stehen hier,
nicht im Chat.

## Ziel

Ein sauberes Werkzeug zum aktiven Arbeiten am PC: Texte und Aufgaben im
Browser anlegen, bearbeiten, abhaken, löschen. Gleichzeitig arbeitet Claude
Code auf denselben Dateien im Repo. Das Handy zeigt nur an (GitHub Pages).

## Festgelegter Stack

| Schicht | Wahl |
|---|---|
| Wahrheit | Markdown (`vault/`) und CSV (`data/`) im Repo, streng definiertes Format, kein Obsidian-Bezug mehr |
| Datenkern | Python-Paket `tools/kern/` — einzige Stelle, die liest und schreibt |
| Befehle | `camper.py` (argparse), ruft den Kern |
| Server | FastAPI + uvicorn, Live-Aktualisierung, Schutz vor Überschreiben, gesammelte Auto-Commits |
| Oberfläche | Svelte 5 + Vite + TypeScript in `web/` |
| Handy | GitHub Action baut Oberfläche + Daten, GitHub Pages nur lesend |
| Node | Nur Build-Werkzeug, portabel unter `~/nodejs/` (nicht im PATH) |

Bearbeitbar im Web: Bereichsabschnitte Beschreibung, Stand, Notizen, Links;
Aufgaben anlegen, abhaken, umbenennen, beschreiben, löschen; bei Teilen
Status, Preis, Menge, Notiz; Einzelteile.
Nur lesend (pflegt Claude): Auslegung, Entscheidungen, Recherche, Anleitungen,
`phase`, alles Berechnete.
Löschen entfernt wirklich aus der Datei (Git sichert), zusätzlich bleibt der
Status „verworfen“.

Das alte Dashboard (`docs/`) läuft unverändert weiter, bis Phase 9 es ablöst.

## Arbeitsweise

- **Hauptchat steuert, Sonnet-Subagenten bauen.** Jeder Punkt mit
  `[Sonnet]` geht per Agent-Werkzeug (`model: "sonnet"`,
  `subagent_type: "general-purpose"`) an einen Subagenten. Punkte mit
  `[Haupt]` macht der Hauptchat selbst (Entscheidungen, Abnahme, Feinschliff
  nach Rückmeldung des Nutzers).
- **Auftrag an den Subagenten:** Punkt aus dieser Datei wörtlich, betroffene
  Dateien, Abnahmekriterium, Verweis auf `FORMAT.md` und die Regeln in
  `CLAUDE.md` (Node-Pfad, `pip install --user`, `docs/data.*` nie lesen).
  Er committet nicht selbst.
- **Rückmeldung des Subagenten:** höchstens zehn Zeilen — was gebaut,
  welche Dateien, Testergebnis, offene Fragen. Kein Code im Bericht.
- **Abnahme im Hauptchat:** `git diff --stat`, Tests laufen lassen,
  höchstens gezielte Ausschnitte lesen. Keine ganzen Dateien.
- **Unabhängige Punkte** derselben Phase dürfen parallel an mehrere
  Subagenten gehen, wenn sie verschiedene Dateien berühren.
- **Nach jedem abgenommenen Punkt:** hier abhaken, Kurznotiz ins Protokoll,
  committen und pushen (eine Zeile, `Co-Authored-By` wie in `CLAUDE.md`).
- **Browser-Prüfungen** nur per Subagent, Befund in wenigen Zeilen,
  höchstens ein Screenshot am Ende einer Phase.
- **Inhaltliche Fragen** (was bearbeitbar ist, wie etwas heißt) stellt der
  Hauptchat dem Nutzer — Subagenten entscheiden das nicht.
- **Kontext knapp:** Wird der Hauptchat lang, Stand hier sichern und dem
  Nutzer einen neuen Chat mit dem Startprompt empfehlen.

## Phase 0 — Vorbereitung

- [x] [Haupt] In `PLAN.md` die Regel „Keine Frameworks, kein Build-Werkzeug, Doppelklick“ durch einen Verweis auf diese Datei ersetzen
- [x] [Sonnet] `fastapi`, `uvicorn`, `pytest` per `pip install --user` installieren; Node-Version prüfen; Ergebnis melden
- [x] [Haupt] `pytest`-Gerüst: `tests/` mit `conftest.py`, das Vault und `data/` nach `tmp_path` kopiert

## Phase 1 — Formatbeschreibung

- [x] [Sonnet] `FORMAT.md` entwerfen aus `tools/*.py` und dem echten Vault: Aufbau Bereichsdatei (YAML-Kopf, feste Abschnitte), Aufgabenzeile (`- [ ]`, `^id`, `#prio`, `@braucht:`, Dauer, eingerückte Beschreibung, Verschachtelung), Querverweise `[[…]]`, Entscheidungen/Anleitungen/Recherche, CSV-Spalten, Medienablage, Matrix bearbeitbar/nur Claude. Abweichungen im Bestand auflisten
- [x] [Haupt] `FORMAT.md` mit dem Nutzer durchgehen, offene Punkte entscheiden
- [x] [Sonnet] Bestand an `FORMAT.md` angleichen (nur Form, kein Inhalt); Liste der Änderungen melden

## Phase 2 — Datenkern `tools/kern/`

- [x] [Sonnet] Lesen: Bereiche, Abschnitte, Aufgabenbaum, Querverweise, Entscheidungen, Teile, Einzelteile, Medien → typisierte Datenklassen. Test: alle echten Dateien lesen ohne Fehler, Ergebnis gleich wie heutiges `tools/tasks.py`/`parts.py`
- [x] [Sonnet] Schreiben Aufgaben: anlegen (ID erzeugen, eindeutig), Status, Titel, Beschreibung, Priorität, löschen (mit Unterpunkten). Test: Rundlauf lesen→schreiben ist bytegleich; Änderung berührt nur die betroffenen Zeilen
- [x] [Sonnet] Schreiben Abschnitte: Bereichsabschnitt ersetzen, nur erlaubte Abschnitte laut Matrix. Test wie oben
- [x] [Sonnet] Schreiben CSV: Teile- und Einzelteilfelder ändern, anlegen, löschen. Test: Spaltenreihenfolge und unberührte Zeilen bleiben gleich
- [x] [Sonnet] Versionsschutz: Hash je Datei; Schreiben mit veraltetem Hash wird abgelehnt
- [x] [Sonnet] Prüfung: `kern.pruefen()` meldet Formatfehler mit Datei und Zeile
- [x] [Haupt] Abnahme: Tests grün, Stichprobe an einer echten Datei

## Phase 3 — Befehle auf den Kern

- [x] [Sonnet] Bestehende Befehle (`task`, `parts`, `bauteile`, `status`, `sync` …) auf den Kern umstellen, Ausgabe bleibt gleich. Vorher/Nachher-Ausgaben vergleichen
- [x] [Sonnet] Neue Befehle: `task add`, `task delete`, `task rename`, `bereich set <Bereich> <Abschnitt>`, `camper check`
- [x] [Haupt] Abnahme mit dem Nutzer: zwei, drei Befehle im Chat ausprobieren

## Phase 4 — FastAPI-Server

- [x] [Sonnet] `tools/server/`: FastAPI-App mit Pydantic-Modellen; `GET /api/daten`, CRUD für Aufgaben, Abschnitte, Teile, Einzelteile; jede Schreibanfrage trägt den Dateihash, Konflikt → 409 mit aktuellem Stand
- [x] [Sonnet] Live-Aktualisierung: Dateien per mtime überwachen (Standardbibliothek), Änderungen als Server-Sent Events an den Browser
- [x] [Sonnet] Auto-Commit: Web-Änderungen sammeln, nach einigen Minuten ohne Eingabe ein Commit mit einer Zeile; kein Push
- [x] [Sonnet] `camper serve` startet die neue App (liefert `web/dist` aus); alte Oberfläche weiter unter `/alt/` erreichbar; `.claude/launch.json` ergänzen
- [x] [Sonnet] JSON-Schema aus den Pydantic-Modellen exportieren → TypeScript-Typen für `web/`
- [x] [Haupt] Abnahme: API-Tests grün, Konfliktfall einmal von Hand durchgespielt

## Phase 5 — Web-Grundgerüst

- [x] [Sonnet] `web/`: Vite + Svelte 5 + TypeScript, Build per `camper web build` (ruft `~/nodejs/npm.cmd`), `node_modules` und `dist` in `.gitignore`
- [x] [Sonnet] Datenschicht im Browser: ein Store, lädt `/api/daten` (Server) oder `data.json` (statisch), hört auf SSE, Schreibfunktionen mit Hash und Konfliktanzeige, Sperre während laufender Anfrage
- [x] [Sonnet] Rahmen: Navigation, Routing per Hash, Hell/Dunkel, Toasts, Tastenkürzel wie heute; Lesemodus blendet alle Bearbeitungselemente aus
- [x] [Haupt] Stil aus `docs/css/` übernehmen, Abnahme mit dem Nutzer

## Phase 6 — Aufgaben und Bereichstexte (ab hier nutzbar)

- [x] [Sonnet] Aufgabenliste mit Filter, Gruppierung, Suche; Statuswechsler; Anlegen, Umbenennen, Löschen (mit Rückfrage); Detailfenster mit Beschreibung
- [x] [Sonnet] Bereichsansicht: Kopf, Reiter, bearbeitbare Abschnitte (Textfeld mit Markdown-Vorschau), nur-lesende Abschnitte sichtbar markiert
- [x] [Sonnet] Aufgabenliste (`web/src/lib/aufgaben/`) und Bereichsansicht (`web/src/lib/bereiche/`) auf die Bausteine aus `web/src/lib/ui/` und die Tokens aus `web/DESIGN.md` umstellen (Knopf, Chip, Statusmarke, Kontrollkaestchen, Dialog/`bestaetigen()`, Tabs, Rubrik, Leerzustand, Fortschritt); eigene Kopien dieser Elemente und alte Variablennamen entfernen; Verhalten bleibt gleich
- [x] [Sonnet] Browser-Prüfung: Anlegen/Ändern/Löschen landet in der Datei; Claude ändert parallel eine Datei → Oberfläche aktualisiert sich; Konflikt wird angezeigt
- [ ] [Haupt] Feinschliff nach Rückmeldung des Nutzers

## Phase 7 — Teile und Einzelteile

- [x] [Sonnet] Teileansicht (Liste/Raster, Filter, Kosten), Statuswechsler, Felder bearbeiten, Detailfenster
- [x] [Sonnet] Zuschnitt/Einzelteile mit Bearbeitung
- [ ] [Haupt] Feinschliff nach Rückmeldung

## Phase 8 — Start, Medien, Suche

- [x] [Sonnet] Startseite mit Kennzahlen und Entscheidungen
- [x] [Sonnet] Medien-Galerie und Lupe
- [x] [Sonnet] Befehlspalette (Strg+K) über alle Inhalte
- [x] [Sonnet] Browser-Prüfung aller Ansichten gegen das alte Dashboard: fehlt etwas?
- [ ] [Sonnet] Lücken aus dem Vergleich schließen: Bereichsreiter „Entscheidungen“ und „Zuschnitt“, Startseite „Kosten je Kategorie“
- [ ] [Haupt] Feinschliff nach Rückmeldung

## Phase 9 — Veröffentlichen und Ablösen

- [ ] [Sonnet] GitHub Action: Python baut `data.json`, Node baut `web/`, Deploy auf Pages; Lesemodus
- [ ] [Sonnet] Erzeugte Dateien aus Git nehmen (`docs/data.*`, altes Dashboard), `.gitignore` anpassen
- [ ] [Haupt] Handy-Ansicht auf Pages einmal ansehen (nur lesen, nichts optimieren)
- [ ] [Sonnet] Altes Dashboard, `tools/serve.py` und nicht mehr gebrauchte Module entfernen
- [ ] [Haupt] `CLAUDE.md`, Skill `master-dev`, `README.md`, `PLAN.md` auf den neuen Stand bringen

## Protokoll

Eine Zeile je abgeschlossenem Punkt oder getroffener Entscheidung.

- 2026-09-18 Stack festgelegt (siehe oben), Plan angelegt.
- 2026-09-18 Phase 0: PLAN.md verweist auf UMBAU.md; fastapi 0.141.1, uvicorn 0.53.0, pytest 9.1.1 installiert (Skripte nicht im PATH → `python -m`); Node v24.14.0, npm 11.9.0.
- 2026-09-18 Phase 0: `tests/conftest.py` — Fixture `repo` kopiert vault/ und data/ nach tmp_path und biegt alle Pfadkonstanten der `tools`-Module um (auch künftige Unterpakete wie `tools/kern/`). Aufruf: `python -m pytest -q`.
- 2026-09-18 Phase 1: `FORMAT.md` entworfen (Code + Bestand, 8 Abweichungen); mit Nutzer entschieden: `[[…]]` bleibt und wird im Web aufgelöst, fester Aufbau für Anleitungen/Recherche, `system` in `kategorie` aufgehen lassen, zusätzliche Web-Felder — alles in FORMAT.md §10.
- 2026-09-18 Phase 1: Bestand angeglichen — Vault war schon formgerecht; Spalte `system` aus parts.csv entfernt (4 Teile → Dämmung/Karosserie), Code und altes Dashboard nachgezogen, `Karosserie` in die Kategorieliste. Phase 1 fertig.
- 2026-09-18 Phase 2: Kern liest alles (`tools/kern/lesen.py`, `modelle.py`, `format.py`); Grammatik und CSV-Spalten wohnen jetzt in `kern/format.py`, alte Module importieren von dort. Jede Einheit kennt Datei (repo-relativ, `/`) und Zeilenbereich. 9 Tests.
- 2026-09-18 Phase 2: Versionsschutz vom Hauptchat vorgezogen — `kern/datei.py` (Hash je Datei, `Konflikt` bei veraltetem Hash, atomares bytegleiches Schreiben); alle Schreibfunktionen laufen darüber.
- 2026-09-18 Phase 2: `kern/abschnitte.py` — Abschnitt und Kopffeld setzen mit Matrix-Prüfung (`quelle=web|claude`), fehlender Abschnitt an richtiger Stelle. 9 Tests.
- 2026-09-18 Phase 2: `kern/tabellen.py` — `teil_*`/`einzelteil_*` Feld setzen, anlegen, löschen; prüft Listen, Zahlen (Punkt), Datum, Matrix; nur die betroffene Zeile ändert sich. 21 Tests.
- 2026-09-18 Phase 2: `kern/aufgaben.py` — anlegen (ID aus Titel, eindeutig; in Gruppe oder als Unterpunkt), Status, Titel, Beschreibung, Prio, löschen mit Unterpunkten; Marken bleiben an ihrer Stelle. 26 Tests.
- 2026-09-18 Phase 2: `kern/pruefen.py` — `kern.pruefen()` meldet Befunde mit Datei/Zeile (Kopf, Abschnitte, Aufgaben, Abhängigkeitskreise, Querverweise, CSV). Entscheidungsseiten ohne festen Aufbau; Bezüge `fuer_aufgabe`/`entscheidung` und `gekauft_am` nur Warnung. Echter Bestand: 0 Befunde. 25 Tests.
- 2026-09-18 Phase 2 abgenommen: `tools.kern` exportiert `laden`, `aufgaben`, `abschnitte`, `tabellen`, `datei`, `pruefen`, Ausnahmen `Konflikt`/`Unerlaubt`/`Ungueltig`. 94 Tests grün. Stichprobe an echter Elektrik.md: anlegen, Status, Beschreibung, Konflikt, löschen → Datei danach bytegleich. Status-Schlüssel im Kern ohne Umlaut: `offen|laeuft|erledigt|verworfen|blockiert`.
- 2026-09-18 Phase 3: tasks/parts/bauteile/bereiche/status/serve lesen und schreiben über den Kern, doppelte Parser entfernt. 20 Befehlsausgaben + data.json vorher/nachher gleich (einzige Abweichung: Pfade mit `/`). Altes `/api/teil` setzt jetzt die Web-Matrix durch; Fehler dort noch als 500 (sauber ab Phase 4).
- 2026-09-18 Phase 3: neue Befehle `task add|rename|delete`, `bereich set <Bereich> <Abschnitt> --text` / `--kopf feld=wert`, `check` (Exit 1 bei Fehlern). CLAUDE.md und Skill `master` verweisen darauf. 113 Tests.
- 2026-09-18 Phase 3 abgenommen: add/rename/start/delete an Heizung vorgeführt, Bestand danach unverändert; Statusausgabe zeigt „läuft“.
- 2026-09-18 Phase 4: `tools/server/` (app.py, modelle.py, daten.py). `/api/daten` = erzeugt, bereiche, aufgaben, querverweise, entscheidungen, anleitungen, recherche, teile, einzelteile, medien, versionen, kennzahlen, bearbeitbar; `daten_json()` liefert dasselbe für den statischen Build. REST-Routen für Aufgaben, Abschnitte/Kopf, Teile, Einzelteile; 409 mit `stand`, 403/422/404. Einhängepunkt `app.state.nach_schreiben`. Teil-Felder außerhalb der Matrix → 422 (Kern meldet `Ungueltig`). 21 Tests.
- 2026-09-18 Phase 4: `tools/server/commit.py` — `anmelden(app, ruhe_sekunden=180)` sammelt Web-Änderungen, committet nach Ruhe nur diese Dateien, eine Zeile „Web: … geändert“, ohne Co-Authored-By, kein Push; `jetzt_committen()` beim Beenden. 7 Tests.
- 2026-09-18 Phase 4: `python -m tools.server.schema` erzeugt `web/src/lib/api-typen.ts` (+ `api-schema.json`) aus den 21 Pydantic-Modellen, ohne npm; tsc --strict fehlerfrei. npx braucht Node im PATH der Sitzung (`PATH=~/nodejs:$PATH`). 4 Tests.
- 2026-09-18 Phase 4: `tools/server/start.py` — `camper serve` startet die neue App: `/api/*`, `/alt/` = altes Dashboard samt alten Schreibendpunkten, `/` = `web/dist` mit SPA-Fallback (ohne dist Hinweisseite). Auto-Commit an, `--kein-commit` aus, `--alt` = alter Server. launch.json: `camper-neu` (8765), `camper-serve` = alt (8766). 8 Tests.
- 2026-09-18 Phase 4: `tools/server/live.py` — Wächter pollt mtime/Größe (1 s, `VANMASTER_LIVE_INTERVALL`, 0 = aus), SSE `GET /api/live`: `event: aenderung`, `data: {dateien:[{datei,version}], quelle: web|extern}`, Heartbeat 15 s. SSE-Test über echten uvicorn-Thread, weil TestClient SSE puffert. 9 Tests.
- 2026-09-18 Phase 4 abgenommen: 162 Tests grün (~85 s). Echter Server: `task add` von außen kommt als SSE `extern` an; PATCH mit altem Hash → 409 samt `stand`; Bestand danach unverändert. Hinweis: curl-Aufrufe mit Umlauten im Git-Bash scheitern an der Kodierung (400) — kein Serverfehler.
- 2026-09-18 Phase 5: `web/` = Vite 8.3 + Svelte 5.57 + TypeScript 5.9 (TS 7 noch nicht von svelte-check unterstützt), `base: './'`, Dev-Proxy `/api` → 8765. `camper web build|dev|check` (`tools/web.py`): npm aus `~/nodejs/npm.cmd`, sonst PATH; installiert bei fehlendem node_modules per `npm ci`. Server liefert `/` samt Assets. 3 Tests.
- 2026-09-18 Phase 5: Store `web/src/lib/daten.svelte.ts` (Modus server/statisch, SSE mit Neuverbinden, Schreibfunktionen mit Hash, 409 → Stand übernehmen + Konflikt-Toast; Sperre weist parallele Schreibaufrufe ab statt Warteschlange). Rahmen: Kopfleiste, Hash-Routing, Hell/Dunkel, Toasts, Tastenkürzel, `Schreibbar.svelte` blendet im Lesemodus aus; Platzhalter-Ansichten in `web/src/routen/`. Kürzel für Palette und Lupe folgen mit den Ansichten. Server- und statischer Fall geprüft.
- 2026-09-18 Phase 5: Stil aus `docs/css/basis.css`/`palette.css` in `web/src/app.css` (gleiche Farbvariablen, dunkel als Grundlage), Seitenschiene links wie früher (`Schiene.svelte`), Kopf mit Suchknopf und live-Anzeige, Kacheln auf Start. Reihenfolge 1 Start, 2 Bereiche, 3 Aufgaben … wie im alten Dashboard, `#/themen` → Bereiche. launch.json kurzzeitig auf `py -3.13`, wieder zurück auf `python`.
- 2026-09-18 Phase 5 abgenommen: Oberfläche startet sauber (Nutzer).
- 2026-09-18 Nutzer: Stil wirkt „AI-Standard“ → Opus-Subagent entwirft parallel im Worktree ein neues Designsystem (`web/src/lib/ui/`, `web/DESIGN.md`, Musterseite `#/muster`); Abnahme durch den Nutzer vor dem Übernehmen.
- 2026-09-18 Phase 6: Aufgabenliste (`web/src/lib/aufgaben/`: AufgabenListe `bereich?`, `anlegenErlaubt?`; AufgabeZeile, AufgabeDetail `#/aufgaben/<id>`), Filter/Gruppierung/Suche, Statuswechsler, Anlegen/Umbenennen/Löschen mit Rückfrage, Beschreibung mit Vorschau. `lib/markdown.ts` + `Markdown.svelte` lösen `[[…]]` auf; externe Links nur http(s)/ohne Schema. An Heizung durchgespielt, Vault danach bytegleich. Stil vorerst schlicht, folgt dem neuen Designsystem.
- 2026-09-18 Phase 6: Bereichsansicht (`web/src/lib/bereiche/`): Übersicht sortierbar baustellen/phase/name, Detail mit Kopf und Reitern im Hash (`#/bereiche/<Name>/<reiter>`), Abschnitte nach `bearbeitbar.bereich_abschnitte` mit Text/Vorschau, sonst „pflegt Claude“. Konflikt beim Speichern: Toast, Eingabe bleibt, erneutes Speichern geht. Vault danach bytegleich.
- 2026-09-18 Designsystem „Werkstattheft“ vom Nutzer abgenommen und nach main übernommen: warmes Papier/Graphit, eine Signalfarbe, Archivo + JetBrains Mono, Lucide-Icons (alles lokal über npm). Bausteine in `web/src/lib/ui/` (Sammelimport `ui/index.ts`), Anleitung `web/DESIGN.md`, Musterseite `#/muster`. Alte Variablennamen gelten als Aliase weiter. Neuer Punkt in Phase 6: Aufgaben- und Bereichsansicht auf die Bausteine umstellen.

- 2026-09-18 Phase 6: Aufgaben- und Bereichsansicht auf die Bausteine aus `lib/ui/` umgestellt (Knopf, IconKnopf, Chip, Etikett, Statusmarke, Kontrollkaestchen, Feld/Auswahl/Textfeld, Dialog + `bestaetigen()`, Tabs, Rubrik, Karte, Leerzustand, FortschrittBalken); Statuswechsler jetzt `Auswahl`, Aufgaben-Detail echter `Dialog`, Zeilenklick echter `<button>` (a11y). Keine alten Aliasnamen, keine eigenen Nachbauten mehr (grep leer), Importe und Props gegen `lib/ui/` geprüft. **Offen: `camper web check|build` — in der Cloud-Sitzung ist der npm-Registry-Zugriff gesperrt, `node_modules` fehlt. Punkt bleibt mit `[~]` markiert, bis der Build lokal einmal durchläuft.**

- 2026-09-18 Phase 6: Baustein `ui/Kennzahl.svelte` (`titel`, `wert`, `zusatz`, `icon`, `ton` neutral|signal|gut|info|warn, `href`/`onclick`) — in `index.ts`, `DESIGN.md` und auf `#/muster`; der Bereichs-Kopf benutzt ihn statt eigener Kacheln. Offen bleibt auch hier die Build-Prüfung. Hinweis: `routen/Start.svelte` hat noch ein handgestricktes `.grosszahl`/`.zahl`-Muster in den Karten Budget/Teile — Kandidat für die Kennzahl, in Phase 8.

- 2026-09-18 Phase 7: Teileansicht (`web/src/lib/teile/`: TeileListe, TeilZeile, TeilKarte, TeilDetail, format.ts) - Kennzahlen-Kopf, Status-Tabs, Kategoriefilter, Suche, Liste/Raster, Anlegen/Loeschen, Detail-`Dialog`. **Teile haben ein eigenes Status-Vokabular** (`tools/common.py: PART_STATUS` = Idee, Recherche, Entschieden, Bestellt, Geliefert, Verbaut) - nicht das Aufgaben-Enum aus `lib/ui`; daher `Etikett` mit Tonzuordnung in `teile/format.ts` statt `Statusmarke`. Bearbeitbarkeit je Feld zur Laufzeit aus `bearbeitbar.teil_felder`.
- 2026-09-18 Phase 7: Zuschnitt (`web/src/lib/zuschnitt/`: EinzelteilListe, -Zeile, -Detail, -Feld, mass.ts, status.ts) - Filter Bereich/Material, Gruppierung nach Bereich, Kennzahlen Anzahl/Flaeche/Laufmeter, alle Felder ausser `id` bearbeitbar, `teil_id` als Auswahl ueber die Teile. Eigenes Vokabular auch hier (`BAUTEIL_STATUS`, `BAUTEIL_ART`, `MASSQUELLE` in `tools/common.py`) - **in den Komponenten fest verdrahtet, weil die API diese Listen nicht ausliefert. Aendert sich das Vokabular, muss es dort nachgezogen werden** (besser waere: die Listen ueber `/api/daten` mitliefern).
- 2026-09-18 Beide Phase-7-Ansichten sind **ungeprueft** (kein Build, siehe Uebergabe). Der Commit „Zwischenstand Zuschnitt-Ansicht“ enthaelt entgegen seiner Nachricht bereits den fertigen Stand.
- 2026-09-18 Phase-7-Zweig lokal auf `main` übernommen. `web check`: 1 Fehler (`filterStatus` in TeileListe zu eng typisiert) und 8 Warnungen, alle behoben — jetzt 0/0, `web build` läuft. Nebenbei: `AufgabenListe` im Bereichs-Reiter steht jetzt in `{#key name}`, sonst blieb beim Wechsel zwischen Bereichen der alte Bereich im Anlegen-Formular stehen. `Kennzahl` rendert `a`/`button`/`div` einzeln statt `svelte:element`. Browser-Prüfung steht noch aus.
- 2026-09-18 Browser-Prüfung Phase 6/7 (Subagent, im versteckten Browser-Fenster): Anlegen, Status, Beschreibung, Live-Aktualisierung per SSE, 409 bei alter Version, Bereichsreiter, Teile- und Zuschnitt-Bearbeitung landen korrekt in Vault/CSV. **Nicht bestätigt:** Löschen über den Bestätigungsdialog und Umbenennen per Enter. Das Fenster hatte keinen Fokus und feuert kein `close` am `<dialog>`, deshalb im echten Browser nachprüfen. Danach behoben: Zahlen deutsch formatiert (`lib/zahlformat.ts`), Teile ohne Preis zeigen „—“ statt „0 €“, Zuschnitt zählt Stück statt Zeilen, und Leisten gehen nicht mehr in die Fläche ein.
- 2026-09-18 Offene Punkte aus der Browser-Prüfung erledigt: `/api/daten` liefert `vokabular` (Teile-Status/-Prio/-Kategorien, Einzelteil-Art/-Status, Maßquelle aus `common.py`). Das Web liest es über `lib/vokabular.svelte.ts` und hat keine eigenen Listen mehr. Zuschnitt: Materialfilter folgt dem Bereich, Gruppierung wählbar (Bereich/Material/Art). Überschreibschutz für Bereichsabschnitte und Aufgabenbeschreibungen (`lib/ueberschreiben.ts`): Ändert sich der Ausgangstext während der Bearbeitung, erscheint ein Hinweis, und vor dem Speichern wird nachgefragt. Hell-Thema: `--farbe-text-3` auf #6f685b (vorher 2,8–3,5:1, jetzt 4,2–5,3:1).
- 2026-09-18 Phase 8: Medien-Galerie (`lib/medien/`: MedienAnsicht, Galerie, Lupe, url.ts) mit Filter nach Bereich und Art, Suche und Lupe (←/→, Esc, Zähler). Der Bereichsreiter „Medien“ nutzt dieselbe Galerie. Bilder kommen aus den Web-Kopien `docs/medien/` über die neue Server-Route `/medien` (in `start.py`, nicht mehr über `/alt`; Vite leitet `/medien` im Dev weiter). Befehlspalette (`lib/palette/`): Strg+K, Suche über Bereiche, Aufgaben, Teile, Einzelteile, Seiten und Medien, dazu Ansichten und Hell/Dunkel. Startseite nimmt die Teile-Stufen aus dem `vokabular`. Im Browser geprüft (Port 8767): Bilder laden, Lupe blättert, Palette findet.
- 2026-09-18 Phase 8: Vergleich neu gegen alt (Subagent, nur lesend). Es fehlen im Bereich-Detail die Reiter „Entscheidungen“ und „Zuschnitt“ (im alten auch leer sichtbar) und auf der Startseite „Kosten je Kategorie“. Themen-Liste, Aufgaben, Teile, Zuschnitt, Medien und Palette sind gleichwertig, keine Konsolenfehler. Neuer Punkt zum Schließen der Lücken.
- 2026-09-18 Phase 6: Rest der Browser-Prüfung mit sichtbarem Browserfenster und echten Eingaben. Umbenennen per Enter, Löschen mit Abbrechen, Escape und Bestätigen landen alle richtig in der Datei, Vault danach bytegleich, kein Code geändert. Die früheren Aussetzer kamen vom versteckten Browserfenster, der Code war nicht schuld.

## Offene Fragen

- Palette: Treffer mit loser Buchstabenfolge („kabel“ findet „Klappenbeschlag … Kinvaro“) stehen in ihrer Gruppe vor echten Worttreffern anderer Typen. Lose Treffer ausblenden, wenn es genug echte gibt?
- Medien-Treffer in der Palette öffnen nur die Galerie. Lupe per Route (`#/medien/<id>`) direkt öffnen?
- Einzelteile haben keine Detail-Route (`#/zuschnitt/<id>`), die Palette springt nur in die Liste.
- Palette zeigt die Dialog-Kopfzeile „Suchen oder springen“ mit X (das alte Dashboard hatte nur das Eingabefeld). `Dialog` ohne Kopf erlauben?
- 3D-Modelle haben keine Web-Kopie und sind in der Galerie nur als Kachel „nur im Vault“ zu sehen.

## Übergabe an den nächsten Chat

Stand 2026-09-18: Phasen 0–5 fertig und abgenommen. Phase 6 und 7 sind gebaut,
`web check` (0 Fehler, 0 Warnungen) und `web build` laufen. 

Browser-Prüfungen für Phase 6 und 8 sind durch (siehe Protokoll). Nächster Schritt: die Lücken
aus dem Vergleich schließen (Phase 8), dann Feinschliff mit dem Nutzer (Phase 6–8).
Browser-Prüfungen nur mit sichtbarem Browserfenster (`tabs_select`), sonst kommen Enter/Escape nicht an.

- Neuer Rechner: `pip install --user -r requirements.txt`; Node portabel nach `~/nodejs/`
  (Version 24, nicht im PATH) oder systemweit im PATH — `camper web` findet beides.
- `python` muss 3.13 mit den Paketen sein (`python --version`); zeigt es auf eine andere Version, PATH prüfen.
- Tests: `PYTHONIOENCODING=utf-8 python -m pytest -q` (~165 Tests, ~85 s).
  Einzelne Datei reicht zum Abnehmen, am Phasenende einmal alles.
- Web: `python camper.py web build|check|dev`. Nach Änderungen an `web/src` neu bauen,
  der Server liefert `web/dist` aus. `check` muss ohne Warnungen durchlaufen.
- Aufbau `web/src/`: `lib/daten.svelte.ts` (Store, Schreibfunktionen, SSE), `lib/router.svelte.ts`,
  `lib/Schreibbar.svelte` (Lesemodus), `lib/ui/` (Bausteine, siehe `web/DESIGN.md`),
  `lib/markdown.ts` + `Markdown.svelte` (`[[…]]`), `lib/aufgaben/` (AufgabenListe `bereich?`,
  `anlegenErlaubt?`), `lib/bereiche/`, `routen/` (eine Datei je Ansicht, `Muster.svelte`).
- Neue Ansichten: zuerst `web/DESIGN.md` lesen, nur Bausteine aus `lib/ui/` und Tokens
  (`--farbe-*`, `--a-*`, `--r-*`) benutzen, Stil scoped in der Komponente, `app.css` nur für Globales.
- Typen für `web/`: `python -m tools.server.schema` → `web/src/lib/api-typen.ts`.
- Server zum Prüfen: Preview `camper-neu` (Port 8765) aus `.claude/launch.json`;
  altes Dashboard unter `/alt/`, alter Server als `camper-serve` (8766). Selbst gestartete
  Server immer mit `--kein-commit`.
- Der neue Server liefert noch keine Bilder aus `vault/Medien` aus (für Phase 8 Medien nötig).
- SSE `GET /api/live`: `event: aenderung`, `data: {dateien:[{datei,version}], quelle}`.
  `quelle: "web"` = eigene Änderung, kein Konflikt anzeigen.
- Status-Schlüssel ohne Umlaut: `offen|laeuft|erledigt|verworfen|blockiert`.
- Parallele Subagenten: jedem die Dateien zuweisen, die er NICHT anfassen darf;
  nach Rückmeldung nur seine Dateien committen. Größere Umgestaltung parallel: Worktree
  (`isolation: "worktree"`), `.claude/worktrees/` ist in `.gitignore`.

## Startprompt für jeden neuen Chat

```text
/master-dev Wir setzen den Umbau aus `UMBAU.md` um.

Lies zuerst nur `UMBAU.md` — sie ist Plan, Stand und Gedächtnis zugleich.
Dann den nächsten offenen Punkt (oder mehrere unabhängige derselben Phase)
abarbeiten, genau nach dem Abschnitt „Arbeitsweise“ dort:

- Du bist der steuernde Hauptchat und sparst Kontext. Punkte mit [Sonnet]
  gibst du per Agent-Werkzeug mit `model: "sonnet"` an Subagenten, mit
  klarem Auftrag und Abnahmekriterium. Sie melden höchstens zehn Zeilen zurück.
- Du liest keine ganzen Dateien, nur `git diff --stat`, Testausgaben und
  gezielte Ausschnitte.
- Nach jeder Abnahme: in `UMBAU.md` abhaken, Protokollzeile, committen, pushen.
- Inhaltliche Entscheidungen fragst du mich. Nach jeder Phase kurz melden,
  was jetzt geht, und auf mein „weiter“ warten.
- Wird der Chat lang: Stand in `UMBAU.md` sichern und mir einen neuen Chat
  mit genau diesem Prompt empfehlen.

Start.
```
