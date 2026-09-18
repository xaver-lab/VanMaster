<script lang="ts">
  // Eine Aufgabenzeile: Kästchen (offen↔erledigt), Statuswechsler (alle
  // Status), Titel, Meta (Thema/Prio/Dauer/Blocker). Klick auf die Zeile
  // öffnet das Detailfenster; Kästchen und Wechsler stoppen die Ausbreitung.
  import type { AufgabeAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';

  const STATUS_WORT: Record<string, string> = {
    offen: 'offen',
    laeuft: 'läuft',
    blockiert: 'blockiert',
    erledigt: 'erledigt',
    verworfen: 'verworfen',
  };
  const ALLE_STATUS = ['offen', 'laeuft', 'blockiert', 'erledigt', 'verworfen'];

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

  let menueOffen = $state(false);
  let hatKinder = $derived(!!a.kinder?.length);
  let blockerListe = $derived(
    (a.braucht ?? [])
      .map((id) => nachId.get(id))
      .filter((b): b is AufgabeAntwort => !!b && b.status !== 'erledigt' && b.status !== 'verworfen'),
  );

  async function schnellwechsel(e: Event): Promise<void> {
    e.stopPropagation();
    if (hatKinder || store.beschaeftigt) return;
    const ziel = a.status === 'erledigt' ? 'offen' : 'erledigt';
    await store.aufgabePatch(a.id, a.datei ?? '', { status: ziel });
  }

  async function statusSetzen(e: Event, status: string): Promise<void> {
    e.stopPropagation();
    menueOffen = false;
    if (status === a.status) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status });
  }

  function wechslerKlick(e: Event): void {
    e.stopPropagation();
    if (hatKinder) return;
    menueOffen = !menueOffen;
  }
</script>

<svelte:window onclick={() => (menueOffen = false)} />

<li
  class="{a.status} ebene-{Math.min(a.ebene ?? 0, ebeneMax)}"
  class:kopfknoten={hatKinder}
  role="button"
  tabindex="0"
  onclick={() => onOeffnen(a.id)}
  onkeydown={(e) => e.key === 'Enter' && onOeffnen(a.id)}
>
  <Schreibbar>
    {#snippet children()}
      <input
        type="checkbox"
        class="kaestchen"
        checked={a.status === 'erledigt'}
        disabled={hatKinder || store.beschaeftigt}
        title={hatKinder ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'offen ↔ erledigt'}
        onclick={schnellwechsel}
      />
    {/snippet}
  </Schreibbar>
  <Schreibbar>
    {#snippet children()}
      <div class="wechsler">
        <button
          type="button"
          class="status {a.status}"
          disabled={hatKinder}
          title={hatKinder ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'Status ändern'}
          onclick={wechslerKlick}
        >
          {a.status === 'verworfen' ? 'verworfen' : STATUS_WORT[a.status] ?? a.status}
          {#if !hatKinder}▾{/if}
        </button>
        {#if menueOffen}
          <div class="menue">
            {#each ALLE_STATUS as s (s)}
              <button
                type="button"
                class:aktiv={a.status === s}
                onclick={(e) => statusSetzen(e, s)}
              >
                {STATUS_WORT[s]}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/snippet}
  </Schreibbar>
  {#if !store.darfSchreiben}
    <span class="status {a.status}">
      {a.status === 'verworfen' ? 'verworfen' : STATUS_WORT[a.status] ?? a.status}
    </span>
  {/if}

  <div class="aufgabe-text">
    <span class="titel">{a.titel}</span>
    {#if mitThema || (a.prio && a.prio !== 'mittel') || a.dauer || blockerListe.length}
      <div class="aufgabe-meta">
        {#if mitThema && a.bereich}
          <span class="aufgabe-marke thema">{a.bereich}</span>
        {/if}
        {#if a.prio && a.prio !== 'mittel'}
          <span class="aufgabe-marke {a.prio}">{a.prio}</span>
        {/if}
        {#if a.dauer}
          <span class="aufgabe-marke">{a.dauer}</span>
        {/if}
        {#if blockerListe.length}
          <span class="aufgabe-marke blocker">braucht: {blockerListe.map((b) => b.titel).join(', ')}</span>
        {/if}
      </div>
    {/if}
  </div>
</li>

<style>
  .kaestchen {
    width: 1.05rem;
    height: 1.05rem;
    margin: 0.15rem 0 0;
    accent-color: var(--akzent);
    cursor: pointer;
  }

  li {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.45rem 0.5rem;
    margin: 0.15rem 0;
    border-radius: var(--radius-klein);
    border-left: 3px solid var(--linie);
  }
  li:hover {
    background: var(--flaeche-hoch);
    cursor: pointer;
  }
  li.ebene-1 {
    margin-left: 1.1rem;
  }
  li.ebene-2 {
    margin-left: 2.2rem;
  }
  li.kopfknoten {
    font-weight: 600;
  }
  li.laeuft {
    border-left-color: var(--akzent);
  }
  li.blockiert {
    border-left-color: var(--warn);
  }
  li.erledigt {
    border-left-color: var(--gut);
  }
  li.verworfen {
    border-left-color: var(--linie-hell);
  }
  li.erledigt .titel {
    color: var(--gedaempft);
    text-decoration: line-through;
  }
  li.verworfen .titel {
    color: var(--gedaempft);
    opacity: 0.65;
  }

  .wechsler {
    position: relative;
  }
  .status {
    font-size: 0.7rem;
    padding: 0.05rem 0.5rem;
    border-radius: 99px;
    border: 1px solid var(--linie);
    white-space: nowrap;
    background: none;
    color: var(--gedaempft);
  }
  .status.offen {
    color: var(--gedaempft);
    border-color: var(--linie);
  }
  .status.laeuft {
    color: var(--akzent);
    border-color: transparent;
    background: var(--akzent-tief);
  }
  .status.blockiert {
    color: var(--warn);
    border-color: transparent;
    background: var(--warn-tief);
  }
  .status.erledigt {
    color: var(--gut);
    border-color: transparent;
    background: var(--gut-tief);
  }
  .status.verworfen {
    color: var(--gedaempft);
  }
  .status:disabled {
    opacity: 0.5;
    cursor: default;
  }
  .wechsler > .status {
    min-height: 26px;
    cursor: pointer;
  }
  .wechsler > .status:hover:not(:disabled) {
    border-color: var(--akzent);
    color: var(--text);
  }
  .menue {
    position: absolute;
    left: 0;
    top: calc(100% + 4px);
    z-index: 12;
    min-width: 10rem;
    padding: 0.3rem;
    background: var(--flaeche-hoch);
    border: 1px solid var(--linie-hell);
    border-radius: var(--radius-klein);
    box-shadow: var(--schatten);
    display: flex;
    flex-direction: column;
    gap: 1px;
  }
  .menue button {
    text-align: left;
    background: none;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 0.55rem;
    font-size: 0.85rem;
    color: var(--text);
  }
  .menue button:hover {
    background: var(--flaeche);
  }
  .menue button.aktiv {
    color: var(--akzent);
  }

  .aufgabe-text {
    flex: 1 1 auto;
    min-width: 0;
  }
  .aufgabe-text .titel {
    display: block;
  }
  .aufgabe-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.2rem;
  }
  .aufgabe-marke {
    font-size: 0.7rem;
    padding: 0.05rem 0.45rem;
    border-radius: 99px;
    border: 1px solid var(--linie);
    color: var(--gedaempft);
    white-space: nowrap;
  }
  .aufgabe-marke.kritisch {
    color: var(--warn);
    border-color: transparent;
    background: var(--warn-tief);
  }
  .aufgabe-marke.hoch {
    color: var(--akzent);
    border-color: transparent;
    background: var(--akzent-tief);
  }
  .aufgabe-marke.blocker {
    color: var(--wartet);
    border-color: transparent;
    background: var(--wartet-tief);
    white-space: normal;
  }
  .aufgabe-marke.thema {
    color: var(--gedaempft);
  }
</style>
