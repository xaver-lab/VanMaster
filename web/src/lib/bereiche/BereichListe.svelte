<script lang="ts">
  // Übersicht aller Bereiche — Name, Kurzbeschreibung, Fortschritt, Phase.
  // Sortierung wie tools/bereiche.py / docs/js/themen.js (SORTIERUNGEN,
  // Voreinstellung "baustellen"), gemerkt wie in AufgabenListe.svelte.
  import { store } from '../daten.svelte';
  import { Auswahl, Etikett, FortschrittBalken, Karte, Leerzustand } from '../ui';
  import { sortiere, fortschritt, SORTIERUNGEN, SORT_WORT, STANDARD_SORTIERUNG, type Sortierung } from './sortierung';

  const STATUS_WORT: Record<string, string> = { 'in-arbeit': 'in Arbeit', geplant: 'geplant', fertig: 'fertig' };
  const STATUS_TON: Record<string, 'gut' | 'signal' | 'neutral'> = {
    fertig: 'gut',
    'in-arbeit': 'signal',
    geplant: 'neutral',
  };

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
  function waehlen(wert: string): void {
    sortierung = wert as Sortierung;
    merken('bereichSortierung', wert);
  }

  const sortierOptionen = SORTIERUNGEN.map((art) => ({ wert: art, label: SORT_WORT[art] }));

  const bereiche = $derived(store.daten?.bereiche ?? []);
  const aufgaben = $derived(store.daten?.aufgaben ?? []);
  const sortiert = $derived(sortiere(bereiche, aufgaben, sortierung));
</script>

<div class="leiste">
  <Auswahl
    class="sortier-wahl"
    wert={sortierung}
    optionen={sortierOptionen}
    onchange={(e) => waehlen((e.target as HTMLSelectElement).value)}
    aria-label="Sortierung"
    klein
  />
</div>

{#if !sortiert.length}
  <Leerzustand titel="Noch kein Bereich angelegt" text="Unter vault/Bereiche/ eine Markdown-Datei anlegen." />
{:else}
  <div class="raster">
    {#each sortiert as b (b.name)}
      {@const f = fortschritt(aufgaben, b.name)}
      <Karte href="#/bereiche/{encodeURIComponent(b.name)}" polster="eng">
        <div class="obenzeile">
          <span class="name">{b.name}</span>
          {#if b.phase != null}<Etikett>Phase {b.phase}</Etikett>{/if}
          <Etikett ton={STATUS_TON[b.status] ?? 'neutral'}>{STATUS_WORT[b.status] ?? b.status}</Etikett>
        </div>
        {#if b.kurz}<p class="kurz">{b.kurz}</p>{/if}
        <FortschrittBalken wert={f.gesamt ? f.fertig / f.gesamt : 0} zahl="{f.fertig}/{f.gesamt} Aufgaben" />
      </Karte>
    {/each}
  </div>
{/if}

<style>
  .leiste {
    display: flex;
    justify-content: flex-end;
    margin-bottom: var(--a-4);
  }
  /* Unter `.leiste` gebunden — unscoped leckte die Breite in jede andere
     Ansicht, die zufällig denselben Klassennamen benutzt. */
  .leiste :global(.sortier-wahl) {
    width: 12rem;
  }

  .raster {
    display: grid;
    gap: var(--a-3);
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
  .obenzeile {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    flex-wrap: wrap;
    margin-bottom: var(--a-2);
  }
  .name {
    font-weight: 650;
    font-size: var(--text-m);
  }
  .obenzeile :global(.ui-etikett:last-child) {
    margin-left: auto;
  }
  .kurz {
    margin: 0 0 var(--a-3);
    color: var(--farbe-text-2);
    font-size: var(--text-s);
  }
</style>
