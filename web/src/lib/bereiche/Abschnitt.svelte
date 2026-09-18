<script lang="ts">
  import { untrack } from 'svelte';
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
  import { bestaetigen, Etikett, Knopf, Leerzustand, Tabs, Textfeld } from '../ui';
  import { IconStift } from '../ui/icons';
  import { neuereFassungUeberschreiben } from '../ueberschreiben';

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
  let entwurf = $state(untrack(() => text));
  let ansicht = $state<'text' | 'vorschau'>('text');

  $effect(() => {
    if (!bearbeiten) entwurf = text;
  });

  const geaendert = $derived(entwurf !== text);
  // Text beim Start der Bearbeitung — weicht `text` davon ab, hat ihn
  // jemand anderes geändert.
  let basis = $state('');
  const fremdGeaendert = $derived(bearbeiten && text !== basis);

  function starten(): void {
    entwurf = text;
    basis = text;
    ansicht = 'text';
    bearbeiten = true;
  }

  async function abbrechen(): Promise<void> {
    if (geaendert) {
      const ja = await bestaetigen({
        titel: 'Ungespeicherte Änderungen verwerfen?',
        ja: 'Verwerfen',
        gefaehrlich: true,
      });
      if (!ja) return;
    }
    bearbeiten = false;
  }

  async function speichern(): Promise<void> {
    if (store.beschaeftigt || !geaendert) return;
    if (fremdGeaendert && !(await neuereFassungUeberschreiben())) return;
    const ok = await store.abschnittSetzen(bereich, name, entwurf);
    if (ok) bearbeiten = false;
  }

  function tastatur(e: KeyboardEvent): void {
    if (e.key === 'Escape') {
      e.preventDefault();
      void abbrechen();
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
      <Etikett>pflegt Claude</Etikett>
    {:else if !bearbeiten}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="leise" groesse="s" icon={IconStift} onclick={starten}>Bearbeiten</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  </div>

  {#if bearbeiten}
    <div class="editor">
      <Tabs
        tabs={[
          { id: 'text', label: 'Text' },
          { id: 'vorschau', label: 'Vorschau' },
        ]}
        aktiv={ansicht}
        onwechsel={(id) => (ansicht = id === 'vorschau' ? 'vorschau' : 'text')}
        label="Ansicht"
      />
      {#if ansicht === 'text'}
        <Textfeld bind:wert={entwurf} onkeydown={tastatur} zeilen={8} placeholder="Markdown-Text …" autofocus />
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
        <Knopf groesse="s" onclick={speichern} disabled={store.beschaeftigt || !geaendert}>Speichern</Knopf>
        <Knopf variante="leise" groesse="s" onclick={abbrechen}>Abbrechen</Knopf>
        {#if fremdGeaendert}<Etikett ton="warn">inzwischen anderswo geändert</Etikett>{/if}
        <span class="hinweis">Strg+Enter speichert · Esc bricht ab</span>
      </div>
    </div>
  {:else if text.trim()}
    <Markdown {text} />
  {:else}
    <Leerzustand kompakt titel="Noch nichts eingetragen" />
  {/if}
</section>

<style>
  .abschnitt {
    padding: var(--a-4) 0;
    border-bottom: 1px solid var(--farbe-linie);
  }
  .abschnitt:last-child {
    border-bottom: none;
  }
  .abschnitt-kopf {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    margin-bottom: var(--a-2);
  }
  .abschnitt-kopf h3 {
    margin: 0;
    font-size: var(--text-m);
    font-weight: 650;
  }
  .abschnitt-kopf :global(button),
  .abschnitt-kopf :global(.ui-etikett) {
    margin-left: auto;
  }

  .editor {
    display: flex;
    flex-direction: column;
    gap: var(--a-3);
  }
  .vorschau-feld {
    min-height: 10rem;
    padding: var(--a-3);
    background: var(--farbe-flaeche-hoch);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-m);
  }
  .editor-leiste {
    display: flex;
    align-items: center;
    gap: var(--a-3);
  }
  .hinweis {
    margin-left: auto;
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
  }
  .hinweis-leer {
    margin: 0;
    color: var(--farbe-text-2);
    font-size: var(--text-s);
  }
</style>
