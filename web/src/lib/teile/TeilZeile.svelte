<script lang="ts">
  // Eine Teilezeile in der Listenansicht: Titel, Kategorie, Gesamtpreis,
  // Statuswechsler. Klick auf den Titel öffnet das Detailfenster.
  import type { TeilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { Auswahl, Etikett } from '../ui';
  import { vokabular } from '../vokabular.svelte';
  import { preisText, zahl, TEIL_STATUS_TON } from './format';

  let {
    t,
    onOeffnen,
  }: {
    t: TeilAntwort;
    onOeffnen: (id: string) => void;
  } = $props();

  const statusBearbeitbar = $derived(!!store.daten?.bearbeitbar?.teil_felder?.status?.web);

  async function statusSetzen(e: Event): Promise<void> {
    const wert = (e.target as HTMLSelectElement).value;
    if (!wert || wert === t.status) return;
    await store.teilPatch(t.id, 'status', wert);
  }
</script>

<li class="teilzeile">
  <button type="button" class="titelknopf" onclick={() => onOeffnen(t.id)}>
    <span class="titel">{t.titel}</span>
    <span class="meta">
      {#if t.kategorie}<Etikett>{t.kategorie}</Etikett>{/if}
      {#if zahl(t.menge) > 1}<span class="zusatz">{t.menge} {t.einheit}</span>{/if}
    </span>
  </button>
  <span class="preis">{preisText(t)}</span>
  {#if store.darfSchreiben && statusBearbeitbar}
    <Schreibbar>
      {#snippet children()}
        <Auswahl
          class="status-wahl"
          klein
          wert={t.status}
          optionen={vokabular.teilStatus}
          onchange={statusSetzen}
          aria-label="Status ändern"
        />
      {/snippet}
    </Schreibbar>
  {:else}
    <Etikett ton={TEIL_STATUS_TON[t.status] ?? 'neutral'}>{t.status || '—'}</Etikett>
  {/if}
</li>

<style>
  .teilzeile {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    padding: var(--a-2) var(--a-4);
    border-bottom: 1px solid var(--farbe-linie);
  }
  .teilzeile:last-child {
    border-bottom: none;
  }
  .titelknopf {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    background: none;
    border: 0;
    padding: var(--a-1);
    border-radius: var(--r-s);
    color: inherit;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .titelknopf:hover {
    background: var(--farbe-flaeche-hoch);
  }
  .titel {
    font-weight: 550;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }
  .meta {
    display: flex;
    align-items: center;
    gap: var(--a-2);
  }
  .zusatz {
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
  }
  .preis {
    flex: none;
    font-family: var(--schrift-mono);
    font-weight: 600;
    white-space: nowrap;
  }
  /* Unter `.teilzeile` gebunden — unscoped leckte die Breite in jede andere
     Ansicht mit einem Feld dieses Namens. */
  .teilzeile :global(.status-wahl) {
    width: 136px;
    flex: none;
  }
</style>
