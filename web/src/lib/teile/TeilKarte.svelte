<script lang="ts">
  // Teilkarte für die Rasteransicht: Titel, Preis, Beschreibung, Meta-Zeile
  // (Kategorie, Menge, Kennwerte, Gewicht, Händler, Shoplink), Statuswechsler.
  import type { TeilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { Auswahl, Etikett, Karte } from '../ui';
  import { vokabular } from '../vokabular.svelte';
  import { dezimal } from '../zahlformat';
  import { IconExtern } from '../ui/icons';
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

<Karte polster="eng" class="teilkarte">
  <button type="button" class="klickflaeche" onclick={() => onOeffnen(t.id)} aria-label="{t.titel} öffnen">
    <div class="kopf">
      <span class="titel">{t.titel}</span>
      <span class="preis">{preisText(t)}</span>
    </div>
    {#if t.beschreibung}<p class="beschreibung">{t.beschreibung}</p>{/if}
    <div class="meta">
      {#if t.kategorie}<Etikett>{t.kategorie}</Etikett>{/if}
      {#if zahl(t.menge) !== 1}<span>{t.menge} {t.einheit}</span>{/if}
      {#if t.kennwerte}<span>{t.kennwerte}</span>{/if}
      {#if zahl(t.gewicht_kg)}<span>{dezimal(zahl(t.gewicht_kg))} kg</span>{/if}
      {#if t.haendler}<span>{t.haendler}</span>{/if}
    </div>
  </button>
  <div class="fuss">
    {#if t.link}
      <a class="shoplink" href={t.link} target="_blank" rel="noopener" onclick={(e) => e.stopPropagation()}>
        Shop <IconExtern size={13} strokeWidth={1.9} aria-hidden="true" />
      </a>
    {/if}
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
  </div>
</Karte>

<style>
  :global(.teilkarte) {
    display: flex;
    flex-direction: column;
  }
  .klickflaeche {
    display: flex;
    flex-direction: column;
    gap: var(--a-2);
    width: 100%;
    background: none;
    border: 0;
    padding: 0;
    color: inherit;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .kopf {
    display: flex;
    align-items: baseline;
    gap: var(--a-2);
  }
  .titel {
    font-weight: 650;
    flex: 1 1 auto;
    min-width: 0;
  }
  .preis {
    flex: none;
    font-family: var(--schrift-mono);
    font-weight: 600;
  }
  .beschreibung {
    margin: 0;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
  }
  .fuss {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    margin-top: var(--a-3);
    padding-top: var(--a-3);
    border-top: 1px solid var(--farbe-linie);
  }
  .shoplink {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--farbe-info);
    font-size: var(--text-s);
    text-decoration: none;
  }
  .shoplink:hover {
    text-decoration: underline;
  }
  .fuss :global(.ui-etikett) {
    margin-left: auto;
  }
  .fuss :global(.status-wahl) {
    margin-left: auto;
    width: 136px;
    flex: none;
  }
</style>
