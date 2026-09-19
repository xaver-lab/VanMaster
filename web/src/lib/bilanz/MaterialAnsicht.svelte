<script lang="ts">
  // Material — was fürs Baumarkt gebraucht wird, nach Material und Dicke
  // gruppiert. Dieselben Gruppen und Bedarfstexte wie `python camper.py
  // material` (tools/material.py); gerechnet wird dort, hier steht die
  // Anzeige und der Filter nach Bereich (`--bereich` auf der Kommandozeile).
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { massText, zahl } from '../zuschnitt/mass';
  import { bauteilStatusTon } from '../zuschnitt/status';
  import { Auswahl, Etikett, Karte, Kennzahl, Leerzustand, Rubrik } from '../ui';
  import { IconZuschnitt } from '../ui/icons';

  let bereich = $state('');

  let einzelteile = $derived(store.daten?.einzelteile ?? []);
  let nachId = $derived(new Map(einzelteile.map((e) => [e.id, e])));

  let bereiche = $derived(
    [...new Set(einzelteile.map((e) => e.bereich).filter(Boolean))].sort((a, b) =>
      a.localeCompare(b, 'de'),
    ),
  );

  // Die Gruppen kommen fertig vom Server; der Bereichsfilter wirkt auf die
  // Zuschnitte darin. Eine Gruppe ohne übrige Zuschnitte fällt weg.
  let gruppen = $derived.by(() => {
    const roh = store.daten?.material ?? [];
    return roh
      .map((g) => ({
        ...g,
        teile: (g.zuschnitte ?? [])
          .map((id) => nachId.get(id))
          .filter((e) => !!e)
          .filter((e) => !bereich || e.bereich === bereich),
      }))
      .filter((g) => g.teile.length > 0);
  });

  let anzahlZuschnitte = $derived(gruppen.reduce((s, g) => s + g.teile.length, 0));

  function titel(g: { material: string; dicke_mm?: string }): string {
    return g.dicke_mm ? `${g.material}, ${g.dicke_mm} mm` : g.material;
  }
</script>

<div class="kopf">
  <div class="kennzahlen">
    <Kennzahl titel="Materialgruppen" wert={gruppen.length} icon={IconZuschnitt} />
    <Kennzahl titel="Zuschnitte" wert={anzahlZuschnitte} href="#/zuschnitt" />
  </div>

  {#if bereiche.length > 1}
    <div class="filter">
      <Auswahl bind:wert={bereich} label="Bereich" optionen={bereiche} leer="Alle Bereiche" />
    </div>
  {/if}
</div>

{#if gruppen.length === 0}
  <Leerzustand
    titel={bereich ? `Keine Einzelteile in ${bereich}` : 'Keine Einzelteile erfasst'}
    text={bereich
      ? 'Für diesen Bereich sind noch keine Zuschnitte angelegt.'
      : 'Sobald Zuschnitte in der Zuschnittliste stehen, entsteht hier die Einkaufsliste fürs Baumarkt.'}
    icon={IconZuschnitt}
  />
{:else}
  {#each gruppen as g (g.material + '|' + g.dicke_mm)}
    <section class="gruppe">
      <Rubrik titel={titel(g)} zahl={g.bedarf} />
      <Karte polster="keins">
        <table class="tabelle">
          <thead>
            <tr>
              <th scope="col">Zuschnitt</th>
              <th scope="col">Maß</th>
              <th scope="col" class="r">Anz</th>
              <th scope="col">Bereich</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {#each g.teile as e (e.id)}
              <tr>
                <th scope="row">
                  <a
                    href="#/zuschnitt/{encodeURIComponent(e.id)}"
                    onclick={(ev) => {
                      ev.preventDefault();
                      router.gehe('zuschnitt', e.id);
                    }}>{e.titel}</a
                  >
                </th>
                <td class="zahl">{massText(e)}</td>
                <td class="r zahl">{zahl(e.anzahl, 1)}</td>
                <td class="schwach">{e.bereich || '—'}</td>
                <td>
                  {#if e.status}<Etikett ton={bauteilStatusTon(e.status)}>{e.status}</Etikett>{/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </Karte>
    </section>
  {/each}

  <p class="fussnote">
    Bedarf: m² bei Platten, laufende Meter bei Leisten und Kanthölzern, sonst Stückzahl.
    Verschnitt ist nicht eingerechnet.
  </p>
{/if}

<style>
  .kopf {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--a-4);
    flex-wrap: wrap;
    margin-bottom: var(--a-6);
  }
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(2, minmax(160px, 200px));
    gap: var(--a-3);
  }
  .filter { min-width: 200px; }

  .gruppe { margin-bottom: var(--a-7); }

  .tabelle {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-s);
  }
  .tabelle th,
  .tabelle td {
    padding: var(--a-2) var(--a-4);
    text-align: left;
    border-bottom: 1px solid var(--farbe-linie);
  }
  .tabelle tbody tr:last-child th,
  .tabelle tbody tr:last-child td { border-bottom: 0; }
  .tabelle thead th {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .tabelle tbody th { font-weight: 550; }
  .tabelle tbody th a { color: inherit; text-decoration: none; }
  .tabelle tbody th a:hover { text-decoration: underline; }
  .tabelle tbody tr:hover { background: var(--farbe-flaeche-hoch); }

  .r { text-align: right; }
  .zahl {
    font-family: var(--schrift-mono);
    font-variant-numeric: tabular-nums;
  }
  .schwach { color: var(--farbe-text-2); }

  .fussnote {
    margin: 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
</style>
