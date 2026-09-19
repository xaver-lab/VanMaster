<script lang="ts">
  // Medienseite: Art als Reiter, Bereich als Auswahl, Suche, Kennzahlen,
  // darunter die Galerie. Vorbild inhaltlich: docs/js/medien.js.
  import type { MediumAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { Auswahl, Feld, Filterleiste, Kennzahl, Leerzustand, Tabs } from '../ui';
  import { IconMedien, IconSuche } from '../ui/icons';
  import Galerie from './Galerie.svelte';
  import Lupe from './Lupe.svelte';
  import { istBild } from './url';

  const ART_WORT: Record<string, string> = { bild: 'Bilder', dokument: 'Unterlagen', modell: 'Modelle' };
  const ART_REIHE = ['bild', 'dokument', 'modell'];

  function gemerkt(schluessel: string): string {
    try {
      return localStorage.getItem(schluessel) ?? '';
    } catch {
      return '';
    }
  }
  function merken(schluessel: string, wert: string): void {
    try {
      localStorage.setItem(schluessel, wert);
    } catch {
      /* egal — nur Komfort */
    }
  }

  let filterArt = $state(gemerkt('medienArt'));
  let filterBereich = $state(gemerkt('medienBereich'));
  let suche = $state('');

  const alle = $derived(store.daten?.medien ?? []);

  // Direktsprung aus der Palette (#/medien/<id>): öffnet die Lupe unabhängig
  // vom aktuellen Filter, auf allen Bildern (nicht nur den gefilterten).
  const bilderAlle = $derived(alle.filter(istBild));
  let routeIndex = $state<number | null>(null);
  // Zuletzt aus der Adresse übernommener Parameter. Ohne ihn setzte der
  // Effekt den Index sofort wieder, den das Schließen der Lupe genullt hat —
  // über einen Direktlink geöffnet ließ sie sich dann nicht mehr schließen.
  // Der Effekt reagiert deshalb nur auf echte Adressänderungen.
  let letzterParam = '';
  $effect(() => {
    if (router.route.ansicht !== 'medien') return;
    // `param` kommt vom Router schon dekodiert — hier nicht noch einmal.
    const param = router.route.parameter[0] ?? '';
    if (param === letzterParam) return;
    const i = param ? bilderAlle.findIndex((m) => m.datei === param) : -1;
    // Bilder noch nicht geladen: später nochmal versuchen.
    if (param && i < 0 && !bilderAlle.length) return;
    letzterParam = param;
    routeIndex = i >= 0 ? i : null;
  });
  $effect(() => {
    // Lupe geschlossen (Esc/X/Klick daneben setzt routeIndex auf null) →
    // Adresse zurück auf die reine Medienseite.
    if (routeIndex === null && router.route.ansicht === 'medien' && router.route.parameter.length) {
      router.gehe('medien');
    }
  });

  const bereiche = $derived.by(() => {
    const reihe = (store.daten?.bereiche ?? []).map((b) => b.name);
    const vorhanden = [...new Set(alle.map((m) => m.bereich))];
    const rest = vorhanden.filter((n) => !reihe.includes(n)).sort((a, b) => a.localeCompare(b, 'de'));
    return [...reihe.filter((n) => vorhanden.includes(n)), ...rest];
  });

  // Gemerkter Filter, den es nicht mehr gibt, fällt still auf "alle" zurück.
  const bereichWirksam = $derived(bereiche.includes(filterBereich) ? filterBereich : '');
  const artenVorhanden = $derived(ART_REIHE.filter((a) => alle.some((m) => m.art === a)));
  const artWirksam = $derived(artenVorhanden.includes(filterArt) ? filterArt : '');

  const imBereich = $derived(alle.filter((m) => !bereichWirksam || m.bereich === bereichWirksam));
  const artTabs = $derived([
    { id: '', label: 'alles', zahl: imBereich.length },
    ...artenVorhanden.map((a) => ({ id: a, label: ART_WORT[a] ?? a, zahl: imBereich.filter((m) => m.art === a).length })),
  ]);

  const suchtext = $derived(suche.trim().toLowerCase());
  function passtSuche(m: MediumAntwort): boolean {
    return !suchtext || `${m.name} ${m.dateiname}`.toLowerCase().includes(suchtext);
  }

  const gefiltert = $derived(imBereich.filter((m) => (!artWirksam || m.art === artWirksam) && passtSuche(m)));
  const anzahlBilder = $derived(gefiltert.filter((m) => m.art === 'bild').length);

  function artWaehlen(a: string): void {
    filterArt = a;
    merken('medienArt', a);
  }
  function bereichWaehlen(b: string): void {
    filterBereich = b;
    merken('medienBereich', b);
  }
</script>

{#if !alle.length}
  <Leerzustand
    icon={IconMedien}
    titel="Noch nichts einsortiert"
    text="Dateien nach _input/ legen, dann „camper media“ ausführen."
  />
{:else}
  <div class="kennzahlen">
    <Kennzahl
      titel="Dateien"
      wert={gefiltert.length}
      zusatz={gefiltert.length !== alle.length ? `von ${alle.length}` : undefined}
    />
    <Kennzahl titel="Bilder" wert={anzahlBilder} />
    {#if gefiltert.length - anzahlBilder}
      <Kennzahl titel="Unterlagen" wert={gefiltert.length - anzahlBilder} />
    {/if}
  </div>

  <Filterleiste>
    {#snippet reiter()}
      <Tabs tabs={artTabs} aktiv={artWirksam} onwechsel={artWaehlen} label="Art" />
    {/snippet}
      <Feld
        bind:wert={suche}
        placeholder="Suche im Namen…"
        aria-label="Medien durchsuchen"
        icon={IconSuche}
        type="search"
        klein
      />
      <Auswahl
        class="filter-wahl"
        wert={bereichWirksam}
        optionen={bereiche.map((b) => ({ wert: b, label: b || 'Unsortiert' }))}
        leer="alle Bereiche"
        onchange={(e) => bereichWaehlen((e.target as HTMLSelectElement).value)}
      aria-label="Bereich filtern"
      klein
    />
  </Filterleiste>

  {#if !gefiltert.length}
    <Leerzustand titel="Nichts passt zum Filter" text="Filter lockern oder die Suche anpassen." />
  {:else}
    <Galerie medien={gefiltert} gruppieren={!bereichWirksam} />
  {/if}
{/if}

<Lupe bilder={bilderAlle} bind:index={routeIndex} />

<style>
  .kennzahlen {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-5);
    margin-bottom: var(--a-5);
  }
</style>
