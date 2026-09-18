<script lang="ts">
  // Leerzustand: wenn eine Liste leer ist, ein Filter nichts findet oder eine
  // Ansicht noch fehlt. children = Aktion (z. B. Knopf "Aufgabe anlegen").
  import type { Snippet } from 'svelte';
  import type { IconKomponente } from './icons';
  import { IconLeer } from './icons';

  interface Props {
    titel: string;
    text?: string;
    icon?: IconKomponente;
    kompakt?: boolean;
    marke?: string;
    children?: Snippet;
  }

  let { titel, text, icon: Icon = IconLeer, kompakt = false, marke, children }: Props = $props();
</script>

<div class="ui-leer" class:kompakt>
  <div class="zeichen" aria-hidden="true">
    <Icon size={kompakt ? 20 : 26} strokeWidth={1.5} />
  </div>
  {#if marke}<span class="marke">{marke}</span>{/if}
  <p class="titel">{titel}</p>
  {#if text}<p class="text">{text}</p>{/if}
  {#if children}<div class="aktion">{@render children()}</div>{/if}
</div>

<style>
  .ui-leer {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: var(--a-8) var(--a-5);
    gap: var(--a-2);
  }
  .kompakt { padding: var(--a-5) var(--a-4); gap: 6px; }
  .zeichen {
    width: 64px;
    height: 64px;
    display: grid;
    place-items: center;
    margin-bottom: var(--a-2);
    color: var(--farbe-text-2);
    border: 1px dashed var(--farbe-linie-stark);
    border-radius: 50%;
    background:
      repeating-linear-gradient(-45deg, transparent 0 5px, var(--farbe-raster) 5px 6px),
      var(--farbe-flaeche);
  }
  .kompakt .zeichen { width: 44px; height: 44px; margin-bottom: 2px; }
  .marke {
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-signal);
    letter-spacing: 0.04em;
  }
  .titel { font-size: var(--text-l); font-weight: 650; font-stretch: var(--breit); letter-spacing: -0.01em; }
  .kompakt .titel { font-size: var(--text-m); }
  .text { color: var(--farbe-text-2); max-width: 44ch; font-size: var(--text-s); }
  .aktion { margin-top: var(--a-3); display: flex; gap: var(--a-2); }
</style>
