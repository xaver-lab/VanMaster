---
name: camper-research
description: Bringt technisches Wissen in das VanMaster-Projekt - Bauteile auslegen und vergleichen, Datenblätter auswerten, Strom-, Wasser- und Gewichtsfragen rechnen, Kaufentscheidungen vorbereiten und im Vault festschreiben. Nutze diesen Skill, wenn etwas unklar ist oder etwas gekauft werden soll, das mehr als eine Bestellung wert ist.
---

# camper-research — Wissen hereinbringen

Auftrag: Technische Fragen belastbar beantworten, Ausbauideen mit Substanz
liefern — ausgelegt auf **Renault Master 2013, Vollzeitnutzung, 300 Ah,
kein Warmwasser, keine Dusche**.

## Wie gesucht wird

1. Erst nachsehen, was schon da ist: `python camper.py find "<thema>"` und ein
   Blick in `vault/Recherche/`, `vault/Entscheidungen/`, `vault/Systeme/`.
2. Dann gezielt ins Netz, in dieser Reihenfolge:
   Herstellerdaten und Datenblätter → Foren → Blogs → Videos.
3. Quellen nennen. Bei Bauteilen die Zahlen mitbringen, die wir brauchen:
   Leistung, Verbrauch (Ah/Tag), Maße, Gewicht, Anschlusswerte, Preis.

Kritisch auch gegen die eigene Fundlage: Marketingzahlen sind keine Messwerte.
Ruhestrom, Anlaufstrom und Wirkungsgrad stehen selten im Werbetext.

Die Regel des übergeordneten Schreibprojekts („keine eigene Websuche") gilt hier
**nicht** — im Camper ist Recherche ausdrücklich erwünscht.

## Umgang mit dem Nutzer

Nicht drei Optionen hinlegen und ihn entscheiden lassen. **Eine Empfehlung mit
Begründung**, die Gegenargumente ehrlich dazu. Wo es auf die Nutzung ankommt
(Winterbetrieb, Standzeiten, Stellplatz mit Strom), nachfragen statt annehmen.

## Was danach passiert

Das Ergebnis geht in den Vault, nicht nur in den Chat:

- `vault/Recherche/<Thema>.md` — Fundlage mit Quellen, YAML-Kopf mit `system`.
- `vault/Entscheidungen/<Frage>.md` — Frage, Optionen, Wahl, Begründung;
  `status: offen` bis gemeinsam entschieden, dann `status: entschieden`.
- Stückliste: `python camper.py parts add "<Teil>" --kategorie <Kategorie>`,
  danach Preis, Händler, Link, `kennwerte`, `gewicht_kg`, `fuer_aufgabe` und
  `entscheidung` setzen (`parts set <id> <feld> <wert>`).
- Verknüpfen mit der Systemseite über `[[Wikilinks]]`.
- Zum Schluss `python camper.py sync`.

Bei einer echten Entscheidung erst gemeinsam durchsprechen, dann festschreiben.

## Rechnen gehört dazu

Strombilanz (Tagesverbrauch gegen Kapazität und Solarertrag), Gewichtsbilanz
gegen die zulässige Zuladung, Wasserbedarf pro Tag, Zuschnitte und Maße.
Braucht es dafür ein kleines Skript — Preisabfrage, Auslegungsrechnung —
wird es geschrieben und unter `tools/` abgelegt.
