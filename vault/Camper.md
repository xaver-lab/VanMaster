---
projekt: VanMaster
fahrzeug: Renault Master 2013
---

# VanMaster

Selbstausbau zum Vollzeit-Campervan. Diese Seite verlinkt alles.

## Einstieg

- [[Stückliste]] — alle Teile, Kosten, Gewicht (erzeugt)
- [[Medien]] — Fotos und Skizzen (erzeugt)

## Aufgaben

[[Vorbereitung]] · [[Dämmung]] · [[Elektrik]] · [[Wasser]] · [[Heizung]] ·
[[Möbel]] · [[Küche]]

## Systeme

[[Elektrik]] · [[Wasser]] · [[Heizung]] · [[Möbel]] · [[Küche]]

## Ordner

| Ordner | Inhalt |
|---|---|
| `Aufgaben/` | eine Datei je Bereich, verschachtelte Checkboxen |
| `Systeme/` | Stand und Auslegung je System |
| `Entscheidungen/` | eine Datei je Entscheidung: Frage, Optionen, Wahl, Begründung |
| `Anleitungen/` | Wie etwas gebaut wird |
| `Recherche/` | Produktvergleiche, Notizen, Quellen |
| `Stückliste/` | erzeugt aus `data/parts.csv` — nicht von Hand ändern |
| `Medien/` | Fotos, 3D-Bilder, Skizzen |

## Aufgaben schreiben

```markdown
- [ ] Batteriehalterung bauen ^batteriehalterung #hoch @dauer:3h
  - [x] Maße nehmen
- [ ] Batterien anschließen ^batterien-anschliessen @braucht:batteriehalterung
```

Kästchen: `[ ]` offen · `[/]` läuft · `[x]` erledigt · `[-]` verworfen.
Die Kennung nach `^` ist der Obsidian-Blockanker — darüber hängen Teile
(`fuer_aufgabe`) und Blocker (`@braucht:`).
