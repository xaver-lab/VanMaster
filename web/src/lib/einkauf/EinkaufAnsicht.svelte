<script lang="ts">
  // Einkauf — was als Nächstes bestellt werden kann, nach Händler gebündelt.
  // Dieselbe Auswahl und Reihenfolge wie `python camper.py buy next`
  // (tools/parts.py: buy_daten); sortiert wird dort, hier wird angezeigt und
  // abgehakt.
  //
  // Der Unterschied zur Teileliste ist der Arbeitsschritt: hier steht man
  // beim Bestellen, hat einen Händlerkorb offen und setzt danach alles auf
  // einmal auf "Bestellt". Genau dafür die Mehrfachauswahl.
  import { store } from '../daten.svelte';
  import { toasts } from '../toasts.svelte';
  import { dezimal } from '../zahlformat';
  import Schreibbar from '../Schreibbar.svelte';
  import { bestaetigen, Karte, Kennzahl, Knopf, Kontrollkaestchen, Leerzustand, Rubrik } from '../ui';
  import { IconEuro, IconExtern, IconTeile } from '../ui/icons';

  let e = $derived(store.daten?.einkauf);
  let nachId = $derived(new Map((store.daten?.teile ?? []).map((t) => [t.id, t])));

  // Angehakt = geht in den nächsten Bestelllauf. Nur IDs merken, damit die
  // Auswahl ein Neuladen der Daten übersteht.
  let gewaehlt = $state<Set<string>>(new Set());
  let laeuft = $state(false);

  let gruppen = $derived(
    (e?.gruppen ?? []).map((g) => ({
      ...g,
      teile: (g.teile ?? []).map((id) => nachId.get(id)).filter((t) => !!t),
    })),
  );

  // Teile, die es nicht mehr gibt, fallen still aus der Auswahl.
  let gueltigGewaehlt = $derived(
    [...gewaehlt].filter((id) => gruppen.some((g) => g.teile.some((t) => t.id === id))),
  );
  let summeGewaehlt = $derived(
    gueltigGewaehlt.reduce((s, id) => {
      const t = nachId.get(id);
      return s + (t ? betrag(t) : 0);
    }, 0),
  );

  function betrag(t: { preis: string; menge: string }): number {
    const preis = Number(String(t.preis ?? '').replace(',', '.')) || 0;
    const menge = Number(String(t.menge ?? '').replace(',', '.')) || 1;
    return preis * menge;
  }

  function mengeText(t: { menge: string }): string {
    const m = Number(String(t.menge ?? '').replace(',', '.')) || 1;
    return m === 1 ? '' : `${m}× `;
  }

  function umschalten(id: string, an: boolean): void {
    const neu = new Set(gewaehlt);
    if (an) neu.add(id);
    else neu.delete(id);
    gewaehlt = neu;
  }

  function gruppeUmschalten(ids: string[], an: boolean): void {
    const neu = new Set(gewaehlt);
    for (const id of ids) {
      if (an) neu.add(id);
      else neu.delete(id);
    }
    gewaehlt = neu;
  }

  async function bestellen(): Promise<void> {
    const ids = gueltigGewaehlt;
    if (!ids.length || laeuft) return;
    const ok = await bestaetigen({
      titel: `${ids.length} ${ids.length === 1 ? 'Teil' : 'Teile'} auf „Bestellt“ setzen?`,
      text: `Zusammen ${dezimal(summeGewaehlt, 2)} €. Der Status wandert von „Entschieden“ auf „Bestellt“ — danach stehen sie nicht mehr auf dieser Liste.`,
      ja: 'Als bestellt eintragen',
    });
    if (!ok) return;

    laeuft = true;
    let fertig = 0;
    // Ein Toast für den ganzen Lauf, nicht einer je Teil.
    await store.ohneRueckgaengig(async () => {
      for (const id of ids) {
        // Nacheinander, nicht parallel: jede Antwort trägt die neue
        // Dateiversion, sonst läuft der zweite Schreibzugriff in einen 409.
        const erfolg = await store.teilPatch(id, 'status', 'Bestellt');
        if (!erfolg) break;
        fertig++;
      }
    });
    laeuft = false;

    if (fertig === ids.length) {
      toasts.info(`${fertig} ${fertig === 1 ? 'Teil' : 'Teile'} auf „Bestellt“ gesetzt.`);
      gewaehlt = new Set();
    } else {
      toasts.fehler(
        `Nur ${fertig} von ${ids.length} Teilen umgestellt — der Rest bleibt ausgewählt.`,
      );
      gewaehlt = new Set(ids.slice(fertig));
    }
  }
</script>

{#if !e || !e.teile_gesamt}
  <Leerzustand
    titel="Nichts zu bestellen"
    text="Auf dieser Liste steht, was den Status „Entschieden“ hat. Teile, die noch in der Recherche sind, tauchen hier erst auf, wenn die Entscheidung steht."
    icon={IconTeile}
  >
    <Knopf href="#/teile" variante="sekundaer">Zur Teileliste</Knopf>
  </Leerzustand>
{:else}
  <div class="kopf">
    <div class="kennzahlen">
      <Kennzahl titel="Zu bestellen" wert={e.teile_gesamt} icon={IconTeile} zusatz="Status „Entschieden“" />
      <Kennzahl titel="Summe" wert="{dezimal(e.summe, 0)} €" icon={IconEuro} zusatz="{gruppen.length} Händler" />
      {#if gueltigGewaehlt.length}
        <Kennzahl
          titel="Ausgewählt"
          wert="{gueltigGewaehlt.length} · {dezimal(summeGewaehlt, 0)} €"
          ton="signal"
          zusatz="für den nächsten Bestelllauf"
        />
      {/if}
    </div>

    {#if gueltigGewaehlt.length}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="primaer" onclick={bestellen} laedt={laeuft}>
            {gueltigGewaehlt.length}
            {gueltigGewaehlt.length === 1 ? 'Teil' : 'Teile'} als bestellt eintragen
          </Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  </div>

  {#each gruppen as g (g.haendler)}
    {@const ids = g.teile.map((t) => t.id)}
    {@const alleAn = ids.length > 0 && ids.every((id) => gewaehlt.has(id))}
    {@const einigeAn = !alleAn && ids.some((id) => gewaehlt.has(id))}
    <section class="gruppe">
      <Rubrik titel={g.haendler} zahl="{dezimal(g.summe, 0)} €" />
      <Karte polster="keins">
        <ul class="liste">
          <Schreibbar>
            {#snippet children()}
              <li class="zeile kopfzeile">
                <Kontrollkaestchen
                  checked={alleAn}
                  gemischt={einigeAn}
                  onchange={(an) => gruppeUmschalten(ids, an)}
                  label="Alles von {g.haendler} auswählen"
                />
                <span class="alle">ganzen Korb auswählen</span>
              </li>
            {/snippet}
          </Schreibbar>

          {#each g.teile as t (t.id)}
            <li class="zeile">
              <Schreibbar>
                {#snippet children()}
                  <Kontrollkaestchen
                    checked={gewaehlt.has(t.id)}
                    onchange={(an) => umschalten(t.id, an)}
                    label="{t.titel} in den Bestelllauf"
                  />
                {/snippet}
              </Schreibbar>

              <a class="titel" href="#/teile/{encodeURIComponent(t.id)}">
                {mengeText(t)}{t.titel}
              </a>

              <span class="prio">{t.prioritaet}</span>
              <span class="preis zahl">{betrag(t) ? `${dezimal(betrag(t), 2)} €` : '—'}</span>

              {#if t.link}
                <a class="shop" href={t.link} target="_blank" rel="noopener noreferrer" title={t.link}>
                  <IconExtern size={14} strokeWidth={2} aria-hidden="true" />
                  <span class="vb">Shop</span>
                </a>
              {:else}
                <span class="shop leer">—</span>
              {/if}
            </li>
          {/each}
        </ul>
      </Karte>
    </section>
  {/each}

  <p class="fussnote">
    Reihenfolge wie <code>camper buy next</code>: erst nach Priorität, dann nach Betrag.
    Teile ohne Preis stehen mit „—“ da und zählen nicht in die Summe.
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
    grid-template-columns: repeat(auto-fit, minmax(180px, 220px));
    gap: var(--a-3);
  }

  .gruppe { margin-bottom: var(--a-7); }

  .liste { list-style: none; margin: 0; padding: 0; }
  .zeile {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    min-height: 40px;
    padding: var(--a-2) var(--a-4);
    border-bottom: 1px solid var(--farbe-linie);
  }
  .zeile:last-child { border-bottom: 0; }
  .zeile:hover { background: var(--farbe-flaeche-hoch); }

  .kopfzeile {
    min-height: 32px;
    background: var(--farbe-flaeche-tief);
  }
  .alle {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }

  .titel {
    flex: 1;
    min-width: 0;
    font-size: var(--text-m);
    color: var(--farbe-text);
    text-decoration: none;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .titel:hover { text-decoration: underline; }

  .prio {
    flex: none;
    width: 70px;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  .preis {
    flex: none;
    width: 90px;
    text-align: right;
  }
  .zahl {
    font-family: var(--schrift-mono);
    font-variant-numeric: tabular-nums;
    font-size: var(--text-s);
  }

  .shop {
    flex: none;
    width: 66px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: var(--text-s);
    color: var(--farbe-info);
    text-decoration: none;
  }
  .shop:hover { text-decoration: underline; }
  .shop.leer { color: var(--farbe-text-3); }
  .vb { display: inline-block; }

  .fussnote {
    margin: 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  code {
    font-family: var(--schrift-mono);
    font-size: 0.9em;
    background: var(--farbe-flaeche-hoch);
    border-radius: var(--r-s);
    padding: 1px 5px;
  }
</style>
