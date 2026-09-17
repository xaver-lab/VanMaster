# VanMaster

Renault Master 2013, Selbstausbau zum Vollzeit-Campervan.
Eine Datenbasis, vier Zugänge: Dashboard, Obsidian, Claude Code, Excel.

Aufbauplan und Begründungen: [PLAN.md](PLAN.md).

## Wo was liegt

| Ort | Inhalt |
|---|---|
| `data/parts.csv` | Stückliste — die Wahrheit |
| `vault/` | Obsidian-Vault: Aufgaben, Systeme, Entscheidungen, Anleitungen |
| `docs/` | Dashboard (GitHub Pages oder Doppelklick auf `index.html`) |
| `tools/`, `camper.py` | die Werkzeuge |
| `data/generated/`, `vault/Stückliste/`, `docs/data.*` | erzeugt, nicht von Hand ändern |

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
python camper.py system elektrik     # Lage eines Systems
python camper.py find "Heizung"      # Volltextsuche
python camper.py media               # Bilder aus _input einsortieren
python camper.py sync                # alles neu erzeugen
python camper.py serve               # Dashboard mit Schreibzugriff
python camper.py ui                  # Fenster mit Knöpfen
```

## Einrichtung

Python 3.13, keine Adminrechte nötig:

```bash
pip install --user openpyxl Pillow
```

Dashboard starten:

```bash
python camper.py serve          # http://localhost:8765, öffnet den Browser
python camper.py serve --offen  # dazu vom Handy im WLAN erreichbar
```

Mit `serve` schreiben die Kästchen und die Statusknöpfe direkt in Vault und
`parts.csv`. Ohne Server — Doppelklick auf `docs/index.html` oder GitHub
Pages — ist das Dashboard reine Anzeige und zeigt statt der Änderung den
passenden `camper`-Befehl zum Kopieren.

## Stückliste bearbeiten

Die CSV wird nie direkt angefasst. `parts excel` schreibt eine aufbereitete
Arbeitsmappe (Kategorien farbig, Auswahllisten, Summenblatt, Filter),
`parts import` liest sie zurück und zeigt erst einen Vergleich.
