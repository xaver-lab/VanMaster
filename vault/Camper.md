---
projekt: VanMaster
fahrzeug: Renault Master 2013
---

# VanMaster

Selbstausbau zum Vollzeit-Campervan. Diese Seite verlinkt alles.

## Einstieg

- [[Stückliste]] — alle Teile, Kosten, Gewicht (erzeugt)
- [[Medien]] — Fotos und Skizzen (erzeugt)

## Bereiche

[[Vorbereitung]] · [[Karosserie]] · [[Dämmung]] · [[Elektrik]] · [[Wasser]] ·
[[Heizung]] · [[Möbel]] · [[Küche]]

Ein Bereich ist ein Arbeitsraum: Beschreibung, Stand, Auslegung, Notizen,
Links und Aufgaben in einer Datei. Bilder, Teile, Einzelteile und Modelle
kommen aus den Daten dazu — `python camper.py bereich Möbel` zeigt alles
zusammen.

## Ordner

| Ordner | Inhalt |
|---|---|
| `Bereiche/` | eine Datei je Arbeitsbereich, feste Abschnitte, Aufgaben unten |
| `Entscheidungen/` | eine Datei je Entscheidung: Frage, Optionen, Wahl, Begründung |
| `Anleitungen/` | Wie etwas gebaut wird |
| `Recherche/` | Produktvergleiche, Notizen, Quellen |
| `Stückliste/` | erzeugt aus `data/parts.csv` — nicht von Hand ändern |
| `Medien/` | Fotos und Skizzen |
| `Modelle/` | 3D-Zeichnungen je Bereich |

Einzelteile mit Maßen — Bretter, Leisten, Zuschnitte — stehen nicht im Vault,
sondern in `data/bauteile.csv` (`camper bauteile`).

## Abschnitte einer Bereichsdatei

`## Beschreibung` · `## Stand` · `## Auslegung` · `## Notizen` · `## Links` ·
`## Aufgaben` — in dieser Reihenfolge. Aufgaben werden nur im letzten
Abschnitt gelesen, eine Checkbox in den Notizen bleibt ein Merker.

## Aufgaben schreiben

```markdown
- [ ] Batteriehalterung bauen ^batteriehalterung #hoch @dauer:3h
  - [x] Maße nehmen
- [ ] Batterien anschließen ^batterien-anschliessen @braucht:batteriehalterung
```

Kästchen: `[ ]` offen · `[/]` läuft · `[x]` erledigt · `[-]` verworfen.
Die Kennung nach `^` ist der Obsidian-Blockanker — darüber hängen Teile
(`fuer_aufgabe`) und Blocker (`@braucht:`).
