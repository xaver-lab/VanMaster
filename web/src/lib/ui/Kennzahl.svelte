<script lang="ts">
  // Kennzahl: Kachel aus Beschriftung und Wert, für Kopfzeilen und Übersichten.
  // ton färbt den Wert wie bei Etikett. href/onclick machen die Kachel klickbar.
  import type { IconKomponente } from './icons';

  interface Props {
    titel: string;
    wert: string | number;
    zusatz?: string;
    icon?: IconKomponente;
    ton?: 'neutral' | 'signal' | 'gut' | 'info' | 'warn';
    href?: string;
    onclick?: (e: MouseEvent) => void;
  }

  let { titel, wert, zusatz, icon: Icon, ton = 'neutral', href, onclick }: Props = $props();

</script>

{#snippet inhalt()}
  <div class="kopf">
    {#if Icon}<Icon size={13} strokeWidth={2} aria-hidden="true" />{/if}
    <span class="titel">{titel}</span>
  </div>
  <div class="wert">{wert}</div>
  {#if zusatz}<div class="zusatz">{zusatz}</div>{/if}
{/snippet}

{#if href}
  <a {href} class="ui-kennzahl {ton} klickbar" {onclick}>{@render inhalt()}</a>
{:else if onclick}
  <button type="button" class="ui-kennzahl {ton} klickbar" {onclick}>{@render inhalt()}</button>
{:else}
  <div class="ui-kennzahl {ton}">{@render inhalt()}</div>
{/if}

<style>
  .ui-kennzahl {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    background: none;
    border: none;
    padding: 0;
    text-align: left;
    text-decoration: none;
    color: inherit;
    font: inherit;
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-stretch: var(--schmal);
  }
  .wert {
    font-family: var(--schrift-mono);
    font-size: var(--text-l);
    font-weight: 650;
    color: var(--farbe-text);
  }
  .signal .wert { color: var(--farbe-signal); }
  .gut .wert { color: var(--farbe-gut); }
  .info .wert { color: var(--farbe-info); }
  .warn .wert { color: var(--farbe-warn); }
  .zusatz {
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
  }
  .klickbar {
    cursor: pointer;
    transition: transform var(--t-kurz) var(--kurve), opacity var(--t-kurz);
  }
  .klickbar:hover { opacity: 0.8; }
  .klickbar:active { transform: translateY(1px); }
</style>
