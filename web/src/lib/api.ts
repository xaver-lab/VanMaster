// Dünne Hülle um fetch für /api/... — kein Zustand, keine Store-Logik hier.
import type { FehlerAntwort, KonfliktAntwort } from './api-typen';

/** Typisierter Fehler einer API-Anfrage. Bei 409 trägt `stand` den
 * aktuellen Bestand aus dem Server-Rumpf (siehe KonfliktAntwort). */
export class ApiFehler extends Error {
  readonly status: number;
  readonly meldung: string;
  readonly stand?: unknown;

  constructor(status: number, meldung: string, stand?: unknown) {
    super(meldung);
    this.name = 'ApiFehler';
    this.status = status;
    this.meldung = meldung;
    this.stand = stand;
  }
}

async function anfrage<T>(pfad: string, init?: RequestInit): Promise<T> {
  let antwort: Response;
  try {
    antwort = await fetch(pfad, init);
  } catch {
    // Netzwerkfehler (Server nicht erreichbar) — Status 0 als Kennzeichen.
    throw new ApiFehler(0, 'Server nicht erreichbar.');
  }

  const text = await antwort.text();
  let rumpf: unknown = null;
  if (text) {
    try {
      rumpf = JSON.parse(text);
    } catch {
      // Antwort war kein JSON — bleibt null, unten ggf. generischer Fehlertext.
    }
  }

  if (!antwort.ok) {
    const fehlerRumpf = (rumpf ?? {}) as Partial<FehlerAntwort & KonfliktAntwort>;
    const meldung = fehlerRumpf.fehler ?? `Fehler ${antwort.status}`;
    throw new ApiFehler(antwort.status, meldung, fehlerRumpf.stand);
  }

  return rumpf as T;
}

export function apiGet<T>(pfad: string): Promise<T> {
  return anfrage<T>(pfad);
}

export function apiPost<T>(pfad: string, rumpf: unknown): Promise<T> {
  return anfrage<T>(pfad, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rumpf),
  });
}

export function apiPatch<T>(pfad: string, rumpf: unknown): Promise<T> {
  return anfrage<T>(pfad, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rumpf),
  });
}

export function apiPut<T>(pfad: string, rumpf: unknown): Promise<T> {
  return anfrage<T>(pfad, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rumpf),
  });
}

export function apiDelete<T>(pfad: string, query?: Record<string, string>): Promise<T> {
  const suffix = query ? `?${new URLSearchParams(query).toString()}` : '';
  return anfrage<T>(pfad + suffix, { method: 'DELETE' });
}
