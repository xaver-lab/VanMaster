<script lang="ts">
  // Fortschrittsbalken. wert 0..1, zusatz 0..1 (schraffiert, z. B. "läuft"
  // oder "bestellt, noch nicht geliefert"). Optional Beschriftung links und
  // Zahl rechts. `teilung` zeichnet Maßstriche (z. B. je Aufgabe einen).
  interface Props {
    wert: number;
    zusatz?: number;
    ton?: 'gut' | 'signal' | 'info' | 'tinte';
    hoehe?: number;
    teilung?: number;
    label?: string;
    zahl?: string;
  }

  let { wert, zusatz = 0, ton = 'gut', hoehe = 6, teilung = 0, label, zahl }: Props = $props();

  const begrenzen = (x: number) => Math.max(0, Math.min(1, Number.isFinite(x) ? x : 0));
  let w = $derived(begrenzen(wert));
  let z = $derived(begrenzen(Math.min(zusatz, 1 - w)));
</script>

<div class="ui-balken {ton}" class:mit-text={!!label || !!zahl}>
  {#if label}<span class="label">{label}</span>{/if}
  <div
    class="spur"
    style:height="{hoehe}px"
    role="progressbar"
    aria-valuemin={0}
    aria-valuemax={100}
    aria-valuenow={Math.round(w * 100)}
    aria-label={label}
  >
    <span class="wert" style:width="{w * 100}%"></span>
    {#if z > 0}<span class="zusatz" style:left="{w * 100}%" style:width="{z * 100}%"></span>{/if}
    {#if teilung > 1}
      <span class="teilung" style:background-size="{100 / teilung}% 100%"></span>
    {/if}
  </div>
  {#if zahl}<span class="zahl">{zahl}</span>{/if}
</div>

<style>
  .ui-balken { display: flex; align-items: center; gap: var(--a-3); min-width: 0; }
  .gut { --c: var(--farbe-gut); }
  .signal { --c: var(--farbe-signal); }
  .info { --c: var(--farbe-info); }
  .tinte { --c: var(--farbe-text); }
  .label { flex: 0 0 auto; font-size: var(--text-s); min-width: 0; }
  .spur {
    position: relative;
    flex: 1;
    min-width: 40px;
    background: var(--farbe-flaeche-hoch);
    box-shadow: inset 0 0 0 1px var(--farbe-linie);
    border-radius: 2px;
    overflow: hidden;
  }
  .wert, .zusatz, .teilung { position: absolute; top: 0; bottom: 0; }
  .wert { left: 0; background: var(--c); transition: width var(--t-lang) var(--kurve); }
  .zusatz {
    background: repeating-linear-gradient(-45deg, var(--farbe-signal) 0 2px, transparent 2px 5px);
    opacity: 0.75;
    transition: left var(--t-lang) var(--kurve), width var(--t-lang) var(--kurve);
  }
  .teilung {
    inset: 0;
    background-image: linear-gradient(to right, transparent calc(100% - 1px), var(--farbe-flaeche) calc(100% - 1px));
    background-repeat: repeat-x;
  }
  .zahl { flex: none; font-family: var(--schrift-mono); font-size: var(--text-xs); color: var(--farbe-text-2); font-variant-numeric: tabular-nums; }
</style>
