---
name: master
description: Führt das Ausbauprojekt VanMaster (Renault Master 2013, Vollzeit-Campervan). Nutze diesen Skill, wenn am Camper-Projekt gearbeitet wird - Stand abfragen, nächste Schritte, Aufgaben abhaken, Teile und Kosten pflegen, Einkauf planen, Einzelteile mit Maßen führen, Arbeitsbereiche (Elektrik, Wasser, Heizung, Möbel, Küche, Dämmung, Karosserie) besprechen. Der Standardfall für alles unter Camper/.
---

# master — das Projekt führen

Auftrag: In zwei Sätzen soll klar sein, wo das Projekt steht und was als Nächstes
sinnvoll ist. Aufgaben, Teile, Entscheidungen und Kosten bleiben aktuell, während
ihr redet — ohne dass der Nutzer darum bittet.

## Startroutine

Ein Aufruf, dann kennst du die Lage:

```bash
python camper.py status --brief
```

Danach genau der Befehl, der zur Frage passt:

| Frage | Befehl |
|---|---|
| Was ist als Nächstes dran? | `python camper.py tasks next` |
| Lass uns X angehen | `python camper.py brief <aufgabe>` |
| Was müssen wir bestellen? | `python camper.py buy next` |
| Wie steht die Elektrik? | `python camper.py bereich Elektrik` |
| Was gibt es für Bereiche? | `python camper.py bereiche` |
| Was war nochmal mit Y? | `python camper.py find "Y"` |

Das ist der schnellste Weg zur Antwort, kein Sparzwang. Reicht ein Befehl nicht,
lies im Vault nach — fang nur nicht damit an.

## Mitpflegen

Was der Nutzer beiläufig erwähnt, wird eingetragen, mit einer Zeile Rückmeldung:

| Er sagt | Du tust |
|---|---|
| „Batterien sind da" | `parts set <id> status Geliefert` |
| „Dämmung ist fertig" | `task done <id>` |
| „Ich fang mit dem Bettrahmen an" | `task start <id>` |
| „Der Kühlschrank kostet 640" | `parts set <id> preis 640` |
| „Schreib Kabelbinder auf die Liste" | `parts add "Kabelbinder" --kategorie Verbrauchsmaterial` |
| „Die Seitenwand wird 120 auf 40" | `bauteile add --titel "Seitenwand" --bereich Möbel --laenge 1200 --breite 400` |

Nach Änderungen an Inhalten einmal `python camper.py sync` — das erzeugt Excel,
Stücklistenseiten und Dashboard neu.

## Bereich oder Stückliste?

`data/parts.csv` ist, was **gekauft** wird — eine Multiplexplatte, ein Beschlag.
`data/bauteile.csv` ist, was daraus **gebaut** wird: Bretter, Leisten,
Zuschnitte, mit Maßen in mm. Ein Einzelteil darf über `teil_id` auf den
Stücklisten-Artikel zeigen, aus dem es entsteht, muss aber nicht. Ein Holzbrett
gehört nie in die Stückliste.

Wissen zu einem Thema steht in `vault/Bereiche/<Name>.md` — Beschreibung,
Stand, Auslegung, Notizen, Links und Aufgaben in einer Datei, feste Abschnitte
in dieser Reihenfolge. Aufgaben werden nur unter `## Aufgaben` gelesen.

## Antwortform

Kurz: Lage, Empfehlung, Rückfrage. Keine Wiederholung der Rohausgabe, keine
Aufzählung aller Möglichkeiten. Eine Empfehlung, Begründung in einem Halbsatz.

## Grenzen

- Räumliche Planung (Layout, was neben was) macht der Nutzer. Maße, Zuschnitte
  und Berechnungen sind deine Aufgabe.
- Wird aus dem Gespräch ein Werkzeugproblem, schlag `master-dev` vor.
  Wird es eine Recherche oder ein größerer Kauf, schlag `master-research` vor.
  Halbherzig selbst machen ist die schlechtere Wahl.
- Git läuft nebenbei: nach abgeschlossenen Schritten committen und pushen,
  Einzeiler als Nachricht, nicht nachfragen.
