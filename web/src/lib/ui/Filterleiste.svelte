<script lang="ts">
  // Filterleiste: die Zeile über einer Liste — Reiter links, Werkzeuge
  // (Suche, Auswahlfelder, Anlegen-Knopf) rechts. Stand vorher vierfach fast
  // gleich in AufgabenListe, TeileListe, EinzelteilListe und MedienAnsicht.
  //
  // Ohne `reiter` läuft alles in einer Reihe und ein Knopf rutscht ans Ende
  // (so arbeitet die Zuschnittliste, die keine Status-Reiter hat).
  //
  // Ein Auswahlfeld, das schmal bleiben soll, bekommt `class="filter-wahl"`.
  // Vorher hatte jede Ansicht dafür einen eigenen Klassennamen in einer
  // unscoped :global()-Regel — die leckte in alle anderen Ansichten.
  import type { Snippet } from 'svelte';

  interface Props {
    /** Reiterzeile (meist `<Tabs>`), steht links. */
    reiter?: Snippet;
    /** Suche, Auswahlfelder, Knöpfe. */
    children: Snippet;
  }

  let { reiter, children }: Props = $props();
</script>

<div class="ui-filterleiste" class:mit-reiter={!!reiter}>
  {#if reiter}
    {@render reiter()}
    <div class="werkzeug">{@render children()}</div>
  {:else}
    {@render children()}
  {/if}
</div>

<style>
  .ui-filterleiste {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    margin-bottom: var(--a-5);
  }
  .ui-filterleiste.mit-reiter {
    justify-content: space-between;
    gap: var(--a-3);
  }

  .werkzeug {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    margin-left: auto;
  }

  /* Suchfeld breit, Auswahlfelder mit `filter-wahl` schmal. Beides sind
     `.ui-feld`, deshalb die zweite Regel danach. */
  .ui-filterleiste :global(.ui-feld) {
    width: 15rem;
  }
  .ui-filterleiste :global(.filter-wahl) {
    width: 11rem;
    flex: none;
  }

  /* Ohne Reiter gibt es kein `.werkzeug`, das den Knopf nach rechts schiebt. */
  .ui-filterleiste:not(.mit-reiter) :global(.ui-knopf) {
    margin-left: auto;
  }
</style>
