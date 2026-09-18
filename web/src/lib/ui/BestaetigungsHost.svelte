<script lang="ts">
  // Zeigt die Frage aus bestaetigen(). Einmal in App.svelte eingebunden.
  import { bestaetigung } from './bestaetigen.svelte';
  import Dialog from './Dialog.svelte';
  import Knopf from './Knopf.svelte';

  let frage = $derived(bestaetigung.aktuell);
  let offen = $state(false);
  let antwort = false;

  $effect(() => {
    if (frage) {
      antwort = false;
      offen = true;
    }
  });
</script>

{#if frage}
  <Dialog
    bind:offen
    titel={frage.titel}
    breite="s"
    onschliessen={() => frage?.antworten(antwort)}
  >
    {#if frage.text}<p class="text">{frage.text}</p>{/if}
    {#snippet fuss()}
      <Knopf variante="leise" data-fokus={frage?.gefaehrlich ? '' : undefined} onclick={() => { antwort = false; offen = false; }}>{frage?.nein ?? 'Abbrechen'}</Knopf>
      <Knopf
        variante={frage?.gefaehrlich ? 'gefaehrlich' : 'primaer'}
        onclick={() => { antwort = true; offen = false; }}
      >
        {frage?.ja ?? 'Bestätigen'}
      </Knopf>
    {/snippet}
  </Dialog>
{/if}

<style>
  .text { color: var(--farbe-text-2); }
</style>
