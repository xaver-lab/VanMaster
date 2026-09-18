---
bereich: Elektrik
kurz: Batterien, Laderegler, Solar, Verteilung, Verbraucher
status: in-arbeit
phase: 4
---

# Elektrik

## Beschreibung

Batterien, Laderegler, Solar, Verteilung, Verbraucher.

## Stand

- Quellen: PV-Modul (6mm² Kabel + Stecker) und Autobatterie laufen je über eine
  Sicherung (6A bzw. 16A DC) zum DC-Laderegler. Die Batteriebank (300 Ah) läuft
  über eine Sicherung (10A DC pro Batterie) zum zentralen Verteiler.
- Der Verteiler speist gesicherte Zonen (je 6A DC, 2x2,5mm² Kabel):
  - Vorne: Lampen 12V, USB 12V
  - Bett: Lampen 12V, USB 12V
  - Dach: Dachlüfter, Soundsystem
  - Küche: USB-Steckdose, Schalter → Wasserpumpe, Taster → Abwasser-Ventil,
    Füllanzeige → LED
  - AC 230V: Wechselrichter → 230V-Steckdose, Beamer
- Die Standheizung (Diesel) hängt an einer eigenen Sicherung direkt am Verteiler.
- Kabeltypen im Diagramm: 2x2,5mm² (Verbraucher), Yf 10mm² (Hauptleitungen
  Batterie/Laderegler), 3x1,5mm² (vereinzelt).

Rohauszug (SVG) in `_input/miro_export.md`.

## Auslegung

_(Zahlen, sobald gerechnet)_

## Notizen

_(keine)_

## Links

_(noch keine)_

## Aufgaben

### Auslegung

- [/] Strombilanz rechnen (Verbraucher, Tagesbedarf) ^strombilanz #kritisch
- [/] Batteriebank und Laderegler festlegen ^batteriebank-entscheiden #kritisch @braucht:strombilanz

### Einbau

- [ ] Batteriehalterung bauen ^batteriehalterung @braucht:batteriebank-entscheiden
- [/] Solarmodule montieren ^solar-montieren #hoch
- [ ] Verteilung und Sicherungen setzen ^verteilung @braucht:batteriehalterung
- [ ] Verbraucher verkabeln (Zonen: Vorne, Bett, Dach, Küche, AC 230V) ^verbraucher-verkabeln @braucht:verteilung
