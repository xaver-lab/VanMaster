<script lang="ts">
  // Rendert Markdown-Text (Bereichs-/Aufgabenbeschreibungen). Querverweise
  // [[Ziel]] werden gegen Bereiche und Aufgaben aus dem Store aufgelöst —
  // Bereich → Hash-Link auf die Bereichsansicht, Aufgabe → Detail-Route;
  // nicht auflösbar → toter Verweis (sichtbar, aber ohne Link).
  import { md, type Aufloeser } from './markdown';
  import { store } from './daten.svelte';

  let { text }: { text: string | null | undefined } = $props();

  const aufloesen: Aufloeser = (ziel) => {
    const bereich = store.daten?.bereiche.find((b) => b.name === ziel);
    if (bereich) return { href: '#/bereiche/' + encodeURIComponent(bereich.name) };
    const aufgabe = store.daten?.aufgaben.find((a) => a.id === ziel || a.titel === ziel);
    if (aufgabe) return { href: '#/aufgaben/' + encodeURIComponent(aufgabe.id) };
    return null;
  };

  let html = $derived(md(text || '', aufloesen));
</script>

<div class="md">{@html html}</div>

<style>
  .md :global(p) {
    margin: 0 0 0.6em;
  }
  .md :global(p:last-child) {
    margin-bottom: 0;
  }
  .md :global(ul),
  .md :global(ol) {
    margin: 0 0 0.6em;
    padding-left: 1.3em;
  }
  .md :global(h1),
  .md :global(h2),
  .md :global(h3),
  .md :global(h4),
  .md :global(h5),
  .md :global(h6) {
    margin: 0.8em 0 0.3em;
  }
  .md :global(h1:first-child),
  .md :global(h2:first-child),
  .md :global(h3:first-child) {
    margin-top: 0;
  }
  .md :global(code) {
    background: var(--flaeche-hoch);
    padding: 0.05em 0.35em;
    border-radius: 5px;
    font-size: 0.9em;
  }
  .md :global(.wiki-link) {
    text-decoration: none;
    color: var(--wartet);
    border-bottom: 1px dashed color-mix(in srgb, var(--wartet) 50%, transparent);
  }
  .md :global(.wiki-link.tot) {
    color: var(--gedaempft);
    border-bottom-color: var(--linie-hell);
    cursor: help;
  }
  .md :global(.tabellenrand) {
    overflow-x: auto;
  }
  .md :global(table) {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9em;
  }
  .md :global(th),
  .md :global(td) {
    border: 1px solid var(--linie);
    padding: 0.3em 0.5em;
    text-align: left;
  }
</style>
