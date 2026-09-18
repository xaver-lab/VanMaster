<script lang="ts">
  // Lupe: großes Bild im Dialog. ←/→ blättern in der übergebenen Liste
  // (reihum), Esc schließt, Fokus kehrt zur Kachel zurück (macht der Dialog).
  import type { MediumAntwort } from '../api-typen';
  import { Dialog, IconKnopf, Kbd } from '../ui';
  import IconZurueck from '@lucide/svelte/icons/chevron-left';
  import IconWeiter from '@lucide/svelte/icons/chevron-right';
  import { medienUrl } from './url';

  interface Props {
    bilder: MediumAntwort[];
    index?: number | null;
  }

  let { bilder, index = $bindable(null) }: Props = $props();

  let offen = $state(false);
  $effect(() => {
    offen = index !== null && !!bilder[index];
  });

  const bild = $derived(index !== null ? bilder[index] : undefined);
  const url = $derived(bild ? medienUrl(bild) : null);
  const mehrere = $derived(bilder.length > 1);

  function blaettern(schritt: number): void {
    if (index === null || !bilder.length) return;
    index = (index + schritt + bilder.length) % bilder.length;
  }

  function taste(e: KeyboardEvent): void {
    if (!offen || !mehrere) return;
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      blaettern(-1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      blaettern(1);
    }
  }
</script>

<svelte:window onkeydown={taste} />

<Dialog
  bind:offen
  breite="l"
  titel={bild?.name ?? ''}
  beschreibung={bild ? `${bild.bereich} · ${bild.dateiname}` : undefined}
  onschliessen={() => (index = null)}
>
  {#if bild}
    <figure class="lupe">
      {#if url}
        <img src={url} alt={bild.name} />
      {/if}
    </figure>
  {/if}
  {#snippet fuss()}
    {#if mehrere}
      <span class="stand">
        <Kbd tasten="← →" />
        <span class="zahl">{(index ?? 0) + 1} / {bilder.length}</span>
      </span>
      <IconKnopf icon={IconZurueck} label="Vorheriges Bild (←)" variante="sekundaer" onclick={() => blaettern(-1)} />
      <IconKnopf icon={IconWeiter} label="Nächstes Bild (→)" variante="sekundaer" onclick={() => blaettern(1)} data-fokus />
    {/if}
  {/snippet}
</Dialog>

<style>
  .lupe {
    margin: 0;
    display: grid;
    place-items: center;
    background: var(--farbe-flaeche-tief);
    border-radius: var(--r-m);
    min-height: 240px;
  }
  .lupe img {
    display: block;
    max-width: 100%;
    max-height: calc(100vh - 260px);
    object-fit: contain;
  }
  .stand {
    display: flex;
    align-items: center;
    gap: var(--a-1);
    margin-right: auto;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
  }
  .zahl {
    margin-left: var(--a-2);
    font-family: var(--schrift-mono);
  }
</style>
