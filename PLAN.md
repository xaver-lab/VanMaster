# VanMaster — Aufbauplan

Renault Master 2013, Selbstausbau zum Vollzeit-Campervan.
Projektname: **VanMaster**.
Stand: 2026-09-18 · Grundgerüst, Skills und Datenpipeline stehen, Umbau des
Dashboards (`UMBAU.md`) bis auf den Feinschliff fertig. Details siehe `.claude/skills/master-dev`.

---

## 1. Grundidee

Eine einzige Datenbasis, vier Zugänge darauf:

| Zugang | Wofür | Richtung |
|---|---|---|
| **Dashboard** (Laptop, Handy über Pages) | schneller Blick und Arbeiten: Aufgaben, Bereichstexte, Teile, Zuschnitt | am Laptop mit `camper serve` lesen + schreiben, Handy nur lesen |
| **Obsidian** (Laptop + Handy) | abhaken, Notizen tippen, Anleitungen lesen, Zusammenhänge verfolgen | lesen + schreiben |
| **Claude Code** (Laptop) | einbauen, umstrukturieren, recherchieren, rechnen | lesen + schreiben |
| **Excel** (Laptop, bei Bedarf) | Stückliste in Ruhe durchgehen, Preise vergleichen | Ausleihe, kommt zurück |

Kein Sync-Konflikt, weil es nur eine Wahrheit gibt: Textdateien im Git-Repo.
Alles Maschinenlesbare wird daraus **erzeugt**, nie von Hand gepflegt.

**Hosting:** öffentliches GitHub-Repo, Dashboard über GitHub Pages
(https://xaver-lab.github.io/VanMaster/, baut sich per GitHub Action bei jedem Push).
Handy: Browser-Lesezeichen für die Übersicht, Obsidian mit Git-Erweiterung für die Inhalte.

---

## 2. Dashboard

Svelte 5 + Vite in `web/`, FastAPI-Server in `tools/server/`, Datenkern in
`tools/kern/`. Technik und Umbau: siehe `UMBAU.md`, Gestaltung: `web/DESIGN.md`.

**Stufe 1 — Grundgerüst** ✅ erledigt
Tab-Navigation. Aufgabenbaum zum Aufklappen mit Fortschritt je Bereich.
Stücklisten-Tabelle mit Filter nach Kategorie und Status. Kostensumme oben.

**Stufe 2 — Inhalte** ✅ erledigt
Bildergalerie mit Bereichszuordnung ✅, Kacheln nach Status/Thema mit
Detailmodal (Beschreibung, Fotos) ✅, Entscheidungen je Bereich, Markdown
gerendert, Anleitungen und Recherche in den Bereichsreitern, `[[…]]`-Verlinkung ✅.

**Stufe 3 — Auswertungen** offen
Strombilanz: Tagesverbrauch gegen Batteriekapazität und Solarertrag.
Gewichtsbilanz gegen zulässige Zuladung. Kostenverlauf. Blocker-Übersicht.

**Stufe 4 — Komfort** teilweise
Volltextsuche über alles (Strg+K) ✅. Ansichten per Link teilbar ✅.
Offline-fähig am Handy — einmal geladen, funktioniert ohne Empfang am Van.

Schreibzugriff (früher "Stufe 5, optional") ist über `camper serve` da:
Aufgaben, Bereichstexte, Teile und Einzelteile gehen direkt in Vault und CSVs,
mit Schutz vor Überschreiben und Live-Aktualisierung.

---

## 3. Stand der Umsetzung

Grundgerüst, Datenpipeline (`camper.py`, `tools/`), Skills und Dashboard
Stufe 1 stehen. Details zu Befehlen, Datenformaten und Skills stehen im Code
und in `.claude/skills/`, nicht hier — sonst zwei Wahrheiten.

## 4. Offen

- Miro-Anbindung direkt nutzen oder Inhalte über `_input` übergeben? (bisher
  ungebraucht, `_input` enthält nur Smart-Home-Doku und einen alten
  Dashboard-Screen)
- Obsidian am Handy: Git-Erweiterung einrichten — eigener Schritt, noch offen

---

## 5. Smart Home (separates Hobby-Nebenprojekt)

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
| Dashboard | Tabs für Bereiche/Aufgaben/Stückliste | eigener zusätzlicher Tab, eigene Daten — mischt sich nicht mit denen des Ausbaus |
| Aufgaben | `vault/Bereiche/*.md` | eigene Datei, klar als Nebenprojekt gekennzeichnet, nicht in die Ausbau-Fortschrittszahlen eingerechnet |

Grund für die Trennung: Smart Home ist Hobby-Nebenprojekt, soll parallel
laufen können, ohne die Ausbau-Pipeline zu verkomplizieren oder deren
Fortschrittszahlen zu verfälschen.
