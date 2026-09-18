// SSE-Anbindung an GET /api/live (UMBAU.md Phase 4/5). Nur im Servermodus
// sinnvoll — im Lesemodus (statischer Build) gibt es keinen Server, der
// Ereignisse sendet, deshalb bricht `verbinden()` dort sofort ab.
//
// Format (live.py): `event: aenderung`, `data: {dateien:[{datei,version}],
// quelle}`. `quelle: "web"` ist die eigene Schreibaktion dieses Browsers —
// der Store hat sich dafür schon selbst aktualisiert, hier also nichts tun.
// `quelle: "extern"` heißt: eine Datei hat sich außerhalb des Browsers
// geändert (z. B. Claude direkt im Vault) — neu laden und den Rahmen über
// `beobachten` informieren. Heartbeat-Kommentare (alle 15 s) ignoriert
// EventSource von selbst, sie lösen kein `message`-Event aus.
import { daten, laden, meldungSenden } from './daten.svelte';

type AenderungsPaket = {
  dateien: { datei: string; version: string }[];
  quelle: 'web' | 'extern';
};

const WIEDERVERBINDEN_MAX_MS = 30_000;

/** Baut die SSE-Verbindung auf und hält sie mit steigender Wartezeit
 * (Exponential Backoff, gedeckelt) am Leben, bis die zurückgegebene
 * Funktion aufgerufen wird. Der Rahmen ruft das einmal beim Start auf
 * (Servermodus) und beim Aufräumen wieder ab. */
export function verbinden(): () => void {
  if (daten.lesemodus) {
    return () => {}; // statischer Build: kein Server, keine Verbindung
  }
  let aktiv = true;
  let quelle: EventSource | null = null;
  let versuch = 0;
  let wiederholTimer: ReturnType<typeof setTimeout> | null = null;

  function verbindungSchliessen(): void {
    quelle?.close();
    quelle = null;
  }

  function neuVersuchen(): void {
    if (!aktiv) return;
    const wartezeit = Math.min(WIEDERVERBINDEN_MAX_MS, 1000 * 2 ** versuch);
    versuch += 1;
    wiederholTimer = setTimeout(oeffnen, wartezeit);
  }

  function oeffnen(): void {
    if (!aktiv) return;
    verbindungSchliessen();
    quelle = new EventSource('/api/live');

    quelle.addEventListener('aenderung', (ereignis) => {
      versuch = 0;
      let paket: AenderungsPaket;
      try {
        paket = JSON.parse((ereignis as MessageEvent).data);
      } catch {
        return; // ungültiges Paket, ignorieren
      }
      if (paket.quelle === 'web') return; // eigene Änderung, kein Konflikt
      void laden();
      const anzahl = paket.dateien.length;
      meldungSenden({
        art: 'info',
        text:
          anzahl === 1
            ? `${paket.dateien[0].datei} wurde von außen geändert.`
            : `${anzahl} Dateien wurden von außen geändert.`,
      });
    });

    quelle.onopen = () => {
      versuch = 0;
    };

    quelle.onerror = () => {
      verbindungSchliessen();
      neuVersuchen();
    };
  }

  oeffnen();

  return () => {
    aktiv = false;
    if (wiederholTimer !== null) clearTimeout(wiederholTimer);
    verbindungSchliessen();
  };
}
