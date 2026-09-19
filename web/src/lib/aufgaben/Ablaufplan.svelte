<script lang="ts">
  // Ablaufplan — dieselben offenen Aufgaben wie die Liste, aber nach
  // `@braucht:` in Stufen gelegt: Stufe 1 ist sofort möglich, Stufe 2 wird
  // frei, sobald Stufe 1 steht. Gerechnet wird im Kern (tools/ablauf.py),
  // dieselben Zahlen wie `python camper.py ablauf`.
  //
  // Die Aufgaben sind hier nicht bearbeitbar: der Plan beantwortet „in
  // welcher Reihenfolge", das Abhaken passiert in der Liste und auf der
  // Startseite. Ein Klick führt auf die Aufgabe.
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { Etikett, Karte, Kennzahl, Leerzustand, Rubrik, Statusmarke } from '../ui';
  import { IconWarnung, IconWerkzeug } from '../ui/icons';

  let {
    bereich,
    // Eingebettet (Bereich-Reiter) soll ein Klick nicht aus dem Bereich
    // herausspringen — dann reicht der Aufrufer sein eigenes Öffnen herein.
    onOeffnen,
  }: { bereich?: string; onOeffnen?: (id: string) => void } = $props();

  let a = $derived(store.daten?.ablauf);

  // Der Server rechnet über alle Bereiche (sonst fehlen fremde Blocker) und
  // liefert alles; gefiltert wird hier, damit der eingebettete Fall stimmt.
  function imBereich<T extends { bereich: string }>(liste: T[]): T[] {
    return bereich ? liste.filter((x) => x.bereich === bereich) : liste;
  }

  let stufen = $derived(
    (a?.stufen ?? [])
      .map((s) => ({ ...s, aufgaben: imBereich(s.aufgaben ?? []) }))
      .filter((s) => s.aufgaben.length),
  );
  let schluessel = $derived(imBereich(a?.schluessel ?? []).slice(0, 8));
  let ring = $derived(imBereich(a?.ring ?? []));
  let offen = $derived(stufen.reduce((n, s) => n + s.aufgaben.length, 0));

  function oeffnen(id: string): void {
    if (onOeffnen) onOeffnen(id);
    else router.gehe('aufgaben', id);
  }

  function stufenwort(nr: number): string {
    return nr === 1 ? 'sofort möglich' : `frei nach Stufe ${nr - 1}`;
  }
</script>

{#if !a || !offen}
  <Leerzustand
    icon={IconWerkzeug}
    titel={bereich ? `Nichts offen in ${bereich}` : 'Nichts offen'}
    text="Der Ablaufplan zeigt, was noch ansteht und in welcher Reihenfolge es geht."
  />
{:else}
  <div class="kennzahlen">
    <Kennzahl titel="Offen" wert={offen} zusatz="Aufgaben ohne Unterpunkte" />
    <Kennzahl titel="Stufen" wert={stufen.length} zusatz="frühestmögliche Runden" />
    <Kennzahl
      titel="Sofort möglich"
      wert={stufen[0]?.stufe === 1 ? stufen[0].aufgaben.length : 0}
      ton="signal"
      zusatz="ohne offene Blocker"
    />
  </div>

  {#if ring.length}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        <span>
          <strong>{ring.length} {ring.length === 1 ? 'Aufgabe hängt' : 'Aufgaben hängen'} im Kreis</strong>
          — sie warten gegenseitig aufeinander und werden nie von selbst frei.
          Ein <code>@braucht:</code> darin muss weg.
        </span>
      </p>
      <ul class="ringliste">
        {#each ring as r (r.id)}
          <li>
            <button type="button" onclick={() => oeffnen(r.id)}>{r.titel}</button>
            <span class="schwach">braucht {r.braucht?.join(', ')}</span>
          </li>
        {/each}
      </ul>
    </Karte>
  {/if}

  {#if schluessel.length}
    <section class="block">
      <Rubrik titel="Schlüsselaufgaben" zahl={schluessel.length} />
      <Karte polster="keins">
        <ul class="liste">
          {#each schluessel as s (s.id)}
            <li>
              <button type="button" class="titel" onclick={() => oeffnen(s.id)}>{s.titel}</button>
              <span class="schwach">{s.bereich}</span>
              <span class="haelt" title="{s.haelt_auf} offene Aufgaben hängen daran">
                hält <b class="zahl">{s.haelt_auf}</b> auf
              </span>
            </li>
          {/each}
        </ul>
      </Karte>
      <p class="fussnote">
        Gezählt wird über die ganze Kette, nicht nur direkt. Hier lohnt Aufwand am meisten.
      </p>
    </section>
  {/if}

  {#each stufen as s (s.stufe)}
    <section class="block">
      <Rubrik titel="Stufe {s.stufe} — {stufenwort(s.stufe)}" zahl={s.aufgaben.length} />
      <Karte polster="keins">
        <ul class="liste">
          {#each s.aufgaben as t (t.id)}
            <li>
              <Statusmarke status={t.status} kompakt />
              <button type="button" class="titel" onclick={() => oeffnen(t.id)}>{t.titel}</button>
              <span class="schwach">{t.bereich}</span>
              {#if t.prio && t.prio !== 'mittel'}
                <Etikett ton={t.prio === 'kritisch' ? 'warn' : 'signal'}>{t.prio}</Etikett>
              {/if}
              {#if t.dauer}<Etikett>{t.dauer}</Etikett>{/if}
              {#if t.haelt_auf}
                <span class="haelt">hält <b class="zahl">{t.haelt_auf}</b> auf</span>
              {/if}
            </li>
          {/each}
        </ul>
      </Karte>
    </section>
  {/each}

  <p class="fussnote">
    Die Stufe ist die früheste Runde, in der eine Aufgabe drankommen kann — eine
    Reihenfolge, kein Termin. Gleiche Zahlen wie <code>camper ablauf</code>.
  </p>
{/if}

<style>
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 220px));
    gap: var(--a-3);
    margin-bottom: var(--a-6);
  }

  .block { margin-bottom: var(--a-6); }

  .liste,
  .ringliste { list-style: none; margin: 0; padding: 0; }
  .liste li {
    display: flex;
    align-items: center;
    gap: var(--a-3);
    min-height: 38px;
    padding: var(--a-2) var(--a-4);
    border-bottom: 1px solid var(--farbe-linie);
  }
  .liste li:last-child { border-bottom: 0; }
  .liste li:hover { background: var(--farbe-flaeche-hoch); }

  .titel {
    flex: 1;
    min-width: 0;
    text-align: left;
    background: none;
    border: 0;
    padding: 0;
    font: inherit;
    font-size: var(--text-m);
    color: var(--farbe-text);
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .titel:hover { text-decoration: underline; }

  .schwach { flex: none; font-size: var(--text-s); color: var(--farbe-text-2); }
  .haelt { flex: none; font-size: var(--text-s); color: var(--farbe-text-2); white-space: nowrap; }
  .zahl { font-family: var(--schrift-mono); color: var(--farbe-text); }

  .hinweis {
    display: flex;
    align-items: flex-start;
    gap: var(--a-2);
    margin: 0 0 var(--a-3);
    font-size: var(--text-m);
  }
  .ringliste li {
    display: flex;
    gap: var(--a-3);
    align-items: baseline;
    padding: 4px 0;
  }
  .ringliste button {
    background: none;
    border: 0;
    padding: 0;
    font: inherit;
    color: var(--farbe-text);
    cursor: pointer;
    text-decoration: underline;
  }

  .fussnote {
    margin: var(--a-2) 0 var(--a-6);
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
