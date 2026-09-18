<script lang="ts">
  // Blendet Bearbeitungselemente im Lesemodus aus. Spätere Ansichten
  // wickeln jeden Knopf/jedes Eingabefeld einfach damit ein:
  //   <Schreibbar>{#snippet children()}<button>…</button>{/snippet}</Schreibbar>
  import type { Snippet } from 'svelte';
  import { store } from './daten.svelte';

  let { children }: { children: Snippet } = $props();
</script>

{#if store.darfSchreiben}
  {@render children()}
{/if}
