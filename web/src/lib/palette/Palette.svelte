<script lang="ts">
  // Befehlspalette: Suchen über alle Inhalte und Springen per Tastatur.
  // Pfeile wählen, Enter öffnet, Esc schließt (macht der Dialog).
  import { tick } from 'svelte';
  import { store } from '../daten.svelte';
  import { palette, paletteSchliessen } from '../palette.svelte';
  import { Dialog, Feld, Kbd } from '../ui';
  import { IconSuche } from '../ui/icons';
  import { ART_MEHRZAHL, befehle, inhalte, type Eintrag } from './quellen';
  import { suchen } from './suche';

  let text = $state('');
  let pos = $state(0);
  let liste = $state<HTMLElement>();

  const listeId = 'palette-liste';
  const optionId = (i: number): string => `palette-option-${i}`;

  const alle = $derived([...befehle(), ...(store.daten ? inhalte(store.daten) : [])]);
  const gruppen = $derived(suchen(alle, text));
  const flach = $derived(gruppen.flatMap((g) => g.eintraege));

  // Beim Öffnen leer anfangen
  $effect(() => {
    if (palette.offen) {
      text = '';
      pos = 0;
    }
  });

  function eingabe(): void {
    pos = 0;
    liste?.scrollTo({ top: 0 });
  }

  async function zeigen(): Promise<void> {
    await tick();
    document.getElementById(optionId(pos))?.scrollIntoView({ block: 'nearest' });
  }

  function oeffnen(e: Eintrag | undefined): void {
    if (!e) return;
    paletteSchliessen();
    e.ausfuehren();
  }

  function tastatur(e: KeyboardEvent): void {
    const n = flach.length;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!n) return;
      pos = (pos + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
      zeigen();
    } else if (e.key === 'Home' && e.ctrlKey) {
      pos = 0;
      zeigen();
    } else if (e.key === 'End' && e.ctrlKey) {
      pos = Math.max(0, n - 1);
      zeigen();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      oeffnen(flach[pos]);
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      // Strg+K bei offener Palette: nicht an den Browser, nur Eingabe markieren
      e.preventDefault();
      (e.currentTarget as HTMLInputElement).select();
    }
  }
</script>

<Dialog bind:offen={palette.offen} titel="Suchen oder springen" breite="m">
  <Feld
    bind:wert={text}
    icon={IconSuche}
    placeholder="Bereich, Aufgabe, Teil, Befehl …"
    aria-label="Suchen oder springen"
    autocomplete="off"
    spellcheck={false}
    role="combobox"
    aria-expanded={flach.length > 0}
    aria-controls={listeId}
    aria-autocomplete="list"
    aria-activedescendant={flach.length ? optionId(pos) : undefined}
    data-fokus
    oninput={eingabe}
    onkeydown={tastatur}
  />

  <div class="treffer" bind:this={liste} id={listeId} role="listbox" aria-label="Treffer">
    {#each gruppen as g (g.art)}
      {@const start = flach.indexOf(g.eintraege[0])}
      <div class="gruppe" role="group" aria-labelledby="palette-gruppe-{g.art}">
        <div class="kopf" id="palette-gruppe-{g.art}">{ART_MEHRZAHL[g.art]}</div>
        {#each g.eintraege as e, j (e.schluessel)}
          {@const i = start + j}
          <!-- Tastatur läuft über das Eingabefeld (aria-activedescendant) -->
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <div
            class="option"
            class:aktiv={i === pos}
            id={optionId(i)}
            role="option"
            tabindex="-1"
            aria-selected={i === pos}
            onmousemove={() => (pos = i)}
            onclick={() => oeffnen(e)}
          >
            <span class="art">{e.art}</span>
            <span class="titel">{e.titel}</span>
            {#if e.neben}<span class="neben">{e.neben}</span>{/if}
          </div>
        {/each}
      </div>
    {:else}
      <p class="leer">Nichts gefunden.</p>
    {/each}
  </div>

  {#snippet fuss()}
    <div class="hinweise">
      <span><Kbd tasten="↑ ↓" /> wählen</span>
      <span><Kbd tasten="Enter" /> öffnen</span>
      <span><Kbd tasten="Esc" /> schließen</span>
      {#if flach.length}<span class="zahl anzahl">{flach.length} Treffer</span>{/if}
    </div>
  {/snippet}
</Dialog>

<style>
  .treffer {
    max-height: min(55vh, 460px);
    overflow-y: auto;
    margin: 0 calc(-1 * var(--a-2));
    display: flex;
    flex-direction: column;
    gap: var(--a-2);
  }
  .kopf {
    padding: var(--a-1) var(--a-2);
    font-size: var(--text-xs);
    font-weight: 650;
    font-stretch: var(--schmal);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--farbe-text-2);
  }
  .option {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    min-width: 0;
    padding: var(--a-2);
    border-radius: var(--r-m);
    cursor: pointer;
    font-size: var(--text-s);
    border-left: 2px solid transparent;
  }
  .option.aktiv {
    background: var(--farbe-flaeche-hoch);
    border-left-color: var(--farbe-signal);
  }
  .art {
    flex: 0 0 6.5rem;
    font-size: var(--text-xs);
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .titel {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--farbe-text);
  }
  .neben {
    flex: 0 1 auto;
    max-width: 45%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
  }
  .leer {
    padding: var(--a-5) 0;
    text-align: center;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
  }
  .hinweise {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--a-4);
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
  }
  .anzahl { margin-left: auto; font-family: var(--schrift-mono); }
  @media (max-width: 480px) {
    .art { display: none; }
  }
</style>
