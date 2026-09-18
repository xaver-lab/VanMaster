<script lang="ts">
  // Eine Aufgabenzeile: Kästchen (offen↔erledigt), Statuswechsler (alle
  // Status), Titel, Meta (Thema/Prio/Dauer/Blocker). Klick auf den Titel
  // öffnet das Detailfenster; Kästchen und Wechsler sind eigene Bedienelemente
  // neben dem Titel-Knopf, nicht darin verschachtelt.
  import type { AufgabeAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { Auswahl, Etikett, Kontrollkaestchen, Statusmarke, STATUS_TEXT, type Status } from '../ui';

  const ALLE_STATUS: Status[] = ['offen', 'laeuft', 'blockiert', 'erledigt', 'verworfen'];
  const STATUS_OPTIONEN = ALLE_STATUS.map((s) => ({ wert: s, label: STATUS_TEXT[s] }));

  let {
    a,
    mitThema = false,
    nachId,
    onOeffnen,
    ebeneMax = 2,
  }: {
    a: AufgabeAntwort;
    mitThema?: boolean;
    nachId: Map<string, AufgabeAntwort>;
    onOeffnen: (id: string) => void;
    ebeneMax?: number;
  } = $props();

  let hatKinder = $derived(!!a.kinder?.length);
  let blockerListe = $derived(
    (a.braucht ?? [])
      .map((id) => nachId.get(id))
      .filter((b): b is AufgabeAntwort => !!b && b.status !== 'erledigt' && b.status !== 'verworfen'),
  );

  async function schnellwechsel(erledigt: boolean): Promise<void> {
    if (hatKinder || store.beschaeftigt) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status: erledigt ? 'erledigt' : 'offen' });
  }

  async function statusSetzen(e: Event): Promise<void> {
    const status = (e.target as HTMLSelectElement).value;
    if (!status || status === a.status) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status });
  }
</script>

<li class="{a.status} ebene-{Math.min(a.ebene ?? 0, ebeneMax)}" class:kopfknoten={hatKinder}>
  <Schreibbar>
    {#snippet children()}
      <Kontrollkaestchen
        checked={a.status === 'erledigt'}
        disabled={hatKinder || store.beschaeftigt}
        titel={hatKinder ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'offen ↔ erledigt'}
        onchange={schnellwechsel}
      />
    {/snippet}
  </Schreibbar>

  {#if store.darfSchreiben}
    <Schreibbar>
      {#snippet children()}
        <Auswahl
          class="status-wahl"
          klein
          wert={a.status}
          optionen={STATUS_OPTIONEN}
          disabled={hatKinder}
          onchange={statusSetzen}
          aria-label="Status ändern"
          title={hatKinder ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'Status ändern'}
        />
      {/snippet}
    </Schreibbar>
  {:else}
    <Statusmarke status={a.status} kompakt />
  {/if}

  <button type="button" class="aufgabe-text" onclick={() => onOeffnen(a.id)}>
    <span class="titel">{a.titel}</span>
    {#if mitThema || (a.prio && a.prio !== 'mittel') || a.dauer || blockerListe.length}
      <span class="aufgabe-meta">
        {#if mitThema && a.bereich}<Etikett>{a.bereich}</Etikett>{/if}
        {#if a.prio && a.prio !== 'mittel'}
          <Etikett ton={a.prio === 'kritisch' ? 'warn' : 'signal'}>{a.prio}</Etikett>
        {/if}
        {#if a.dauer}<Etikett>{a.dauer}</Etikett>{/if}
        {#if blockerListe.length}
          <Etikett ton="warn">braucht: {blockerListe.map((b) => b.titel).join(', ')}</Etikett>
        {/if}
      </span>
    {/if}
  </button>
</li>

<style>
  li {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    padding: var(--a-2);
    margin: 2px 0;
    border-radius: var(--r-s);
    border-left: 3px solid var(--farbe-linie);
  }
  li.ebene-1 { margin-left: var(--a-5); }
  li.ebene-2 { margin-left: var(--a-7); }
  li.kopfknoten { font-weight: 650; }
  li.laeuft { border-left-color: var(--farbe-signal); }
  li.blockiert { border-left-color: var(--farbe-warn); }
  li.erledigt { border-left-color: var(--farbe-gut); }
  li.verworfen { border-left-color: var(--farbe-linie-stark); }
  li.erledigt .titel { color: var(--farbe-text-2); text-decoration: line-through; }
  li.verworfen .titel { color: var(--farbe-text-2); opacity: 0.65; }

  :global(.status-wahl) { width: 136px; flex: none; }

  .aufgabe-text {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    background: none;
    border: 0;
    padding: var(--a-1);
    border-radius: var(--r-s);
    color: inherit;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .aufgabe-text:hover { background: var(--farbe-flaeche-hoch); }
  .titel { display: block; }
  .aufgabe-meta { display: flex; flex-wrap: wrap; gap: var(--a-1); }
</style>
