<script lang="ts">
  import { untrack } from 'svelte';
  // Detailfenster eines Teils, als Dialog. Bearbeitbare Felder kommen aus
  // der Matrix store.daten.bearbeitbar.teil_felder (FORMAT.md §8) — nicht aus
  // einer fest eingebauten Liste. Nicht bearbeitbare Felder stehen sichtbar
  // als "pflegt Claude" da (wie lib/bereiche/Abschnitt.svelte).
  import type { AufgabeAntwort, TeilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { Auswahl, bestaetigen, Chip, Dialog, Etikett, Feld, Knopf, Rubrik, Textfeld } from '../ui';
  import { IconLoeschen } from '../ui/icons';
  import { euro, gesamtpreis, zahl, TEIL_PRIO, TEIL_STATUS } from './format';

  let {
    t,
    onClose,
    loeschenErlaubt = true,
  }: {
    t: TeilAntwort;
    onClose: () => void;
    loeschenErlaubt?: boolean;
  } = $props();

  let offen = $state(true);
  $effect(() => {
    if (!offen) onClose();
  });

  const matrix = $derived(store.daten?.bearbeitbar?.teil_felder ?? {});
  function bearbeitbar(feld: string): boolean {
    return !!matrix[feld]?.web;
  }

  const aufgabe = $derived<AufgabeAntwort | undefined>(
    t.fuer_aufgabe ? store.daten?.aufgaben.find((a) => a.id === t.fuer_aufgabe) : undefined,
  );

  // Entwurf für die Notiz, damit ein SSE-Neuladen während der Eingabe nichts
  // überschreibt (wie in AufgabeDetail); gespeichert wird beim Verlassen.
  let notizEntwurf = $state(untrack(() => t.notiz));
  let notizFokus = $state(false);
  $effect(() => {
    if (!notizFokus) notizEntwurf = t.notiz;
  });

  async function feldSpeichern(feld: string, wert: string): Promise<void> {
    if (wert === (t as unknown as Record<string, string>)[feld]) return;
    await store.teilPatch(t.id, feld, wert);
  }

  async function notizSpeichern(): Promise<void> {
    notizFokus = false;
    if (notizEntwurf === t.notiz) return;
    await store.teilPatch(t.id, 'notiz', notizEntwurf);
  }

  async function statusSetzen(e: Event): Promise<void> {
    const wert = (e.target as HTMLSelectElement).value;
    if (!wert || wert === t.status) return;
    await store.teilPatch(t.id, 'status', wert);
  }
  async function prioritaetSetzen(e: Event): Promise<void> {
    const wert = (e.target as HTMLSelectElement).value;
    if (!wert || wert === t.prioritaet) return;
    await store.teilPatch(t.id, 'prioritaet', wert);
  }

  async function loeschen(): Promise<void> {
    const ok = await store.teilLoeschen(t.id);
    if (ok) onClose();
  }
  async function loeschenMitBestaetigung(): Promise<void> {
    const ja = await bestaetigen({
      titel: `Teil „${t.titel}“ löschen?`,
      text: 'Das lässt sich nur über Git zurückholen.',
      ja: 'Löschen',
      gefaehrlich: true,
    });
    if (ja) await loeschen();
  }

  function beiAufgabeKlick(): void {
    onClose();
    router.gehe('aufgaben', aufgabe!.id);
  }

  const pflegtFelder = $derived(
    (
      [
        ['Beschreibung', t.beschreibung],
        ['Einheit', t.einheit],
        ['Kennwerte', t.kennwerte],
        ['Gewicht', zahl(t.gewicht_kg) ? `${zahl(t.gewicht_kg).toFixed(1)} kg` : ''],
        ['Entscheidung', t.entscheidung],
      ] as [string, string][]
    ).filter(([, wert]) => !!wert),
  );
</script>

<Dialog bind:offen titel={t.titel} breite="l">
  <div class="tm-kopf">
    {#if store.darfSchreiben && bearbeitbar('status')}
      <Schreibbar>
        {#snippet children()}
          <Auswahl
            class="status-wahl"
            wert={t.status}
            optionen={TEIL_STATUS}
            onchange={statusSetzen}
            aria-label="Status ändern"
          />
        {/snippet}
      </Schreibbar>
    {:else}
      <Etikett>{t.status || '—'}</Etikett>
    {/if}
    <span class="preis">{euro.format(gesamtpreis(t))}</span>
    {#if t.kategorie}<Etikett>{t.kategorie}</Etikett>{/if}
    {#if aufgabe}<Chip onclick={beiAufgabeKlick}>{aufgabe.titel}</Chip>{/if}
  </div>

  <div class="tm-felder">
    {#if bearbeitbar('kategorie')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Kategorie" wert={t.kategorie} onblur={(e) => feldSpeichern('kategorie', (e.target as HTMLInputElement).value)} klein />
        {/snippet}
      </Schreibbar>
    {:else if t.kategorie}
      <div class="nur-lesen"><span class="label">Kategorie</span><span>{t.kategorie}</span></div>
    {/if}

    {#if bearbeitbar('prioritaet')}
      <Schreibbar>
        {#snippet children()}
          <Auswahl label="Priorität" wert={t.prioritaet} optionen={TEIL_PRIO} leer="— keine —" onchange={prioritaetSetzen} klein />
        {/snippet}
      </Schreibbar>
    {:else if t.prioritaet}
      <div class="nur-lesen"><span class="label">Priorität</span><span>{t.prioritaet}</span></div>
    {/if}

    {#if bearbeitbar('menge')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Menge" wert={t.menge} einheit={t.einheit} onblur={(e) => feldSpeichern('menge', (e.target as HTMLInputElement).value)} mono klein />
        {/snippet}
      </Schreibbar>
    {/if}

    {#if bearbeitbar('preis')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Preis / Stk" wert={t.preis} einheit="€" onblur={(e) => feldSpeichern('preis', (e.target as HTMLInputElement).value)} mono klein />
        {/snippet}
      </Schreibbar>
    {/if}

    {#if bearbeitbar('haendler')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Händler" wert={t.haendler} onblur={(e) => feldSpeichern('haendler', (e.target as HTMLInputElement).value)} klein />
        {/snippet}
      </Schreibbar>
    {/if}

    {#if bearbeitbar('link')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Link" type="url" wert={t.link} onblur={(e) => feldSpeichern('link', (e.target as HTMLInputElement).value)} klein />
        {/snippet}
      </Schreibbar>
    {/if}

    {#if bearbeitbar('gekauft_am')}
      <Schreibbar>
        {#snippet children()}
          <Feld label="Gekauft am" wert={t.gekauft_am} placeholder="JJJJ-MM-TT" onblur={(e) => feldSpeichern('gekauft_am', (e.target as HTMLInputElement).value)} klein />
        {/snippet}
      </Schreibbar>
    {/if}
  </div>

  {#if t.link && !store.darfSchreiben}
    <p><a href={t.link} target="_blank" rel="noopener">Zum Shop ↗</a></p>
  {/if}

  <div>
    <Rubrik titel="Notiz" />
    {#if bearbeitbar('notiz')}
      <Schreibbar>
        {#snippet children()}
          <Textfeld
            bind:wert={notizEntwurf}
            zeilen={4}
            onfocus={() => (notizFokus = true)}
            onblur={notizSpeichern}
            disabled={store.beschaeftigt}
            placeholder="Noch keine Notiz."
          />
        {/snippet}
      </Schreibbar>
    {:else if t.notiz}
      <p class="notiz-text">{t.notiz}</p>
    {:else}
      <p class="zusatz">Noch keine Notiz.</p>
    {/if}
  </div>

  {#if pflegtFelder.length}
    <div>
      <Rubrik titel="Weitere Angaben" />
      <Etikett>pflegt Claude</Etikett>
      <dl class="tm-nurlesen">
        {#each pflegtFelder as [k, wert] (k)}
          <div class="feld">
            <dt>{k}</dt>
            <dd>{wert}</dd>
          </div>
        {/each}
      </dl>
    </div>
  {/if}

  {#snippet fuss()}
    {#if loeschenErlaubt}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="gefaehrlich" icon={IconLoeschen} onclick={loeschenMitBestaetigung}>Löschen …</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  {/snippet}
</Dialog>

<style>
  .tm-kopf {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    margin-bottom: var(--a-3);
  }
  .tm-kopf :global(.status-wahl) {
    width: 148px;
    flex: none;
  }
  .preis {
    font-family: var(--schrift-mono);
    font-weight: 650;
    font-size: var(--text-l);
  }
  .tm-felder {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: var(--a-3);
    margin-bottom: var(--a-4);
  }
  .nur-lesen {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: var(--text-s);
  }
  .nur-lesen .label {
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
  }
  .notiz-text {
    margin: 0;
    white-space: pre-wrap;
  }
  .zusatz {
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    margin: 0;
  }
  .tm-nurlesen {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: var(--a-2) var(--a-4);
    margin: var(--a-2) 0 0;
  }
  .tm-nurlesen .feld {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .tm-nurlesen dt {
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
  }
  .tm-nurlesen dd {
    margin: 0;
    font-size: var(--text-s);
  }
</style>
