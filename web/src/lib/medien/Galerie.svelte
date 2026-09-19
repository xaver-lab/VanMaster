<script lang="ts">
  // Kachelraster für Medien. Bilder öffnen die Lupe, Unterlagen einen neuen
  // Tab. Mit `gruppieren` je Bereich eine Rubrik — die Lupe blättert trotzdem
  // durch alle gezeigten Bilder in Anzeigereihenfolge.
  import type { MediumAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { toasts } from '../toasts.svelte';
  import { Rubrik } from '../ui';
  import IconDatei from '@lucide/svelte/icons/file-text';
  import IconModell from '@lucide/svelte/icons/box';
  import IconKopieren from '@lucide/svelte/icons/copy';
  import Lupe from './Lupe.svelte';
  import { endung, istBild, medienUrl } from './url';

  // 3D-Modelle haben keine Web-Kopie (tools/media.py kopiert sie nicht) —
  // Pfad im Vault kommt über `m.datei` (Projektwurzel-relativ), eine
  // Dateigröße liefert /api/daten dafür bisher nicht (Medium hat kein
  // `groesse`-Feld, siehe tools/kern/modelle.py).
  async function pfadKopieren(pfad: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(pfad);
      toasts.info('Pfad kopiert.');
    } catch {
      toasts.fehler('Kopieren nicht möglich.');
    }
  }

  interface Props {
    medien: MediumAntwort[];
    gruppieren?: boolean;
  }

  let { medien, gruppieren = false }: Props = $props();

  // Bekannte Bereiche in der Reihenfolge der Daten, alles Übrige hinten.
  const gruppen = $derived.by(() => {
    if (!gruppieren) return [{ bereich: '', medien }];
    const reihe = (store.daten?.bereiche ?? []).map((b) => b.name);
    const vorhanden = [...new Set(medien.map((m) => m.bereich))];
    const bekannt = reihe.filter((n) => vorhanden.includes(n));
    const rest = vorhanden.filter((n) => !reihe.includes(n)).sort((a, b) => a.localeCompare(b, 'de'));
    return [...bekannt, ...rest].map((bereich) => ({ bereich, medien: medien.filter((m) => m.bereich === bereich) }));
  });

  const bilder = $derived(gruppen.flatMap((g) => g.medien.filter(istBild)));
  let lupeIndex = $state<number | null>(null);
</script>

{#snippet kachel(m: MediumAntwort)}
  {@const url = medienUrl(m)}
  {#if istBild(m) && url}
    <li>
      <button type="button" class="kachel bild" onclick={() => (lupeIndex = bilder.indexOf(m))} aria-label="{m.name} vergrößern">
        <img src={url} alt="" loading="lazy" />
        <span class="name">{m.name}</span>
      </button>
    </li>
  {:else if url}
    <li>
      <a class="kachel datei" href={url} target="_blank" rel="noopener" title="{m.dateiname} in neuem Tab öffnen">
        <IconDatei size={28} strokeWidth={1.5} aria-hidden="true" />
        <span class="art">{endung(m)}</span>
        <span class="name">{m.dateiname}</span>
      </a>
    </li>
  {:else}
    <li>
      <div class="kachel datei stumm" title="{m.datei} — nur im Vault">
        <IconModell size={28} strokeWidth={1.5} aria-hidden="true" />
        <span class="art">{endung(m)} · nur im Vault</span>
        <span class="name">{m.dateiname}</span>
        <span class="pfad">{m.datei}</span>
        <button type="button" class="kopieren" onclick={() => pfadKopieren(m.datei)}>
          <IconKopieren size={13} strokeWidth={1.8} aria-hidden="true" />
          Pfad kopieren
        </button>
      </div>
    </li>
  {/if}
{/snippet}

{#each gruppen as g (g.bereich)}
  <section class="gruppe">
    {#if gruppieren}<Rubrik titel={g.bereich || 'Unsortiert'} zahl={g.medien.length} />{/if}
    <ul class="galerie">
      {#each g.medien as m (m.datei)}
        {@render kachel(m)}
      {/each}
    </ul>
  </section>
{/each}

<Lupe {bilder} bind:index={lupeIndex} />

<style>
  .gruppe + .gruppe {
    margin-top: var(--a-6);
  }
  .galerie {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: var(--a-3);
  }
  .kachel {
    position: relative;
    display: flex;
    width: 100%;
    aspect-ratio: 4 / 3;
    padding: 0;
    overflow: hidden;
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-l);
    background: var(--farbe-flaeche);
    color: var(--farbe-text);
    text-decoration: none;
    font: inherit;
    transition: border-color var(--t-kurz), transform var(--t-kurz) var(--kurve);
  }
  .kachel:hover:not(.stumm) {
    border-color: var(--farbe-text-3);
  }
  .kachel:active:not(.stumm) {
    transform: translateY(1px);
  }
  .bild {
    cursor: zoom-in;
  }
  .bild img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform var(--t-mittel) var(--kurve);
  }
  .bild:hover img {
    transform: scale(1.04);
  }
  .bild .name {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    padding: var(--a-3) var(--a-2) var(--a-1);
    font-size: var(--text-xs);
    text-align: left;
    color: #fff;
    background: linear-gradient(transparent, rgb(0 0 0 / 0.72));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .datei {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--a-1);
    padding: var(--a-3);
    color: var(--farbe-text-2);
    background:
      repeating-linear-gradient(-45deg, transparent 0 5px, var(--farbe-raster) 5px 6px),
      var(--farbe-flaeche);
  }
  .datei .art {
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-signal);
    letter-spacing: 0.04em;
  }
  .datei .name {
    max-width: 100%;
    font-size: var(--text-s);
    font-weight: 550;
    color: var(--farbe-text);
    text-align: center;
    overflow-wrap: anywhere;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .stumm {
    aspect-ratio: auto;
    padding: var(--a-4) var(--a-3);
  }
  .stumm .art {
    color: var(--farbe-text-2);
  }
  .stumm .pfad {
    max-width: 100%;
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
    text-align: center;
    overflow-wrap: anywhere;
  }
  .stumm .kopieren {
    display: flex;
    align-items: center;
    gap: var(--a-1);
    margin-top: var(--a-1);
    padding: var(--a-1) var(--a-3);
    border: 1px solid var(--farbe-linie-stark);
    border-radius: var(--r-m);
    background: var(--farbe-flaeche);
    color: var(--farbe-text);
    font: inherit;
    font-size: var(--text-xs);
    cursor: pointer;
  }
  .stumm .kopieren:hover {
    background: var(--farbe-flaeche-hoch);
  }
</style>
