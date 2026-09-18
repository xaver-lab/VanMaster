<script lang="ts">
  // Kontrollkästchen mit Haken-Animation. Ohne `label` braucht es `titel`
  // (Vorlesetext). `gemischt` = teilweise (z. B. Gruppe halb erledigt).
  import type { Snippet } from 'svelte';

  interface Props {
    checked?: boolean;
    gemischt?: boolean;
    label?: string;
    titel?: string;
    disabled?: boolean;
    durchstreichen?: boolean;
    onchange?: (checked: boolean) => void;
    children?: Snippet;
  }

  let {
    checked = $bindable(false),
    gemischt = false,
    label,
    titel,
    disabled = false,
    durchstreichen = false,
    onchange,
    children,
  }: Props = $props();
</script>

<label class="ui-kasten" class:gesperrt={disabled} class:durch={durchstreichen && checked} title={titel}>
  <input
    type="checkbox"
    bind:checked
    indeterminate={gemischt && !checked}
    {disabled}
    aria-label={!label && !children ? titel : undefined}
    onchange={() => onchange?.(checked)}
  />
  <span class="box" aria-hidden="true">
    <svg viewBox="0 0 16 16" width="16" height="16">
      {#if gemischt && !checked}
        <path class="strich" d="M4.5 8h7" />
      {:else}
        <path class="haken" d="M3.8 8.3 6.7 11.1 12.3 5.2" />
      {/if}
    </svg>
  </span>
  {#if children}<span class="text">{@render children()}</span>{:else if label}<span class="text">{label}</span>{/if}
</label>

<style>
  .ui-kasten {
    display: inline-flex;
    align-items: flex-start;
    gap: 10px;
    cursor: pointer;
    position: relative;
    line-height: 1.4;
    -webkit-user-select: none;
    user-select: none;
  }
  .gesperrt { cursor: not-allowed; opacity: 0.55; }
  input { position: absolute; opacity: 0; width: 18px; height: 18px; margin: 0; cursor: inherit; }
  .box {
    flex: none;
    width: 18px;
    height: 18px;
    margin-top: 1px;
    display: grid;
    place-items: center;
    border: 1.5px solid var(--farbe-linie-stark);
    border-radius: 4px;
    background: var(--farbe-flaeche);
    transition: background-color var(--t-kurz), border-color var(--t-kurz), transform var(--t-kurz) var(--kurve-feder);
  }
  .ui-kasten:hover .box { border-color: var(--farbe-text-2); }
  input:focus-visible + .box { outline: 2px solid var(--farbe-fokus); outline-offset: 2px; }
  svg { fill: none; stroke: var(--farbe-flaeche); stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
  .haken { stroke-dasharray: 14; stroke-dashoffset: 14; transition: stroke-dashoffset var(--t-mittel) var(--kurve); }
  input:checked + .box { background: var(--farbe-gut); border-color: var(--farbe-gut); transform: scale(1.04); }
  input:checked + .box .haken { stroke-dashoffset: 0; transition-delay: 40ms; }
  input:indeterminate + .box { background: var(--farbe-text-2); border-color: var(--farbe-text-2); }
  .ui-kasten:active .box { transform: scale(0.9); }
  .text { min-width: 0; }
  .durch .text { text-decoration: line-through; text-decoration-color: var(--farbe-text-3); color: var(--farbe-text-2); }
</style>
