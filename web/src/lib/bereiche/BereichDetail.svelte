<script lang="ts">
  // Bereichsansicht: Kopf, Reiter, bearbeitbare Abschnitte. Reiter „Übersicht“
  // und „Aufgaben“ gibt es immer, die übrigen nur wenn zum Bereich Daten
  // vorliegen (wie früher docs/js/themen.js:themaReiter, hier ohne Zuschnitt
  // — das ist kein Teil dieses Auftrags).
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import AufgabenListe from '../aufgaben/AufgabenListe.svelte';
  import Markdown from '../Markdown.svelte';
  import Abschnitt from './Abschnitt.svelte';
  import { fortschritt } from './sortierung';
  import { Etikett, FortschrittBalken, Karte, Kennzahl, Leerzustand, Tabs } from '../ui';

  let { name }: { name: string } = $props();

  const REIHENFOLGE_ABSCHNITTE = ['Beschreibung', 'Stand', 'Auslegung', 'Notizen', 'Links'];
  const STATUS_WORT: Record<string, string> = { 'in-arbeit': 'in Arbeit', geplant: 'geplant', fertig: 'fertig' };
  const STATUS_TON: Record<string, 'gut' | 'signal' | 'neutral'> = {
    fertig: 'gut',
    'in-arbeit': 'signal',
    geplant: 'neutral',
  };

  const euro = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
  function zahl(wert: string | undefined): number {
    const n = parseFloat((wert ?? '').replace(',', '.'));
    return Number.isFinite(n) ? n : 0;
  }

  const bereich = $derived(store.daten?.bereiche.find((b) => b.name === name));
  const aufgaben = $derived(store.daten?.aufgaben ?? []);
  const f = $derived(fortschritt(aufgaben, name));

  const teile = $derived((store.daten?.teile ?? []).filter((t) => t.kategorie === name));
  const entscheidungen = $derived((store.daten?.entscheidungen ?? []).filter((s) => s.bereich === name));
  const anleitungen = $derived((store.daten?.anleitungen ?? []).filter((s) => s.bereich === name));
  const recherche = $derived((store.daten?.recherche ?? []).filter((s) => s.bereich === name));
  const medien = $derived((store.daten?.medien ?? []).filter((m) => m.bereich === name));

  const kosten = $derived(teile.reduce((s, t) => s + zahl(t.preis), 0));
  const gewicht = $derived(teile.reduce((s, t) => s + zahl(t.gewicht_kg), 0));

  type ReiterId = 'uebersicht' | 'aufgaben' | 'teile' | 'entscheidungen' | 'anleitungen' | 'recherche' | 'medien';

  const reiter = $derived.by((): { id: ReiterId; wort: string; zahl: number }[] => {
    const r: { id: ReiterId; wort: string; zahl: number }[] = [
      { id: 'uebersicht', wort: 'Übersicht', zahl: 0 },
      { id: 'aufgaben', wort: 'Aufgaben', zahl: f.gesamt },
    ];
    if (teile.length) r.push({ id: 'teile', wort: 'Teile', zahl: teile.length });
    if (entscheidungen.length) r.push({ id: 'entscheidungen', wort: 'Entscheidungen', zahl: entscheidungen.length });
    if (anleitungen.length) r.push({ id: 'anleitungen', wort: 'Anleitungen', zahl: anleitungen.length });
    if (recherche.length) r.push({ id: 'recherche', wort: 'Recherche', zahl: recherche.length });
    if (medien.length) r.push({ id: 'medien', wort: 'Medien', zahl: medien.length });
    return r;
  });

  const reiterTabs = $derived(reiter.map((r) => ({ id: r.id, label: r.wort, zahl: r.zahl || undefined })));

  const aktiv = $derived.by((): ReiterId => {
    const gewuenscht = router.route.parameter[1];
    const treffer = reiter.find((r) => r.id === gewuenscht);
    return treffer ? treffer.id : 'uebersicht';
  });

  function reiterWaehlen(id: string): void {
    router.gehe('bereiche', name, id);
  }

  const matrix = $derived(store.daten?.bearbeitbar?.bereich_abschnitte ?? {});
  const abschnitteAnzeige = $derived(
    REIHENFOLGE_ABSCHNITTE.map((n) => ({
      name: n,
      text: bereich?.abschnitte?.[n]?.text ?? '',
      bearbeitbar: !!matrix[n]?.web,
    })),
  );
</script>

{#if !bereich}
  <Leerzustand titel="Bereich „{name}“ nicht gefunden" />
{:else}
  <div class="bereich-kopf">
    <div class="obenzeile">
      <h2 class="titel-gross">{bereich.name}</h2>
      {#if bereich.phase != null}<Etikett>Phase {bereich.phase}</Etikett>{/if}
      <Etikett ton={STATUS_TON[bereich.status] ?? 'neutral'}>{STATUS_WORT[bereich.status] ?? bereich.status}</Etikett>
    </div>
    {#if bereich.kurz}<p class="kurz">{bereich.kurz}</p>{/if}
    {#if f.gesamt}
      <FortschrittBalken wert={f.fertig / f.gesamt} />
    {/if}
    <div class="kennzahlen">
      <Kennzahl titel="Aufgaben" wert="{f.fertig}/{f.gesamt}" />
      {#if teile.length}
        <Kennzahl titel="Teilekosten" wert={euro.format(kosten)} />
        <Kennzahl titel="Gewicht" wert="{gewicht.toFixed(1)} kg" />
      {/if}
      {#if medien.length}
        <Kennzahl titel="Medien" wert={medien.length} />
      {/if}
    </div>
  </div>

  <Tabs tabs={reiterTabs} aktiv={aktiv} onwechsel={reiterWaehlen} label="Bereich-Reiter" />

  <div class="reiter-inhalt">
    {#if aktiv === 'uebersicht'}
      <Karte>
        {#each abschnitteAnzeige as a (a.name)}
          <Abschnitt bereich={name} name={a.name} text={a.text} bearbeitbar={a.bearbeitbar} />
        {/each}
      </Karte>
    {:else if aktiv === 'aufgaben'}
      <AufgabenListe bereich={name} />
    {:else if aktiv === 'teile'}
      <Karte polster="keins">
        <ul class="liste">
          {#each teile as t (t.id)}
            <li>
              <span class="titel">{t.titel}</span>
              <span class="zusatz">{t.status}{#if t.preis}&nbsp;·&nbsp;{euro.format(zahl(t.preis))}{/if}</span>
            </li>
          {/each}
        </ul>
      </Karte>
    {:else if aktiv === 'entscheidungen'}
      {#each entscheidungen as s (s.datei)}
        <Karte titel={s.titel}>
          {#snippet aktionen()}<Etikett>{s.status}</Etikett>{/snippet}
          <Markdown text={s.text} />
        </Karte>
      {/each}
    {:else if aktiv === 'anleitungen'}
      {#each anleitungen as s (s.datei)}
        <Karte titel={s.titel}>
          <Markdown text={s.text} />
        </Karte>
      {/each}
    {:else if aktiv === 'recherche'}
      {#each recherche as s (s.datei)}
        <Karte titel={s.titel}>
          <Markdown text={s.text} />
        </Karte>
      {/each}
    {:else if aktiv === 'medien'}
      <Karte polster="keins">
        <ul class="liste">
          {#each medien as m (m.datei)}
            <li><span class="titel">{m.name}</span><span class="zusatz">{m.art}</span></li>
          {/each}
        </ul>
      </Karte>
    {/if}
  </div>
{/if}

<style>
  .bereich-kopf {
    display: flex;
    flex-direction: column;
    gap: var(--a-3);
    margin-bottom: var(--a-5);
  }
  .obenzeile {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    flex-wrap: wrap;
  }
  .titel-gross {
    margin: 0;
    font-size: var(--text-xl);
    font-weight: 750;
    font-stretch: var(--breit);
  }
  .obenzeile :global(.ui-etikett:last-child) {
    margin-left: auto;
  }
  .kurz {
    margin: 0;
    color: var(--farbe-text-2);
    font-size: var(--text-m);
  }
  .kennzahlen {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-5);
    margin-top: var(--a-1);
  }
  .reiter-inhalt {
    margin-top: var(--a-4);
    display: flex;
    flex-direction: column;
    gap: var(--a-3);
  }

  .liste {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .liste li {
    display: flex;
    align-items: baseline;
    gap: var(--a-3);
    padding: var(--a-2) var(--a-4);
    border-bottom: 1px solid var(--farbe-linie);
  }
  .liste li:last-child {
    border-bottom: none;
  }
  .liste .titel {
    font-weight: 550;
  }
  .liste .zusatz {
    margin-left: auto;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    white-space: nowrap;
  }
</style>
