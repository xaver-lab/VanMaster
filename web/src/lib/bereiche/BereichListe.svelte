<script lang="ts">
  // Übersicht aller Bereiche — Name, Kurzbeschreibung, Fortschritt, Phase.
  // Sortierung wie tools/bereiche.py / docs/js/themen.js (SORTIERUNGEN,
  // Voreinstellung "baustellen"), gemerkt wie in AufgabenListe.svelte.
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { sortiere, fortschritt, SORTIERUNGEN, SORT_WORT, STANDARD_SORTIERUNG, type Sortierung } from './sortierung';

  const STATUS_WORT: Record<string, string> = { 'in-arbeit': 'in Arbeit', geplant: 'geplant', fertig: 'fertig' };

  function gemerkt(schluessel: string, standard: Sortierung): Sortierung {
    try {
      const wert = localStorage.getItem(schluessel);
      return (SORTIERUNGEN as readonly string[]).includes(wert ?? '') ? (wert as Sortierung) : standard;
    } catch {
      return standard;
    }
  }
  function merken(schluessel: string, wert: string): void {
    try {
      localStorage.setItem(schluessel, wert);
    } catch {
      /* egal — nur Komfort */
    }
  }

  let sortierung = $state<Sortierung>(gemerkt('bereichSortierung', STANDARD_SORTIERUNG));
  function waehlen(): void {
    merken('bereichSortierung', sortierung);
  }

  const bereiche = $derived(store.daten?.bereiche ?? []);
  const aufgaben = $derived(store.daten?.aufgaben ?? []);
  const sortiert = $derived(sortiere(bereiche, aufgaben, sortierung));
</script>

<div class="leiste">
  <select class="wahl" bind:value={sortierung} onchange={waehlen} aria-label="Sortierung">
    {#each SORTIERUNGEN as art (art)}
      <option value={art}>{SORT_WORT[art]}</option>
    {/each}
  </select>
</div>

{#if !sortiert.length}
  <p class="leer">Noch kein Bereich unter <code>vault/Bereiche/</code> angelegt.</p>
{:else}
  <div class="raster">
    {#each sortiert as b (b.name)}
      {@const f = fortschritt(aufgaben, b.name)}
      <button type="button" class="zeile" onclick={() => router.gehe('bereiche', b.name)}>
        <div class="obenzeile">
          <span class="name">{b.name}</span>
          {#if b.phase != null}<span class="chip">Phase {b.phase}</span>{/if}
          <span class="chip status-{b.status}">{STATUS_WORT[b.status] ?? b.status}</span>
        </div>
        {#if b.kurz}<p class="kurz">{b.kurz}</p>{/if}
        <div class="balken"><span style="width: {f.gesamt ? (100 * f.fertig) / f.gesamt : 0}%"></span></div>
        <span class="zahl">{f.fertig}/{f.gesamt} Aufgaben</span>
      </button>
    {/each}
  </div>
{/if}

<style>
  .leiste {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1rem;
  }
  .wahl {
    min-height: 38px;
    padding: 0 0.75rem;
    background: var(--flaeche);
    color: var(--text);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
  }
  .wahl:focus {
    outline: none;
    border-color: var(--akzent);
  }

  .raster {
    display: grid;
    gap: 0.7rem;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
  .zeile {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    text-align: left;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius);
    padding: 0.9rem 1rem;
    box-shadow: var(--schatten);
  }
  .zeile:hover {
    border-color: var(--linie-hell);
  }
  .obenzeile {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .name {
    font-weight: 650;
    font-size: 1rem;
  }
  .chip {
    margin-left: auto;
    font-size: 0.7rem;
    padding: 0.15rem 0.55rem;
    border-radius: 99px;
    background: var(--flaeche-hoch);
    color: var(--gedaempft);
    border: 1px solid var(--linie);
    white-space: nowrap;
  }
  .chip + .chip {
    margin-left: 0;
  }
  .chip.status-in-arbeit {
    color: var(--wartet);
    border-color: color-mix(in srgb, var(--wartet) 45%, transparent);
    background: var(--wartet-tief);
  }
  .chip.status-fertig {
    color: var(--gut);
    border-color: color-mix(in srgb, var(--gut) 45%, transparent);
    background: var(--gut-tief);
  }
  .kurz {
    margin: 0;
    color: var(--gedaempft);
    font-size: 0.85rem;
  }
  .balken {
    height: 7px;
    background: var(--flaeche-hoch);
    border-radius: 99px;
    overflow: hidden;
  }
  .balken span {
    display: block;
    height: 100%;
    background: var(--gut);
    border-radius: 99px;
    transition: width 0.5s ease;
  }
  .zahl {
    color: var(--gedaempft);
    font-size: 0.78rem;
    font-variant-numeric: tabular-nums;
  }
</style>
