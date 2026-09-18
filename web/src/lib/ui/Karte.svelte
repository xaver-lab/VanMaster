<script lang="ts">
  // Fläche für zusammengehörigen Inhalt. Kopf optional: titel, zusatz
  // (kleiner Text rechts, z. B. Zahl), aktionen (Snippet, rechts).
  // polster: 'normal' | 'eng' | 'keins' (für Listen bis an den Rand).
  // ton: 'flaeche' (Standard) | 'vertieft' (Nebeninfo) | 'signal' (Hinweis).
  import type { Snippet } from 'svelte';
  import type { IconKomponente } from './icons';

  interface Props {
    titel?: string;
    zusatz?: string | number;
    icon?: IconKomponente;
    polster?: 'normal' | 'eng' | 'keins';
    ton?: 'flaeche' | 'vertieft' | 'signal';
    href?: string;
    aktionen?: Snippet;
    children: Snippet;
    class?: string;
  }

  let {
    titel,
    zusatz,
    icon: Icon,
    polster = 'normal',
    ton = 'flaeche',
    href,
    aktionen,
    children,
    class: klasse = '',
  }: Props = $props();
</script>

<svelte:element this={href ? 'a' : 'section'} {href} class="ui-karte p-{polster} {ton} {klasse}" class:link={!!href}>
  {#if titel || aktionen}
    <header class="kopf">
      {#if Icon}<span class="icon"><Icon size={16} strokeWidth={1.8} aria-hidden="true" /></span>{/if}
      {#if titel}<h3>{titel}</h3>{/if}
      {#if zusatz !== undefined}<span class="zusatz">{zusatz}</span>{/if}
      {#if aktionen}<div class="aktionen">{@render aktionen()}</div>{/if}
    </header>
  {/if}
  <div class="rumpf">{@render children()}</div>
</svelte:element>

<style>
  .ui-karte {
    --polster: var(--a-5);
    display: block;
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-l);
    box-shadow: var(--schatten-1);
    color: inherit;
    text-decoration: none;
    min-width: 0;
  }
  .p-eng { --polster: var(--a-4); }
  .p-keins { --polster: 0px; }
  .vertieft { background: var(--farbe-flaeche-hoch); box-shadow: none; }
  .signal {
    background: color-mix(in srgb, var(--farbe-signal-grund) 45%, var(--farbe-flaeche));
    border-color: color-mix(in srgb, var(--farbe-signal) 30%, var(--farbe-linie));
    box-shadow: inset 0 3px 0 var(--farbe-signal), var(--schatten-1);
  }
  .signal .kopf { border-bottom-color: color-mix(in srgb, var(--farbe-signal) 18%, var(--farbe-linie)); }
  .link { transition: border-color var(--t-kurz), transform var(--t-mittel) var(--kurve), box-shadow var(--t-mittel); }
  .link:hover { border-color: var(--farbe-linie-stark); box-shadow: var(--schatten-2); transform: translateY(-1px); }

  .kopf {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    min-height: 52px;
    padding: var(--a-3) var(--a-5);
    border-bottom: 1px solid var(--farbe-linie);
  }
  .p-eng .kopf { padding: var(--a-2) var(--a-4); min-height: 44px; }
  .icon { color: var(--farbe-text-2); display: inline-flex; }
  h3 { font-size: var(--text-m); font-weight: 650; font-stretch: 104%; letter-spacing: -0.005em; }
  .zusatz { font-family: var(--schrift-mono); font-size: var(--text-xs); color: var(--farbe-text-2); }
  .aktionen { margin-left: auto; display: flex; align-items: center; gap: var(--a-1); }
  .rumpf { padding: var(--polster); }
</style>
