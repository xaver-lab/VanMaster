<script lang="ts">
  // Etikett: kleine Beschriftung für Kategorien, Prioritäten, Zähler.
  // Keine Aktion — für klickbare Filter den Chip nehmen.
  import type { Snippet } from 'svelte';
  import type { IconKomponente } from './icons';

  interface Props {
    ton?: 'neutral' | 'signal' | 'gut' | 'info' | 'warn' | 'tinte';
    icon?: IconKomponente;
    mono?: boolean;
    children: Snippet;
  }

  let { ton = 'neutral', icon: Icon, mono = false, children }: Props = $props();
</script>

<span class="ui-etikett {ton}" class:mono>
  {#if Icon}<Icon size={12} strokeWidth={2.2} aria-hidden="true" />{/if}
  {@render children()}
</span>

<style>
  .ui-etikett {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 20px;
    padding: 0 6px;
    border-radius: var(--r-s);
    font-size: 0.6875rem;
    font-weight: 650;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    white-space: nowrap;
    vertical-align: middle;
    line-height: 1;
  }
  .mono { font-family: var(--schrift-mono); text-transform: none; letter-spacing: 0; font-weight: 500; font-stretch: 100%; }
  .neutral { background: var(--farbe-flaeche-hoch); color: var(--farbe-text-2); box-shadow: inset 0 0 0 1px var(--farbe-linie); }
  .signal { background: var(--farbe-signal-grund); color: var(--farbe-signal); }
  .gut { background: var(--farbe-gut-grund); color: var(--farbe-gut); }
  .info { background: var(--farbe-info-grund); color: var(--farbe-info); }
  .warn { background: var(--farbe-warn-grund); color: var(--farbe-warn); }
  .tinte { background: var(--farbe-tinte-fuellung); color: var(--farbe-auf-tinte); }
</style>
