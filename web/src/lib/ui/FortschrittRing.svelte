<script lang="ts">
  // Fortschrittsring. wert/zusatz 0..1 (zusatz = z. B. "läuft", schraffiert
  // direkt hinter dem Wert). Mitte: children, sonst Prozent.
  import type { Snippet } from 'svelte';

  interface Props {
    wert: number;
    zusatz?: number;
    groesse?: number;
    dicke?: number;
    ton?: 'gut' | 'signal' | 'info' | 'tinte';
    label?: string;
    children?: Snippet;
  }

  let { wert, zusatz = 0, groesse = 44, dicke = 4, ton = 'gut', label, children }: Props = $props();

  const begrenzen = (x: number) => Math.max(0, Math.min(1, Number.isFinite(x) ? x : 0));
  let r = $derived((groesse - dicke) / 2);
  let umfang = $derived(2 * Math.PI * r);
  let w = $derived(begrenzen(wert));
  let z = $derived(begrenzen(Math.min(zusatz, 1 - w)));
</script>

<div
  class="ui-ring {ton}"
  style:width="{groesse}px"
  style:height="{groesse}px"
  role="progressbar"
  aria-valuemin={0}
  aria-valuemax={100}
  aria-valuenow={Math.round(w * 100)}
  aria-label={label}
>
  <svg viewBox="0 0 {groesse} {groesse}" width={groesse} height={groesse}>
    <circle class="spur" cx={groesse / 2} cy={groesse / 2} {r} stroke-width={dicke} />
    {#if z > 0}
      <circle
        class="zusatz"
        cx={groesse / 2}
        cy={groesse / 2}
        {r}
        stroke-width={dicke}
        stroke-dasharray="{z * umfang} {umfang}"
        stroke-dashoffset={-w * umfang}
      />
    {/if}
    <circle
      class="wert"
      cx={groesse / 2}
      cy={groesse / 2}
      {r}
      stroke-width={dicke}
      stroke-dasharray="{w * umfang} {umfang}"
    />
  </svg>
  <div class="mitte">
    {#if children}{@render children()}{:else}<span class="prozent">{Math.round(w * 100)}</span>{/if}
  </div>
</div>

<style>
  .ui-ring { position: relative; display: inline-grid; place-items: center; flex: none; }
  svg { position: absolute; inset: 0; transform: rotate(-90deg); }
  circle { fill: none; }
  .spur { stroke: var(--farbe-flaeche-hoch); }
  .wert { stroke: var(--c); stroke-linecap: butt; transition: stroke-dasharray var(--t-lang) var(--kurve); }
  .zusatz { stroke: var(--farbe-signal); opacity: 0.45; transition: stroke-dasharray var(--t-lang) var(--kurve); }
  .gut { --c: var(--farbe-gut); }
  .signal { --c: var(--farbe-signal); }
  .info { --c: var(--farbe-info); }
  .tinte { --c: var(--farbe-text); }
  .mitte { position: relative; font-family: var(--schrift-mono); font-size: 0.7rem; font-weight: 600; line-height: 1; }
  .prozent { font-variant-numeric: tabular-nums; }
</style>
