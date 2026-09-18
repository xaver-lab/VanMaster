// Status von Aufgaben (und allem, was denselben Lebenslauf hat).

export const STATUS = ['offen', 'laeuft', 'erledigt', 'verworfen', 'blockiert'] as const;
export type Status = (typeof STATUS)[number];

export const STATUS_TEXT: Record<Status, string> = {
  offen: 'offen',
  laeuft: 'läuft',
  erledigt: 'erledigt',
  verworfen: 'verworfen',
  blockiert: 'blockiert',
};

export function istStatus(wert: string): wert is Status {
  return (STATUS as readonly string[]).includes(wert);
}
