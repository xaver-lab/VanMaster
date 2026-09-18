<script lang="ts">
  // Detailfenster einer Aufgabe (Modal). Route macht sie verlinkbar
  // (#/aufgaben/<id>) — AufgabenListe hält Route und offene Aufgabe
  // synchron, wenn sie die Top-Ansicht ist.
  import type { AufgabeAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import Markdown from '../Markdown.svelte';

  const STATUS_WORT: Record<string, string> = {
    offen: 'offen',
    laeuft: 'läuft',
    blockiert: 'blockiert',
    erledigt: 'erledigt',
    verworfen: 'verworfen',
  };
  const ALLE_STATUS = ['offen', 'laeuft', 'blockiert', 'erledigt', 'verworfen'];

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

  let menueOffen = $state(false);
  let titelBearbeiten = $state(false);
  let titelEntwurf = $state(a.titel);
  let beschreibungBearbeiten = $state(false);
  let beschreibungEntwurf = $state(a.beschreibung ?? '');
  let loeschenBestaetigen = $state(false);

  // Entwürfe zurücksetzen, wenn eine andere/aktualisierte Aufgabe kommt,
  // solange gerade nicht bearbeitet wird (kein Datenverlust durch SSE-Reload).
  $effect(() => {
    if (!titelBearbeiten) titelEntwurf = a.titel;
    if (!beschreibungBearbeiten) beschreibungEntwurf = a.beschreibung ?? '';
  });

  let kinder = $derived((a.kinder ?? []).map((id) => nachId.get(id)).filter((x): x is AufgabeAntwort => !!x));
  let braucht = $derived((a.braucht ?? []).map((id) => nachId.get(id)).filter((x): x is AufgabeAntwort => !!x));

  function keydown(e: KeyboardEvent): void {
    if (e.key === 'Escape') {
      if (loeschenBestaetigen) {
        loeschenBestaetigen = false;
        return;
      }
      onClose();
    }
  }

  async function statusSetzen(status: string): Promise<void> {
    menueOffen = false;
    if (status === a.status) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status });
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

  function beiThemaKlick(): void {
    onClose();
    router.gehe('bereiche', a.bereich);
  }
</script>

<svelte:window onkeydown={keydown} />

<div
  class="modal-hinter"
  role="button"
  tabindex="-1"
  onclick={onClose}
  onkeydown={(e) => e.key === 'Enter' && onClose()}
>
  <div class="modal" role="dialog" aria-modal="true" aria-label={a.titel} onclick={(e) => e.stopPropagation()}>
    <button type="button" class="modal-zu" onclick={onClose} title="Schließen (Esc)">✕</button>

    {#if titelBearbeiten}
      <Schreibbar>
        {#snippet children()}
          <input
            class="tm-titel-eingabe"
            bind:value={titelEntwurf}
            onkeydown={titelTastatur}
            onblur={titelSpeichern}
            disabled={store.beschaeftigt}
            autofocus
          />
        {/snippet}
      </Schreibbar>
    {:else}
      <div
        class="tm-titel"
        role="button"
        tabindex="0"
        onclick={() => store.darfSchreiben && (titelBearbeiten = true)}
        onkeydown={(e) => e.key === 'Enter' && store.darfSchreiben && (titelBearbeiten = true)}
        title={store.darfSchreiben ? 'Klicken zum Umbenennen' : ''}
      >
        {a.titel}
      </div>
    {/if}

    <div class="tm-kopf">
      <Schreibbar>
        {#snippet children()}
          <div class="wechsler">
            <button
              type="button"
              class="status {a.status}"
              onclick={(e) => {
                e.stopPropagation();
                menueOffen = !menueOffen;
              }}
            >
              {a.status === 'verworfen' ? 'verworfen' : STATUS_WORT[a.status] ?? a.status} ▾
            </button>
            {#if menueOffen}
              <div class="menue">
                {#each ALLE_STATUS as s (s)}
                  <button type="button" class:aktiv={a.status === s} onclick={() => statusSetzen(s)}>
                    {STATUS_WORT[s]}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/snippet}
      </Schreibbar>
      {#if !store.darfSchreiben}
        <span class="status {a.status}">
          {a.status === 'verworfen' ? 'verworfen' : STATUS_WORT[a.status] ?? a.status}
        </span>
      {/if}
      {#if a.prio && a.prio !== 'mittel'}<span class="aufgabe-marke {a.prio}">{a.prio}</span>{/if}
      {#if a.dauer}<span class="aufgabe-marke">{a.dauer}</span>{/if}
      <button type="button" class="chip" onclick={beiThemaKlick}>{a.bereich}</button>
    </div>

    {#if braucht.length}
      <div class="tm-abschnitt">
        <h4>Braucht</h4>
        <div class="tm-themen">
          {#each braucht as b (b.id)}
            <button
              type="button"
              class="chip"
              class:erledigt={b.status === 'erledigt' || b.status === 'verworfen'}
              onclick={() => onOeffnen(b.id)}
            >
              {b.titel}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    {#if kinder.length}
      <div class="tm-abschnitt">
        <h4>Unterpunkte</h4>
        <ul class="unterpunkte">
          {#each kinder as k (k.id)}
            <li>
              <button type="button" class="unterpunkt" onclick={() => onOeffnen(k.id)}>
                <span class="status-punkt {k.status}"></span>
                {k.titel}
              </button>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <div class="tm-abschnitt">
      <h4>Wie wird das gemacht</h4>
      {#if beschreibungBearbeiten}
        <textarea
          class="tm-notiz"
          rows="6"
          bind:value={beschreibungEntwurf}
          onkeydown={beschreibungTastatur}
          disabled={store.beschaeftigt}
          placeholder="Noch keine Beschreibung — wie wird diese Aufgabe angegangen?"
        ></textarea>
        <div class="tm-notiz-leiste">
          <button type="button" class="flachknopf" onclick={beschreibungSpeichern} disabled={store.beschaeftigt}>
            Speichern
          </button>
          <button type="button" class="flachknopf" onclick={beschreibungAbbrechen}>Abbrechen</button>
          <span class="zusatz">Strg+Enter speichert</span>
        </div>
      {:else if a.beschreibung}
        <Markdown text={a.beschreibung} />
        <Schreibbar>
          {#snippet children()}
            <div class="tm-notiz-leiste">
              <button type="button" class="flachknopf" onclick={() => (beschreibungBearbeiten = true)}>
                Bearbeiten
              </button>
            </div>
          {/snippet}
        </Schreibbar>
      {:else}
        <p class="zusatz">Noch keine Beschreibung.</p>
        <Schreibbar>
          {#snippet children()}
            <div class="tm-notiz-leiste">
              <button type="button" class="flachknopf" onclick={() => (beschreibungBearbeiten = true)}>
                Beschreibung hinzufügen
              </button>
            </div>
          {/snippet}
        </Schreibbar>
      {/if}
    </div>

    <Schreibbar>
      {#snippet children()}
        <div class="tm-fuss">
          {#if loeschenBestaetigen}
            <div class="bestaetigen">
              <span>
                Aufgabe „{a.titel}“ wirklich löschen?
                {#if kinder.length} {kinder.length} Unterpunkt{kinder.length === 1 ? '' : 'e'} werden mitgelöscht.{/if}
              </span>
              <button type="button" class="flachknopf warnung" onclick={loeschen} disabled={store.beschaeftigt}>
                Ja, löschen
              </button>
              <button type="button" class="flachknopf" onclick={() => (loeschenBestaetigen = false)}>Abbrechen</button>
            </div>
          {:else}
            <button type="button" class="flachknopf warnung" onclick={() => (loeschenBestaetigen = true)}>
              Löschen
            </button>
          {/if}
        </div>
      {/snippet}
    </Schreibbar>
  </div>
</div>

<style>
  .modal-hinter {
    position: fixed;
    inset: 0;
    z-index: 28;
    background: rgba(6, 8, 12, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .modal {
    position: relative;
    background: var(--flaeche-hoch);
    border: 1px solid var(--linie-hell);
    border-radius: var(--radius);
    box-shadow: var(--schatten);
    width: min(640px, 100%);
    max-height: min(85vh, 900px);
    overflow-y: auto;
    padding: 1.25rem 1.35rem;
  }
  .modal-zu {
    position: sticky;
    float: right;
    top: 0;
    right: 0;
    margin-left: 0.5rem;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    color: var(--gedaempft);
    width: 30px;
    height: 30px;
    border-radius: 50%;
    font-size: 0.9rem;
    z-index: 1;
  }
  .modal-zu:hover {
    color: var(--text);
    border-color: var(--akzent);
  }

  .tm-titel {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0 2.2rem 0.2rem 0;
  }
  .tm-kopf {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.7rem;
  }
  .tm-abschnitt {
    margin-bottom: 0.9rem;
  }
  .tm-abschnitt h4 {
    margin: 0 0 0.45rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--gedaempft);
  }

  .wechsler {
    position: relative;
  }
  .status {
    font-size: 0.7rem;
    padding: 0.05rem 0.5rem;
    border-radius: 99px;
    border: 1px solid var(--linie);
    white-space: nowrap;
    background: none;
    color: var(--gedaempft);
  }
  .status.offen {
    color: var(--gedaempft);
    border-color: var(--linie);
  }
  .status.laeuft {
    color: var(--akzent);
    border-color: transparent;
    background: var(--akzent-tief);
  }
  .status.blockiert {
    color: var(--warn);
    border-color: transparent;
    background: var(--warn-tief);
  }
  .status.erledigt {
    color: var(--gut);
    border-color: transparent;
    background: var(--gut-tief);
  }
  .status.verworfen {
    color: var(--gedaempft);
  }
  .wechsler > .status {
    min-height: 26px;
    cursor: pointer;
  }
  .wechsler > .status:hover {
    border-color: var(--akzent);
    color: var(--text);
  }
  .menue {
    position: absolute;
    left: 0;
    top: calc(100% + 4px);
    z-index: 12;
    min-width: 10rem;
    padding: 0.3rem;
    background: var(--flaeche-hoch);
    border: 1px solid var(--linie-hell);
    border-radius: var(--radius-klein);
    box-shadow: var(--schatten);
    display: flex;
    flex-direction: column;
    gap: 1px;
  }
  .menue button {
    text-align: left;
    background: none;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 0.55rem;
    font-size: 0.85rem;
    color: var(--text);
  }
  .menue button:hover {
    background: var(--flaeche);
  }
  .menue button.aktiv {
    color: var(--akzent);
  }

  .chip {
    min-height: 32px;
    padding: 0 0.7rem;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: 99px;
    color: var(--gedaempft);
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  .chip:hover {
    border-color: var(--linie-hell);
    color: var(--text);
  }

  .aufgabe-marke {
    font-size: 0.7rem;
    padding: 0.05rem 0.45rem;
    border-radius: 99px;
    border: 1px solid var(--linie);
    color: var(--gedaempft);
    white-space: nowrap;
  }
  .aufgabe-marke.kritisch {
    color: var(--warn);
    border-color: transparent;
    background: var(--warn-tief);
  }
  .aufgabe-marke.hoch {
    color: var(--akzent);
    border-color: transparent;
    background: var(--akzent-tief);
  }

  .tm-notiz {
    width: 100%;
    resize: vertical;
    font: inherit;
    color: var(--text);
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    padding: 0.55rem 0.65rem;
  }
  .tm-notiz:focus {
    outline: none;
    border-color: var(--akzent);
  }
  .tm-notiz:disabled {
    color: var(--gedaempft);
    resize: none;
  }
  .tm-notiz-leiste {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-top: 0.5rem;
  }
  .zusatz {
    color: var(--gedaempft);
    font-size: 0.78rem;
  }

  .tm-titel-eingabe {
    display: block;
    width: 100%;
    font-size: 1.15rem;
    font-weight: 650;
    margin: 0 2.2rem 0.2rem 0;
    background: var(--flaeche);
    border: 1px solid var(--akzent);
    border-radius: var(--radius-klein);
    padding: 0.3rem 0.5rem;
  }
  .tm-titel[role='button'] {
    cursor: text;
  }
  .tm-titel[role='button']:hover {
    text-decoration: underline dotted;
    text-underline-offset: 3px;
  }
  .tm-themen {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  .tm-themen .chip.erledigt {
    text-decoration: line-through;
    opacity: 0.6;
  }
  .unterpunkte {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .unterpunkt {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    color: var(--text);
    padding: 0.3rem 0.2rem;
    text-align: left;
    width: 100%;
    border-radius: var(--radius-klein);
  }
  .unterpunkt:hover {
    background: var(--flaeche);
  }
  .status-punkt {
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    flex: 0 0 auto;
    background: var(--linie-hell);
  }
  .status-punkt.laeuft {
    background: var(--akzent);
  }
  .status-punkt.blockiert {
    background: var(--warn);
  }
  .status-punkt.erledigt {
    background: var(--gut);
  }
  .tm-fuss {
    margin-top: 1rem;
    padding-top: 0.8rem;
    border-top: 1px solid var(--linie);
  }
  .flachknopf.warnung {
    color: var(--warn);
    border-color: transparent;
  }
  .flachknopf.warnung:hover {
    border-color: var(--warn);
  }
  .bestaetigen {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.88rem;
  }
</style>
