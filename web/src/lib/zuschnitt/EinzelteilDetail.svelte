<script lang="ts">
  // Detailfenster eines Einzelteils, als Dialog. Jedes Feld einzeln über
  // EinzelteilFeld: editierbar (Schreibbar) oder als Text im Lesemodus.
  // Bearbeitbarkeit richtet sich nach store.daten.bearbeitbar.einzelteil_felder,
  // nicht nach einer festen Liste.
  import type { EinzelteilAntwort, TeilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import { bestaetigen, Dialog, Etikett, Knopf, Rubrik } from '../ui';
  import { vokabular } from '../vokabular.svelte';
  import { IconLoeschen } from '../ui/icons';
  import EinzelteilFeld from './EinzelteilFeld.svelte';
  import { bauteilStatusTon } from './status';
  import { massText } from './mass';

  let {
    e,
    teile,
    bereiche,
    onClose,
  }: {
    e: EinzelteilAntwort;
    teile: TeilAntwort[];
    bereiche: string[];
    onClose: () => void;
  } = $props();

  let offen = $state(true);
  $effect(() => {
    if (!offen) onClose();
  });

  const matrix = $derived(store.daten?.bearbeitbar?.einzelteil_felder ?? {});
  const loeschenErlaubt = $derived(!!store.daten?.bearbeitbar?.einzelteil_loeschen);
  function bearbeitbar(feld: string): boolean {
    return !!matrix[feld]?.web;
  }

  const teilOptionen = $derived(teile.map((t) => ({ wert: t.id, label: t.titel })));

  function speichern(feld: string): (wert: string) => void {
    return (wert) => {
      if (wert === (e as unknown as Record<string, string>)[feld]) return;
      void store.einzelteilPatch(e.id, feld, wert);
    };
  }

  async function loeschen(): Promise<void> {
    const ja = await bestaetigen({
      titel: `Einzelteil „${e.titel}“ löschen?`,
      text: 'Das lässt sich nur über Git zurückholen.',
      ja: 'Löschen',
      gefaehrlich: true,
    });
    if (!ja) return;
    const ok = await store.einzelteilLoeschen(e.id);
    if (ok) onClose();
  }
</script>

<Dialog bind:offen titel={e.titel} breite="l">
  <div class="kopf">
    {#if e.status}<Etikett ton={bauteilStatusTon(e.status)}>{e.status}</Etikett>{/if}
    <Etikett mono>{massText(e)}</Etikett>
  </div>

  <div>
    <Rubrik titel="Grunddaten" />
    <div class="raster">
      <EinzelteilFeld label="Titel" wert={e.titel} bearbeitbar={bearbeitbar('titel')} onSpeichern={speichern('titel')} />
      <EinzelteilFeld
        label="Bereich"
        wert={e.bereich}
        art="auswahl"
        optionen={bereiche}
        bearbeitbar={bearbeitbar('bereich')}
        onSpeichern={speichern('bereich')}
      />
      <EinzelteilFeld
        label="Art"
        wert={e.art}
        art="auswahl"
        optionen={vokabular.einzelteilArt}
        leer="—"
        bearbeitbar={bearbeitbar('art')}
        onSpeichern={speichern('art')}
      />
      <EinzelteilFeld label="Material" wert={e.material} bearbeitbar={bearbeitbar('material')} onSpeichern={speichern('material')} />
    </div>
  </div>

  <div>
    <Rubrik titel="Maße (mm) und Menge" />
    <div class="raster raster-4">
      <EinzelteilFeld label="Länge" wert={e.laenge_mm} art="number" mono einheit="mm" bearbeitbar={bearbeitbar('laenge_mm')} onSpeichern={speichern('laenge_mm')} />
      <EinzelteilFeld label="Breite" wert={e.breite_mm} art="number" mono einheit="mm" bearbeitbar={bearbeitbar('breite_mm')} onSpeichern={speichern('breite_mm')} />
      <EinzelteilFeld label="Dicke" wert={e.dicke_mm} art="number" mono einheit="mm" bearbeitbar={bearbeitbar('dicke_mm')} onSpeichern={speichern('dicke_mm')} />
      <EinzelteilFeld label="Anzahl" wert={e.anzahl} art="number" mono bearbeitbar={bearbeitbar('anzahl')} onSpeichern={speichern('anzahl')} />
    </div>
  </div>

  <div>
    <Rubrik titel="Herkunft und Bezug" />
    <div class="raster">
      <EinzelteilFeld
        label="Aus Teil"
        wert={e.teil_id}
        art="auswahl"
        optionen={teilOptionen}
        leer="— kein Bezug —"
        bearbeitbar={bearbeitbar('teil_id')}
        onSpeichern={speichern('teil_id')}
      />
      <EinzelteilFeld
        label="Maßquelle"
        wert={e.massquelle}
        art="auswahl"
        optionen={vokabular.massquelle}
        leer="—"
        bearbeitbar={bearbeitbar('massquelle')}
        onSpeichern={speichern('massquelle')}
      />
      <EinzelteilFeld label="Für Aufgabe" wert={e.fuer_aufgabe} bearbeitbar={bearbeitbar('fuer_aufgabe')} onSpeichern={speichern('fuer_aufgabe')} />
      <EinzelteilFeld label="Status" wert={e.status} art="auswahl" optionen={vokabular.einzelteilStatus} leer="—" bearbeitbar={bearbeitbar('status')} onSpeichern={speichern('status')} />
    </div>
  </div>

  <div>
    <Rubrik titel="Notiz" />
    <EinzelteilFeld label="Notiz" wert={e.notiz} art="textfeld" bearbeitbar={bearbeitbar('notiz')} onSpeichern={speichern('notiz')} />
  </div>

  {#snippet fuss()}
    {#if loeschenErlaubt}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="gefaehrlich" icon={IconLoeschen} onclick={loeschen}>Löschen …</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  {/snippet}
</Dialog>

<style>
  .kopf {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
  }
  .raster {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--a-3);
  }
  .raster-4 {
    grid-template-columns: repeat(4, 1fr);
  }
</style>
