<script lang="ts">
  // Filterchip: schaltbar (aria-pressed), optional mit Zahl und Icon.
  // Aktiv = dunkel gefüllt ("gestempelt"), nicht farbig — Farbe bleibt Status.
  import type { Snippet } from 'svelte';
  import type { IconKomponente } from './icons';

  interface Props {
    aktiv?: boolean;
    zahl?: number | string | null;
    icon?: IconKomponente;
    disabled?: boolean;
    onclick?: (e: MouseEvent) => void;
    children: Snippet;
  }

  let { aktiv = $bindable(false), zahl = null, icon: Icon, disabled = false, onclick, children }: Props = $props();
</script>

<button
  type="button"
  class="ui-chip"
  class:aktiv
  aria-pressed={aktiv}
  {disabled}
  onclick={(e) => {
    if (onclick) onclick(e);
    else aktiv = !aktiv;
  }}
>
  {#if Icon}<Icon size={14} strokeWidth={1.9} aria-hidden="true" />{/if}
  <span>{@render children()}</span>
  {#if zahl !== null && zahl !== undefined}<span class="zahl">{zahl}</span>{/if}
</button>

<style>
  .ui-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 30px;
    padding: 0 10px;
    border: 1px solid var(--farbe-linie-stark);
    border-radius: var(--r-m);
    background: var(--farbe-flaeche);
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    font-weight: 550;
    white-space: nowrap;
    transition: background-color var(--t-kurz), color var(--t-kurz), border-color var(--t-kurz),
      transform var(--t-kurz) var(--kurve);
  }
  .ui-chip:hover:not(:disabled) { color: var(--farbe-text); border-color: var(--farbe-text-3); }
  .ui-chip:active:not(:disabled) { transform: scale(0.97); }
  .ui-chip:disabled { opacity: 0.45; }
  .zahl {
    font-family: var(--schrift-mono);
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--farbe-text-3);
    padding-left: 7px;
    border-left: 1px solid var(--farbe-linie);
  }
  .aktiv {
    background: var(--farbe-tinte-fuellung);
    border-color: var(--farbe-tinte-fuellung);
    color: var(--farbe-auf-tinte);
  }
  .aktiv:hover:not(:disabled) { color: var(--farbe-auf-tinte); border-color: var(--farbe-tinte-fuellung); }
  .aktiv .zahl { color: color-mix(in srgb, var(--farbe-auf-tinte) 70%, transparent); border-color: color-mix(in srgb, var(--farbe-auf-tinte) 25%, transparent); }
</style>
