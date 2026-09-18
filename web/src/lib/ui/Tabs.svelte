<script lang="ts">
  // Reiter. Der Inhalt wird vom Aufrufer nach `aktiv` gewählt:
  //   <Tabs {tabs} bind:aktiv />  {#if aktiv === 'notizen'} … {/if}
  // Pfeiltasten ←/→, Pos1/Ende wechseln (Roving-Tabindex nach WAI-ARIA).
  import type { IconKomponente } from './icons';

  export interface Tab {
    id: string;
    label: string;
    zahl?: number | string;
    icon?: IconKomponente;
  }

  interface Props {
    tabs: Tab[];
    aktiv?: string;
    label?: string;
    onwechsel?: (id: string) => void;
  }

  let { tabs, aktiv = $bindable(tabs[0]?.id ?? ''), label = 'Reiter', onwechsel }: Props = $props();

  let knoepfe: HTMLButtonElement[] = $state([]);

  function waehlen(id: string, fokus = false): void {
    aktiv = id;
    onwechsel?.(id);
    if (fokus) knoepfe[tabs.findIndex((t) => t.id === id)]?.focus();
  }

  function taste(e: KeyboardEvent, i: number): void {
    let ziel = -1;
    if (e.key === 'ArrowRight') ziel = (i + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') ziel = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') ziel = 0;
    else if (e.key === 'End') ziel = tabs.length - 1;
    if (ziel < 0) return;
    e.preventDefault();
    waehlen(tabs[ziel].id, true);
  }
</script>

<div class="ui-tabs" role="tablist" aria-label={label}>
  {#each tabs as tab, i (tab.id)}
    {@const Icon = tab.icon}
    <button
      bind:this={knoepfe[i]}
      type="button"
      role="tab"
      aria-selected={aktiv === tab.id}
      tabindex={aktiv === tab.id ? 0 : -1}
      class:aktiv={aktiv === tab.id}
      onclick={() => waehlen(tab.id)}
      onkeydown={(e) => taste(e, i)}
    >
      {#if Icon}<Icon size={15} strokeWidth={1.8} aria-hidden="true" />{/if}
      <span>{tab.label}</span>
      {#if tab.zahl !== undefined}<span class="zahl">{tab.zahl}</span>{/if}
    </button>
  {/each}
</div>

<style>
  .ui-tabs {
    display: flex;
    gap: var(--a-5);
    border-bottom: 1px solid var(--farbe-linie);
    overflow-x: auto;
    scrollbar-width: none;
  }
  button {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    height: 40px;
    padding: 0 2px;
    border: 0;
    background: none;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    font-weight: 600;
    white-space: nowrap;
    transition: color var(--t-kurz);
  }
  button::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 2px;
    background: var(--farbe-signal);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform var(--t-mittel) var(--kurve);
  }
  button:hover { color: var(--farbe-text); }
  .aktiv { color: var(--farbe-text); }
  .aktiv::after { transform: scaleX(1); }
  .zahl { font-family: var(--schrift-mono); font-size: 0.7rem; font-weight: 500; color: var(--farbe-text-3); }
  .aktiv .zahl { color: var(--farbe-signal); }
</style>
