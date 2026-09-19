# VanMaster

Renault Master 2013, Selbstausbau zum Vollzeit-Campervan.
Eine Datenbasis, vier Zugänge: Dashboard, Obsidian, Claude Code, Excel.

Aufbauplan und Begründungen: [PLAN.md](PLAN.md).

## Wo was liegt

| Ort | Inhalt |
|---|---|
| `data/parts.csv` | Stückliste — die Wahrheit |
| `vault/` | Obsidian-Vault: Aufgaben, Systeme, Entscheidungen, Anleitungen |
| `web/` | Dashboard: Svelte 5 + Vite + TypeScript, Aufbau in `web/DESIGN.md` |
| `tools/server/` | Server für das Dashboard (FastAPI) mit Schreib-API und Live-Aktualisierung |
| `tools/`, `camper.py` | die Werkzeuge |
| `data/generated/`, `vault/Stückliste/`, `web/dist/` | erzeugt, nicht von Hand ändern |

## Befehle

```bash
python camper.py status --brief      # Lage in zwei Zeilen
python camper.py tasks next          # nächste Aufgaben mit Blockern
python camper.py brief <aufgabe>     # alles zu einer Aufgabe
python camper.py task done <id>      # abhaken
python camper.py parts excel         # Stückliste als Excel
python camper.py parts import        # Excel zurücklesen, zeigt erst den Vergleich
python camper.py parts import --apply
python camper.py buy next            # Einkauf nach Händler gruppiert
python camper.py bereich Elektrik    # Lage eines Bereichs
python camper.py find "Heizung"      # Volltextsuche
python camper.py media               # Bilder aus _input einsortieren
python camper.py sync                # alles neu erzeugen
python camper.py serve               # Dashboard mit Schreibzugriff
python camper.py web build           # Dashboard neu bauen (nach Änderungen in web/)
python camper.py check               # Format von Vault und CSVs prüfen
python camper.py ui                  # Fenster mit Knöpfen
```

## Einrichtung

Python 3.13, keine Adminrechte nötig:

```bash
pip install --user -r requirements.txt
```

Node 24 nur zum Bauen des Dashboards: portabel unter `~/nodejs/` oder im PATH,
`camper web` findet beides.

Dashboard starten:

```bash
python camper.py serve          # http://localhost:8765, öffnet den Browser
python camper.py serve --offen  # dazu vom Handy im WLAN erreichbar
```

Mit `serve` schreibt das Dashboard Aufgaben, Bereichstexte, Teile und
Einzelteile direkt in Vault und CSVs. Ändert Claude parallel eine Datei, zieht
die Oberfläche sofort nach, und veraltete Stände werden abgelehnt statt
überschrieben. Web-Änderungen landen nach einigen Minuten Ruhe gesammelt in
einem Commit (`--kein-commit` schaltet das ab).

Fürs Handy baut eine GitHub Action bei jedem Push auf `main` eine reine
Leseansicht: https://xaver-lab.github.io/VanMaster/

## Stückliste bearbeiten

Die CSV wird nie direkt angefasst. `parts excel` schreibt eine aufbereitete
Arbeitsmappe (Kategorien farbig, Auswahllisten, Summenblatt, Filter),
`parts import` liest sie zurück und zeigt erst einen Vergleich.
