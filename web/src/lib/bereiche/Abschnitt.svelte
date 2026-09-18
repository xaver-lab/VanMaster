<script lang="ts">
  // Ein Abschnitt einer Bereichsdatei — bearbeitbar mit Text/Vorschau-
  // Umschalter, oder nur lesend sichtbar markiert ("pflegt Claude").
  //
  // Konfliktschutz: Der Entwurf wird nur aus der Prop übernommen, solange
  // nicht bearbeitet wird ($effect unten). Lädt der Store währenddessen neu
  // (SSE, externe Änderung), bleibt die Eingabe stehen; beim Speichern greift
  // dann der Konflikt-Toast im Store selbst (409 → Toast, Version übernommen,
  // Text im Feld bleibt erhalten und kann erneut gespeichert werden).
  import { store } from '../daten.svelte';
  import Markdown from '../Markdown.svelte';
  import Schreibbar from '../Schreibbar.svelte';

  let {
    bereich,
    name,
    text,
    bearbeitbar,
  }: {
    bereich: string;
    name: string;
    text: string;
    bearbeitbar: boolean;
  } = $props();

  let bearbeiten = $state(false);
  let entwurf = $state(text);
  let ansicht = $state<'text' | 'vorschau'>('text');

  $effect(() => {
    if (!bearbeiten) entwurf = text;
  });

  const geaendert = $derived(entwurf !== text);

  function starten(): void {
    entwurf = text;
    ansicht = 'text';
    bearbeiten = true;
  }

  function abbrechen(): void {
    if (geaendert && !confirm('Ungespeicherte Änderungen verwerfen?')) return;
    bearbeiten = false;
  }

  async function speichern(): Promise<void> {
    if (store.beschaeftigt || !geaendert) return;
    const ok = await store.abschnittSetzen(bereich, name, entwurf);
    if (ok) bearbeiten = false;
  }

  function tastatur(e: KeyboardEvent): void {
    if (e.key === 'Escape') {
      e.preventDefault();
      abbrechen();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void speichern();
    }
  }
</script>

<section class="abschnitt">
  <div class="abschnitt-kopf">
    <h3>{name}</h3>
    {#if !bearbeitbar}
      <span class="marke-lesend" title="Wird von Claude gepflegt — im Web nicht bearbeitbar.">
        pflegt Claude
      </span>
    {:else if !bearbeiten}
      <Schreibbar>
        {#snippet children()}
          <button type="button" class="knopf-klein" onclick={starten}>Bearbeiten</button>
        {/snippet}
      </Schreibbar>
    {/if}
  </div>

  {#if bearbeiten}
    <div class="editor">
      <div class="umschalter">
        <button type="button" class:aktiv={ansicht === 'text'} onclick={() => (ansicht = 'text')}>
          Text
        </button>
        <button type="button" class:aktiv={ansicht === 'vorschau'} onclick={() => (ansicht = 'vorschau')}>
          Vorschau
        </button>
      </div>
      {#if ansicht === 'text'}
        <!-- svelte-ignore a11y_autofocus -->
        <textarea
          bind:value={entwurf}
          onkeydown={tastatur}
          rows="8"
          autofocus
          placeholder="Markdown-Text …"
        ></textarea>
      {:else}
        <div class="vorschau-feld">
          {#if entwurf.trim()}
            <Markdown text={entwurf} />
          {:else}
            <p class="hinweis-leer">Kein Text.</p>
          {/if}
        </div>
      {/if}
      <div class="editor-leiste">
        <button type="button" class="knopf" onclick={speichern} disabled={store.beschaeftigt || !geaendert}>
          Speichern
        </button>
        <button type="button" class="knopf" onclick={abbrechen}>Abbrechen</button>
        <span class="hinweis">Strg+Enter speichert · Esc bricht ab</span>
      </div>
    </div>
  {:else if text.trim()}
    <Markdown {text} />
  {:else}
    <p class="hinweis-leer">Noch nichts eingetragen.</p>
  {/if}
</section>

<style>
  .abschnitt {
    padding: 0.9rem 0;
    border-bottom: 1px solid var(--linie);
  }
  .abschnitt:last-child {
    border-bottom: none;
  }
  .abschnitt-kopf {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
  }
  .abschnitt-kopf h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 650;
  }
  .abschnitt-kopf :global(button) {
    margin-left: auto;
  }
  .marke-lesend {
    margin-left: auto;
    font-size: 0.7rem;
    padding: 0.15rem 0.55rem;
    border-radius: 99px;
    background: var(--flaeche-hoch);
    color: var(--gedaempft);
    border: 1px solid var(--linie);
    white-space: nowrap;
  }
  .knopf-klein,
  .knopf {
    min-height: 32px;
    padding: 0 0.7rem;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    color: var(--gedaempft);
    font-size: 0.82rem;
  }
  .knopf-klein:hover,
  .knopf:hover {
    color: var(--text);
    border-color: var(--linie-hell);
  }
  .knopf:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .editor {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .umschalter {
    display: flex;
    gap: 0.3rem;
  }
  .umschalter button {
    min-height: 30px;
    padding: 0 0.7rem;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    color: var(--gedaempft);
    font-size: 0.82rem;
  }
  .umschalter button.aktiv {
    background: var(--akzent-tief);
    color: var(--text);
    border-color: var(--akzent);
  }
  textarea {
    width: 100%;
    min-height: 10rem;
    padding: 0.6rem 0.7rem;
    background: var(--flaeche);
    color: var(--text);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    font: inherit;
    font-size: 0.9rem;
    resize: vertical;
  }
  textarea:focus {
    outline: none;
    border-color: var(--akzent);
  }
  .vorschau-feld {
    min-height: 10rem;
    padding: 0.6rem 0.7rem;
    background: var(--flaeche-hoch);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
  }
  .editor-leiste {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .editor-leiste .knopf {
    margin-left: 0;
  }
  .hinweis {
    margin-left: auto;
    color: var(--gedaempft);
    font-size: 0.76rem;
  }
  .hinweis-leer {
    margin: 0;
    color: var(--gedaempft);
    font-size: 0.86rem;
  }
</style>
