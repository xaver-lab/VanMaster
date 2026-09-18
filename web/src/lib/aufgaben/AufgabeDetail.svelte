<script lang="ts">
  import { untrack } from 'svelte';
  // Detailfenster einer Aufgabe, als Dialog. Route macht sie verlinkbar
  // (#/aufgaben/<id>) — AufgabenListe hält Route und offene Aufgabe
  // synchron, wenn sie die Top-Ansicht ist.
  import type { AufgabeAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import Markdown from '../Markdown.svelte';
  import {
    Auswahl,
    bestaetigen,
    Chip,
    Dialog,
    Etikett,
    IconKnopf,
    Knopf,
    Rubrik,
    Statusmarke,
    STATUS_TEXT,
    Textfeld,
    type Status,
  } from '../ui';
  import { IconHaken, IconLoeschen, IconStift } from '../ui/icons';

  const ALLE_STATUS: Status[] = ['offen', 'laeuft', 'blockiert', 'erledigt', 'verworfen'];
  const STATUS_OPTIONEN = ALLE_STATUS.map((s) => ({ wert: s, label: STATUS_TEXT[s] }));

  let {
    a,
    nachId,
    onClose,
    onOeffnen,
  }: {
    a: AufgabeAntwort;
    nachId: Map<string, AufgabeAntwort>;
    onClose: () => void;
    onOeffnen: (id: string) => void;
  } = $props();

  let offen = $state(true);
  $effect(() => {
    if (!offen) onClose();
  });

  let titelBearbeiten = $state(false);
  let titelEntwurf = $state(untrack(() => a.titel));
  let beschreibungBearbeiten = $state(false);
  let beschreibungEntwurf = $state(untrack(() => a.beschreibung ?? ''));

  // Entwürfe zurücksetzen, wenn eine andere/aktualisierte Aufgabe kommt,
  // solange gerade nicht bearbeitet wird (kein Datenverlust durch SSE-Reload).
  $effect(() => {
    if (!titelBearbeiten) titelEntwurf = a.titel;
    if (!beschreibungBearbeiten) beschreibungEntwurf = a.beschreibung ?? '';
  });

  let kinder = $derived((a.kinder ?? []).map((id) => nachId.get(id)).filter((x): x is AufgabeAntwort => !!x));
  let braucht = $derived((a.braucht ?? []).map((id) => nachId.get(id)).filter((x): x is AufgabeAntwort => !!x));

  async function statusSetzen(e: Event): Promise<void> {
    const status = (e.target as HTMLSelectElement).value;
    if (!status || status === a.status) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status });
  }

  function titelBearbeitenStarten(): void {
    titelEntwurf = a.titel;
    titelBearbeiten = true;
  }

  async function titelSpeichern(): Promise<void> {
    const wert = titelEntwurf.trim();
    if (!wert || wert === a.titel) {
      titelBearbeiten = false;
      titelEntwurf = a.titel;
      return;
    }
    const ok = await store.aufgabePatch(a.id, a.datei ?? '', { titel: wert });
    if (ok) titelBearbeiten = false;
  }

  function titelTastatur(e: KeyboardEvent): void {
    if (e.key === 'Enter') {
      e.preventDefault();
      void titelSpeichern();
    } else if (e.key === 'Escape') {
      e.stopPropagation();
      titelBearbeiten = false;
      titelEntwurf = a.titel;
    }
  }

  async function beschreibungSpeichern(): Promise<void> {
    const ok = await store.aufgabePatch(a.id, a.datei ?? '', { beschreibung: beschreibungEntwurf });
    if (ok) beschreibungBearbeiten = false;
  }

  function beschreibungAbbrechen(): void {
    beschreibungEntwurf = a.beschreibung ?? '';
    beschreibungBearbeiten = false;
  }

  function beschreibungTastatur(e: KeyboardEvent): void {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void beschreibungSpeichern();
    } else if (e.key === 'Escape') {
      e.stopPropagation();
      beschreibungAbbrechen();
    }
  }

  async function loeschen(): Promise<void> {
    const ok = await store.aufgabeLoeschen(a.id, a.datei ?? '');
    if (ok) onClose();
  }

  async function loeschenMitBestaetigung(): Promise<void> {
    const ja = await bestaetigen({
      titel: `Aufgabe „${a.titel}“ löschen?`,
      text: kinder.length
        ? `${kinder.length} Unterpunkt${kinder.length === 1 ? '' : 'e'} werden mitgelöscht. Das lässt sich nur über Git zurückholen.`
        : 'Das lässt sich nur über Git zurückholen.',
      ja: 'Löschen',
      gefaehrlich: true,
    });
    if (ja) await loeschen();
  }

  function beiThemaKlick(): void {
    onClose();
    router.gehe('bereiche', a.bereich);
  }
</script>

<Dialog bind:offen titel={a.titel} breite="l">
  <div class="tm-kopf">
    {#if store.darfSchreiben}
      <Schreibbar>
        {#snippet children()}
          <Auswahl
            class="status-wahl"
            wert={a.status}
            optionen={STATUS_OPTIONEN}
            onchange={statusSetzen}
            aria-label="Status ändern"
          />
        {/snippet}
      </Schreibbar>
    {:else}
      <Statusmarke status={a.status} />
    {/if}
    {#if a.prio && a.prio !== 'mittel'}
      <Etikett ton={a.prio === 'kritisch' ? 'warn' : 'signal'}>{a.prio}</Etikett>
    {/if}
    {#if a.dauer}<Etikett>{a.dauer}</Etikett>{/if}
    <Chip onclick={beiThemaKlick}>{a.bereich}</Chip>
    <div class="tm-kopf-luecke">
      <Schreibbar>
        {#snippet children()}
          <IconKnopf icon={IconStift} label="Titel bearbeiten" groesse="s" onclick={titelBearbeitenStarten} />
        {/snippet}
      </Schreibbar>
    </div>
  </div>

  {#if titelBearbeiten}
    <Schreibbar>
      {#snippet children()}
        <!-- svelte-ignore a11y_autofocus -->
        <input
          class="tm-titel-eingabe"
          bind:value={titelEntwurf}
          onkeydown={titelTastatur}
          onblur={titelSpeichern}
          disabled={store.beschaeftigt}
          autofocus
          aria-label="Titel"
        />
      {/snippet}
    </Schreibbar>
  {/if}

  {#if braucht.length}
    <div>
      <Rubrik titel="Braucht" zahl={braucht.length} />
      <div class="tm-themen">
        {#each braucht as b (b.id)}
          {@const fertig = b.status === 'erledigt' || b.status === 'verworfen'}
          <Chip icon={fertig ? IconHaken : undefined} onclick={() => onOeffnen(b.id)}>{b.titel}</Chip>
        {/each}
      </div>
    </div>
  {/if}

  {#if kinder.length}
    <div>
      <Rubrik titel="Unterpunkte" zahl={kinder.length} />
      <ul class="unterpunkte">
        {#each kinder as k (k.id)}
          <li>
            <button type="button" class="unterpunkt" onclick={() => onOeffnen(k.id)}>
              <Statusmarke status={k.status} kompakt />
              {k.titel}
            </button>
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  <div>
    <Rubrik titel="Wie wird das gemacht" />
    {#if beschreibungBearbeiten}
      <Textfeld
        bind:wert={beschreibungEntwurf}
        zeilen={6}
        onkeydown={beschreibungTastatur}
        disabled={store.beschaeftigt}
        placeholder="Noch keine Beschreibung — wie wird diese Aufgabe angegangen?"
      />
      <div class="tm-notiz-leiste">
        <Knopf groesse="s" onclick={beschreibungSpeichern} disabled={store.beschaeftigt}>Speichern</Knopf>
        <Knopf variante="leise" groesse="s" onclick={beschreibungAbbrechen}>Abbrechen</Knopf>
        <span class="zusatz">Strg+Enter speichert</span>
      </div>
    {:else if a.beschreibung}
      <Markdown text={a.beschreibung} />
      <Schreibbar>
        {#snippet children()}
          <div class="tm-notiz-leiste">
            <Knopf variante="leise" groesse="s" icon={IconStift} onclick={() => (beschreibungBearbeiten = true)}>
              Bearbeiten
            </Knopf>
          </div>
        {/snippet}
      </Schreibbar>
    {:else}
      <p class="zusatz">Noch keine Beschreibung.</p>
      <Schreibbar>
        {#snippet children()}
          <div class="tm-notiz-leiste">
            <Knopf variante="leise" groesse="s" icon={IconStift} onclick={() => (beschreibungBearbeiten = true)}>
              Beschreibung hinzufügen
            </Knopf>
          </div>
        {/snippet}
      </Schreibbar>
    {/if}
  </div>

  {#snippet fuss()}
    <Schreibbar>
      {#snippet children()}
        <Knopf variante="gefaehrlich" icon={IconLoeschen} onclick={loeschenMitBestaetigung}>Löschen …</Knopf>
      {/snippet}
    </Schreibbar>
  {/snippet}
</Dialog>

<style>
  .tm-kopf {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
  }
  .tm-kopf :global(.status-wahl) {
    width: 148px;
    flex: none;
  }
  .tm-kopf-luecke { margin-left: auto; }

  .tm-titel-eingabe {
    display: block;
    width: 100%;
    font: inherit;
    font-size: var(--text-l);
    font-weight: 650;
    color: var(--farbe-text);
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-signal);
    border-radius: var(--r-m);
    padding: var(--a-2) var(--a-3);
  }

  .tm-themen {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-2);
  }

  .unterpunkte {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .unterpunkt {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    width: 100%;
    background: none;
    border: 0;
    color: var(--farbe-text);
    font: inherit;
    text-align: left;
    padding: var(--a-1) var(--a-2);
    border-radius: var(--r-s);
  }
  .unterpunkt:hover { background: var(--farbe-flaeche-hoch); }

  .tm-notiz-leiste {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    margin-top: var(--a-2);
  }
  .zusatz { color: var(--farbe-text-2); font-size: var(--text-s); }
</style>
