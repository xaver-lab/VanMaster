// Schutz für Texte, die im Web bearbeitet werden: Hat sich der Ausgangstext
// während der Bearbeitung anderswo geändert (Claude, CLI, zweites Fenster),
// wird vor dem Speichern nachgefragt statt still zu überschreiben.
// Die Dateiversion allein hilft hier nicht — die Seite lädt sie per SSE nach.
import { bestaetigen } from './ui';

export function neuereFassungUeberschreiben(): Promise<boolean> {
  return bestaetigen({
    titel: 'Text wurde inzwischen geändert',
    text: 'Während du bearbeitet hast, hat jemand anderes diesen Text geändert. Speichern ersetzt diese neuere Fassung durch deinen Entwurf.',
    ja: 'Trotzdem speichern',
    nein: 'Zurück zum Entwurf',
    gefaehrlich: true,
  });
}
