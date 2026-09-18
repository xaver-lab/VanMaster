<script lang="ts">
  // Abschnittsüberschrift im Stil einer Maßlinie:  BAUABSCHNITTE ├──────┤ 07
  // Gliedert eine Seite ohne zusätzliche Kästen.
  import type { Snippet } from 'svelte';

  interface Props {
    titel: string;
    zahl?: string | number;
    aktionen?: Snippet;
    id?: string;
  }

  let { titel, zahl, aktionen, id }: Props = $props();
</script>

<div class="ui-rubrik">
  <h2 {id}>{titel}</h2>
  <span class="linie" aria-hidden="true"></span>
  {#if zahl !== undefined}<span class="zahl">{zahl}</span>{/if}
  {#if aktionen}<div class="aktionen">{@render aktionen()}</div>{/if}
</div>

<style>
  .ui-rubrik {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    margin: 0 0 var(--a-4);
    min-height: 28px;
  }
  h2 {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text);
    white-space: nowrap;
  }
  .linie {
    flex: 1;
    height: 9px;
    border-left: 1px solid var(--farbe-linie-stark);
    border-right: 1px solid var(--farbe-linie-stark);
    background: linear-gradient(var(--farbe-linie-stark), var(--farbe-linie-stark)) center / 100% 1px no-repeat;
    min-width: 24px;
  }
  .zahl { font-family: var(--schrift-mono); font-size: var(--text-xs); color: var(--farbe-text-2); }
  .aktionen { display: flex; gap: var(--a-1); }
</style>
