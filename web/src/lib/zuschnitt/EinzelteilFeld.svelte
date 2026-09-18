<script lang="ts">
  // Ein Feld im Einzelteil-Detail: editierbar (Schreibbar) oder als reiner
  // Text im Lesemodus / wenn die Matrix es sperrt. Trägt eigene Speicherung
  // per onblur/onchange — der Aufrufer bekommt nur den neuen Wert.
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { Auswahl, Feld, Textfeld } from '../ui';

  type Option = string | { wert: string; label: string };

  let {
    label,
    wert,
    art = 'text',
    optionen,
    leer,
    einheit,
    mono = false,
    bearbeitbar = true,
    onSpeichern,
  }: {
    label: string;
    wert: string;
    art?: 'text' | 'number' | 'auswahl' | 'textfeld';
    optionen?: Option[];
    leer?: string;
    einheit?: string;
    mono?: boolean;
    bearbeitbar?: boolean;
    onSpeichern: (wert: string) => void;
  } = $props();

  function anzeigename(): string {
    if (art !== 'auswahl' || !optionen) return wert || '—';
    const treffer = optionen.find((o) => (typeof o === 'string' ? o === wert : o.wert === wert));
    if (!treffer) return wert || '—';
    return typeof treffer === 'string' ? treffer : treffer.label;
  }
</script>

{#if store.darfSchreiben && bearbeitbar}
  <Schreibbar>
    {#snippet children()}
      {#if art === 'auswahl'}
        <Auswahl {label} {wert} optionen={optionen ?? []} {leer} onchange={(e) => onSpeichern((e.target as HTMLSelectElement).value)} />
      {:else if art === 'textfeld'}
        <Textfeld {label} {wert} zeilen={4} onblur={(e) => onSpeichern((e.currentTarget as HTMLTextAreaElement).value)} />
      {:else}
        <Feld
          {label}
          {wert}
          {einheit}
          {mono}
          type={art === 'number' ? 'number' : 'text'}
          onblur={(e) => onSpeichern((e.currentTarget as HTMLInputElement).value)}
        />
      {/if}
    {/snippet}
  </Schreibbar>
{:else}
  <div class="statisch">
    <span class="label">{label}</span>
    <span class="wert" class:mono>{anzeigename()}{#if einheit && wert} {einheit}{/if}</span>
  </div>
{/if}

<style>
  .statisch {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .label {
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
  }
  .wert {
    font-size: var(--text-s);
    overflow-wrap: break-word;
  }
  .mono {
    font-family: var(--schrift-mono);
  }
</style>
