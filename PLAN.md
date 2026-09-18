# VanMaster — Aufbauplan

Renault Master 2013, Selbstausbau zum Vollzeit-Campervan.
Projektname: **VanMaster**.
Stand: 2026-09-17 · Planungsphase abgeschlossen, Umsetzung noch nicht begonnen.

---

## 1. Grundidee

Eine einzige Datenbasis, vier Zugänge darauf:

| Zugang | Wofür | Richtung |
|---|---|---|
| **HTML-Übersicht** (Handy + Laptop) | schneller Blick: was ist offen, was kostet es, wie schaut's aus | nur lesen |
| **Obsidian** (Laptop + Handy) | abhaken, Notizen tippen, Anleitungen lesen, Zusammenhänge verfolgen | lesen + schreiben |
| **Claude Code** (Laptop) | einbauen, umstrukturieren, recherchieren, rechnen | lesen + schreiben |
| **Excel** (Laptop, bei Bedarf) | Stückliste in Ruhe durchgehen, Preise vergleichen | Ausleihe, kommt zurück |

Kein Sync-Konflikt, weil es nur eine Wahrheit gibt: Textdateien im Git-Repo.
Alles Maschinenlesbare wird daraus **erzeugt**, nie von Hand gepflegt.

**Hosting:** öffentliches GitHub-Repo, Dashboard über GitHub Pages.
Handy: Browser-Lesezeichen für die Übersicht, Obsidian mit Git-Erweiterung für die Inhalte.

---

## 2. Ordnerstruktur

```
Camper/
├── camper.py              ein Einstiegspunkt für alle Befehle
├── tools/                 Python-Module
│   ├── parts.py           Stückliste: CSV <-> Excel <-> Markdown
│   ├── tasks.py           Aufgabenbaum lesen, auswerten, ändern
│   ├── bereiche.py        Bereichsdateien lesen und zerlegen
│   ├── bauteile.py        Einzelteile mit Maßen
│   ├── media.py           Bilder einsortieren, verkleinern, verlinken
│   ├── build.py           Dashboard-Daten erzeugen
│   ├── status.py          kompakte Lageberichte für den Chat
│   └── ui.py              Tkinter-Fenster mit Knöpfen
├── vault/                 der Obsidian-Vault
│   ├── Camper.md                 Startseite, verlinkt alles
│   ├── Bereiche/                 ein Arbeitsbereich je Datei, Aufgaben inbegriffen
│   ├── Entscheidungen/           eine Datei pro Entscheidung
│   ├── Anleitungen/              "Bettrahmen bauen", "Kabel crimpen"
│   ├── Recherche/                Produktvergleiche, Notizen
│   ├── Stückliste/               erzeugt — nicht von Hand ändern
│   ├── Medien/                   Fotos und Skizzen
│   └── Modelle/                  3D-Zeichnungen je Bereich
├── data/
│   ├── parts.csv                 die Wahrheit für die Stückliste (was gekauft wird)
│   ├── bauteile.csv              Einzelteile mit Maßen (was gebaut wird)
│   └── generated/                Excel + Dashboard-JSON, beides erzeugt
├── _input/                Rohablage: Miro-Auszüge, Fotos, Links, Notizen
│                          bleibt liegen, bis integriert — dann geleert
├── docs/                  index.html + Daten, was GitHub als Webseite ausliefert
└── .claude/skills/        die drei Skills, mitversioniert
```

Obsidian trägt das Ganze über `[[Wikilinks]]`: Bereich → Anleitung →
Entscheidung → Teil. Jede Datei bekommt einen kleinen YAML-Kopf (Bereich, Status,
Kosten), aus dem sich später Dataview-Abfragen speisen.

---

## 3. Datenformate

| Inhalt | Format | Begründung |
|---|---|---|
| Bereiche | eine Markdown-Datei je Bereich, feste Abschnitte | alles zu einem Thema an einem Ort, am Stück lesbar |
| Aufgaben | Markdown, verschachtelte Checkboxen im Abschnitt `## Aufgaben` | Obsidian hakt nativ ab, GitHub zeigt es lesbar, Git-Diff sauber |
| Anleitungen, Recherche | Markdown mit YAML-Kopf | überall lesbar, von Hand und maschinell pflegbar |
| Einzelteile | CSV als Quelle | Maße rechenbar, Excel-Runde wie bei der Stückliste |
| Entscheidungen | eine Markdown-Datei je Entscheidung | Frage, Optionen, Wahl, Begründung — nachvollziehbar |
| Stückliste | CSV als Quelle | Textdatei, guter Git-Diff, in VS Code und Excel bearbeitbar |
| Dashboard | erzeugtes JSON | nur Ausgabe, nie Eingabe |

### Stücklisten-Spalten

| Spalte | Zweck |
|---|---|
| `id` | stabile Kennung für Verlinkungen |
| `titel`, `beschreibung` | Grunddaten |
| `kategorie` | Elektrik, Wasser, Heizung, Möbel, Küche, Stauraum, Werkzeug, Verbrauchsmaterial |
| `system` | verweist auf die Systemseite im Vault |
| `menge`, `einheit` | Gesamtpreis rechnet sich daraus |
| `preis` | Einzelpreis |
| `status` | Idee → Recherche → Entschieden → Bestellt → Geliefert → Verbaut |
| `prioritaet` | Kritisch / Hoch / Mittel / Nice-to-have |
| `link`, `haendler` | Händler getrennt für Sammelbestellungen |
| `fuer_aufgabe` | welche Aufgabe braucht das Teil |
| `entscheidung` | verweist auf die Entscheidungsseite |
| `kennwerte` | frei: "12 V, 5 A, 60 W" — Grundlage der Strombilanz |
| `gewicht_kg` | Zuladung ist beim Master ein echtes Thema |
| `notiz`, `gekauft_am` | Rest |

`fuer_aufgabe`, `kennwerte` und `gewicht_kg` machen aus einer Liste ein System:
aufgabenbezogene Einkaufszettel, Strombilanz, Gewichtsbilanz.

### Stückliste bearbeiten

Die CSV wird nie direkt angefasst:

- `camper parts excel` → aufbereitete Excel-Datei: Kategorien farblich getrennt,
  Auswahllisten für Status, Summen je Bereich, Filter gesetzt.
- `camper parts import` → liest zurück, zeigt **erst** einen Vergleich
  ("3 Zeilen geändert, 2 neu, Gesamtkosten +180 €"), schreibt nach Bestätigung.
- `camper parts md` → lesbare Markdown-Tabellen nach `vault/Stückliste/`,
  eine Seite je Kategorie, verlinkbar aus Aufgaben.

Excel-Komfort beim Bearbeiten, ohne dass Excel je die Wahrheit hält.

---

## 4. Python-Werkzeuge

Python 3.13, User-Scope-Installation (keine Adminrechte).
Abhängigkeiten minimal: `openpyxl` für Excel, `Pillow` für Bildverkleinerung.
Tkinter für die UI — steckt schon in Python.

```
camper sync          alles neu erzeugen (Excel, Markdown, Dashboard)
camper status        Lageüberblick;  --brief für den kompakten Chat-Bericht
camper tasks next    nächste Aufgaben mit Blockern
camper brief <id>    alles zu einer Aufgabe in einem Aufruf
camper parts query   gefilterte Stücklisten-Abfrage
camper parts excel   Stückliste als Excel rausschreiben
camper parts import  Excel zurücklesen, mit Vergleich vorher
camper parts set     Status/Feld eines Teils ändern
camper task done     Aufgabe abhaken
camper buy next      Einkaufsvorschlag, nach Händler gruppiert
camper bereich <name> alles zu einem Arbeitsbereich in einem Aufruf
camper bereiche      alle Bereiche mit Fortschritt
camper bauteile      Einzelteile mit Maßen anlegen, abfragen, Excel-Runde
camper find "<text>" Volltextsuche, liefert Pfade statt Inhalte
camper media         Bilder aus _input einsortieren, verkleinern, verlinken
camper build         Dashboard bauen
camper ui            Tkinter-Fenster mit Knöpfen für all das
```

**Grundregel für jeden Befehl:** kompakte, antwortfertige Textausgabe für den Chat,
optional `--json` für das Dashboard. Keine Rohdatenwüsten.

---

## 5. HTML-Übersicht

Eine HTML-Datei, eine CSS-, eine JS-Datei, dazu ein erzeugtes `data.json`.
Keine Frameworks, kein Build-Werkzeug — läuft per Doppelklick lokal genauso wie
auf GitHub Pages. Mobil zuerst gedacht, dunkles Thema, große Klickflächen.

**Stufe 1 — Grundgerüst**
Tab-Navigation. Aufgabenbaum zum Aufklappen mit Fortschritt je Bereich.
Stücklisten-Tabelle mit Filter nach Kategorie und Status. Kostensumme oben.

**Stufe 2 — Inhalte**
Bildergalerie mit Bereichszuordnung. Entscheidungsseiten. Anleitungen direkt
im Dashboard lesbar (Markdown gerendert). Verlinkung zwischen allem.

**Stufe 3 — Auswertungen**
Strombilanz: Tagesverbrauch gegen Batteriekapazität und Solarertrag.
Gewichtsbilanz gegen zulässige Zuladung. Kostenverlauf. Blocker-Übersicht.

**Stufe 4 — Komfort**
Volltextsuche über alles. Ansichten per Link teilbar.
Offline-fähig am Handy — einmal geladen, funktioniert ohne Empfang am Van.

**Stufe 5 — optional, später**
Schreibzugriff am Laptop, falls Obsidian irgendwann nicht reicht.

---

## 6. Die drei Skills

Als Auftrag und Arbeitsweise formuliert, nicht als Verbotsliste.
Jeder darf tun, was der Sache dient — die Rolle beschreibt den Schwerpunkt.

### `master-dev` — baut das Werkzeug

**Auftrag:** Die Pipeline soll den Ausbau tragen. Befehle mit antwortfertiger
Ausgabe. Ein Dashboard, das am Van auf dem Handy so gut funktioniert wie am
Laptop. Datenformate, die von Hand bearbeitbar bleiben.

**Arbeitsweise:** Erst verstehen, wie es läuft, dann ändern. Jede neue Funktion
braucht einen Befehl **und** eine Dashboard-Ansicht. Nach Änderungen einmal
`camper sync` durchlaufen lassen.

Fasst Inhalte an, wenn es der Sache dient (Testdaten, Migrationen, Umbauten) —
trifft aber keine inhaltlichen Entscheidungen im Alleingang.

**Rufen, wenn:** am System etwas fehlt oder klemmt.

### `master` — führt das Projekt

**Auftrag:** In zwei Sätzen soll klar sein, wo das Projekt steht und was als
Nächstes sinnvoll ist. Hält Aufgaben, Teile, Entscheidungen und Kosten aktuell,
während ihr redet.

**Startroutine:** ein Aufruf `camper status --brief`, dann die Lage kennen.
Danach genau der Befehl, der zur Frage passt:

| Frage | Befehl |
|---|---|
| Was ist als Nächstes dran? | `camper tasks next` |
| Lass uns X angehen | `camper brief <aufgabe>` |
| Was müssen wir bestellen? | `camper buy next` |
| Wie steht die Elektrik? | `camper bereich Elektrik` |
| Was war nochmal mit Y? | `camper find "Y"` |

Das ist der schnellste Weg zur Antwort, kein Sparzwang. Reicht ein Befehl nicht,
wird nachgelesen — es fängt nur nicht damit an.

**Arbeitsweise:** Kurz antworten — Lage, Empfehlung, Rückfrage. Beiläufig
Erwähntes wird mitgepflegt ("Batterien sind da" → Status auf Geliefert, eine
Zeile Rückmeldung). Wird aus dem Gespräch ein Werkzeugproblem oder eine
Recherche, Wechsel vorschlagen statt halbherzig selbst machen.

**Rufen, wenn:** am Projekt gearbeitet wird. Der Standardfall.

### `master-research` — bringt Wissen herein

**Auftrag:** Technische Fragen belastbar beantworten, Ausbauideen mit Substanz
liefern — ausgelegt auf Renault Master 2013, Vollzeitnutzung, 300 Ah,
kein Warmwasser, keine Dusche.

**Wie gesucht wird:** Erst nachsehen, was im Vault schon steht. Dann gezielt:
Herstellerdaten und Datenblätter vor Foren, Foren vor Blogs, Blogs vor Videos.
Quellen nennen. Bei Bauteilen die Zahlen mitbringen, die wir brauchen:
Leistung, Verbrauch, Maße, Gewicht.

**Umgang mit dem Nutzer:** Nicht drei Optionen hinlegen und ihn entscheiden
lassen. Eine Empfehlung mit Begründung, Gegenargumente ehrlich dazu, und wo es
auf die Nutzung ankommt, nachfragen. Kritisch auch gegen die eigene Fundlage —
Marketingzahlen sind keine Messwerte.

**Was danach passiert:** Das Ergebnis geht in den Vault, nicht nur in den Chat.
Recherchenotiz, Entscheidungsseite, Stücklisteneinträge, verknüpft mit dem
betroffenen System. Bei einer echten Entscheidung erst gemeinsam durchsprechen,
dann festschreiben. Braucht es dafür ein kleines Skript — Preisabfrage,
Auslegungsrechnung — wird es geschrieben.

**Rufen, wenn:** etwas unklar ist oder etwas gekauft werden soll, das mehr als
eine Bestellung wert ist.

---

## 7. Projektregeln (kommen in die CLAUDE.md)

**Git läuft nebenbei.** Nach abgeschlossenen Arbeitsschritten selbst committen
und pushen. Nicht nachfragen, nicht den Nutzer damit behelligen.
Commit-Nachrichten kurz und knapp: eine Zeile, die sagt was passiert ist —
kein Fließtext, keine Aufzählungen, keine Begründungen. Das spart Kontext,
wenn die Historie später gelesen wird. Abschluss mit
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

**Räumliche Planung macht der Nutzer.** Wo der Kühlschrank sitzt, wie die Möbel
angeordnet sind, was neben was passt — das entwirft er selbst, nicht wir von uns
aus. Maße von Produkten, Materialstärken, Zuschnitte und Berechnungen sind
dagegen ausdrücklich unsere Aufgabe. Liegt ein Layout-Plan vor, wird
selbstverständlich damit gearbeitet.

**Recherche ist hier erwünscht.** Die Regel aus dem übergeordneten
Schreibprojekt ("keine eigene Websuche, nur Suchvorschläge") gilt für das
Schreibprojekt, nicht für den Camper.

---

## 8. Umsetzungsreihenfolge

1. Repo anlegen, Grundstruktur, CLAUDE.md, .gitignore
2. `camper.py` mit `sync`, `status`, `build` — das Skelett
3. Stückliste: CSV-Schema, Excel-Export, Excel-Import mit Vergleich, Markdown-Ausgabe
4. Aufgaben: Markdown-Format festlegen, lesen, auswerten, abhaken
5. Dashboard Stufe 1
6. Die drei Skills
7. Miro-Inhalte übernehmen — direkt oder über `_input`
8. Medien-Ablauf, Tkinter-UI
9. Dashboard Stufen 2–4, laufend

---

## 9. Offen

- Miro-Anbindung direkt nutzen oder Inhalte über `_input` übergeben?
- Obsidian am Handy: Git-Erweiterung einrichten — eigener Schritt nach dem Repo

---

## 10. Smart Home (separates Hobby-Nebenprojekt)

Eigenes Steuerungs- und Überwachungssystem für den Camper (Pi/Odroid als
Master-Node, ESP32-Satelliten, FastAPI/MQTT-Backend, PWA-Dashboard).
Architektur-Grundlage: `_input/Camper Smart Home Architektur.md`.

Technisch komplett losgelöst vom Ausbau — eigene Hardware, eigener Stack,
eigener Code. Läuft **im selben Repo, aber als eigener Ast**, nicht vermischt
mit der Ausbau-Pipeline:

| Bereich | Ausbau (bestehend) | Smart Home (eigener Ast) |
|---|---|---|
| Ordner | `vault/`, `data/`, `tools/` | eigener Zweig, z. B. `smarthome/` mit eigenem `vault/`, `data/` |
| CLI | `camper.py` mit den bestehenden Befehlen | eigener Namespace, z. B. `camper smarthome ...`, statt in die bestehenden Befehle hineinzuwachsen |
| Skill | `master`, `master-dev`, `master-research` | eigener vierter Skill, z. B. `master-smarthome` |
| Dashboard | Tabs für Bereiche/Aufgaben/Stückliste | eigener zusätzlicher Tab, eigenes generiertes JSON — mischt sich nicht mit `data.json` des Ausbaus |
| Aufgaben | `vault/Bereiche/*.md` | eigene Datei, klar als Nebenprojekt gekennzeichnet, nicht in die Ausbau-Fortschrittszahlen eingerechnet |

Grund für die Trennung: Smart Home ist Hobby-Nebenprojekt, soll parallel
laufen können, ohne die Ausbau-Pipeline zu verkomplizieren oder deren
Fortschrittszahlen zu verfälschen.
