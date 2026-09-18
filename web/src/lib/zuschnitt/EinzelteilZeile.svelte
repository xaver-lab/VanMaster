<script lang="ts">
  // Eine Zeile der Einzelteilliste: Titel (öffnet Detail), Maß in Mono,
  // Material, Anzahl, Status, Teil-Bezug.
  import type { EinzelteilAntwort, TeilAntwort } from '../api-typen';
  import { Etikett } from '../ui';
  import { bauteilStatusTon } from './status';
  import { massText } from './mass';

  let {
    e,
    mitBereich = false,
    teileNachId,
    onOeffnen,
  }: {
    e: EinzelteilAntwort;
    mitBereich?: boolean;
    teileNachId: Map<string, TeilAntwort>;
    onOeffnen: (id: string) => void;
  } = $props();

  const teilTitel = $derived(e.teil_id ? teileNachId.get(e.teil_id)?.titel ?? e.teil_id : '');
</script>

<li>
  <button type="button" class="zeile" onclick={() => onOeffnen(e.id)}>
    <span class="titel-spalte">
      <span class="titel">{e.titel}</span>
      <span class="meta">
        {#if mitBereich && e.bereich}<Etikett>{e.bereich}</Etikett>{/if}
        {#if e.art}<Etikett>{e.art}</Etikett>{/if}
        {#if e.material}<Etikett ton="tinte">{e.material}</Etikett>{/if}
        {#if teilTitel}<Etikett ton="info">Teil: {teilTitel}</Etikett>{/if}
      </span>
    </span>
    <span class="mass">{massText(e)}</span>
    <span class="anzahl">× {e.anzahl || '1'}</span>
    {#if e.status}<Etikett ton={bauteilStatusTon(e.status)}>{e.status}</Etikett>{/if}
  </button>
</li>

<style>
  li {
    list-style: none;
    margin: 2px 0;
  }
  .zeile {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    width: 100%;
    padding: var(--a-2);
    background: none;
    border: 0;
    border-radius: var(--r-s);
    color: inherit;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .zeile:hover {
    background: var(--farbe-flaeche-hoch);
  }
  .titel-spalte {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .titel {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-1);
  }
  .mass {
    flex: none;
    font-family: var(--schrift-mono);
    font-size: var(--text-s);
    color: var(--farbe-text-2);
    white-space: nowrap;
  }
  .anzahl {
    flex: none;
    font-family: var(--schrift-mono);
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
</style>
