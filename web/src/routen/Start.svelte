<script lang="ts">
  // Startseite: wo steht der Ausbau, und was ist als Nächstes dran.
  //
  // Bewusst kurz. Kosten- und Kategoriezahlen standen hier früher noch einmal,
  // obwohl sie in `#/bilanz` und `#/teile` vollständig und bedienbar stehen —
  // doppelte Zahlen veralten unterschiedlich. Geblieben ist, was es sonst
  // nirgends gibt: der Gesamtstand, die Bauabschnitte in ihrer Reihenfolge,
  // was gerade läuft (hier direkt abhakbar) und was noch zu entscheiden ist.
  import { store } from '../lib/daten.svelte';
  import type { AufgabeAntwort, BereichAntwort } from '../lib/api-typen';
  import Schreibbar from '../lib/Schreibbar.svelte';
  import Karte from '../lib/ui/Karte.svelte';
  import Rubrik from '../lib/ui/Rubrik.svelte';
  import Etikett from '../lib/ui/Etikett.svelte';
  import Kontrollkaestchen from '../lib/ui/Kontrollkaestchen.svelte';
  import Statusmarke from '../lib/ui/Statusmarke.svelte';
  import FortschrittBalken from '../lib/ui/FortschrittBalken.svelte';
  import Leerzustand from '../lib/ui/Leerzustand.svelte';
  import { IconPfeil, IconWegweiser, IconWerkzeug } from '../lib/ui/icons';

  const euro = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 });
  const kg = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 1 });

  const REIHENFOLGE: Record<string, number> = { erledigt: 0, laeuft: 1, blockiert: 2, offen: 3, verworfen: 4 };
  const PRIO: Record<string, number> = { kritisch: 0, hoch: 1 };

  let d = $derived(store.daten);
  let k = $derived(d?.kennzahlen);

  interface Abschnitt {
    bereich: BereichAntwort;
    nr: string;
    aufgaben: AufgabeAntwort[];
    erledigt: number;
    laeuft: number;
    naechste: AufgabeAntwort | undefined;
    start: number;
  }

  let abschnitte = $derived.by((): Abschnitt[] => {
    if (!d) return [];
    const sortiert = [...d.bereiche].sort(
      (a, b) => (a.phase ?? 999) - (b.phase ?? 999) || a.name.localeCompare(b.name, 'de'),
    );
    let start = 0;
    return sortiert.map((bereich, i) => {
      const aufgaben = d.aufgaben
        .filter((a) => a.bereich === bereich.name && a.status !== 'verworfen')
        .sort((a, b) => (REIHENFOLGE[a.status] ?? 9) - (REIHENFOLGE[b.status] ?? 9));
      const nr = String(bereich.phase ?? i + 1).padStart(2, '0');
      start += aufgaben.length;
      return {
        start: start - aufgaben.length,
        bereich,
        nr,
        aufgaben,
        erledigt: aufgaben.filter((a) => a.status === 'erledigt').length,
        laeuft: aufgaben.filter((a) => a.status === 'laeuft').length,
        naechste: aufgaben.find((a) => a.status === 'laeuft') ?? aufgaben.find((a) => a.status === 'offen'),
      };
    });
  });

  let gesamt = $derived(abschnitte.reduce((s, a) => s + a.aufgaben.length, 0));
  let laeuftGesamt = $derived(abschnitte.reduce((s, a) => s + a.laeuft, 0));
  let anteil = $derived(k && k.aufgaben_gesamt ? k.aufgaben_fertig / k.aufgaben_gesamt : 0);

  let laufend = $derived(d ? d.aufgaben.filter((a) => a.status === 'laeuft') : []);

  let alsNaechstes = $derived.by(() => {
    if (!d) return [];
    const erledigt = new Set(d.aufgaben.filter((a) => a.status === 'erledigt').map((a) => a.id));
    return d.aufgaben
      .filter((a) => a.status === 'offen' && a.prio && a.prio in PRIO)
      .map((a) => ({ a, frei: (a.braucht ?? []).every((id) => erledigt.has(id)) }))
      .sort((x, y) => Number(y.frei) - Number(x.frei) || PRIO[x.a.prio!] - PRIO[y.a.prio!])
      .slice(0, 5);
  });

  let offeneEntscheidungen = $derived(d ? d.entscheidungen.filter((e) => e.status !== 'entschieden' && e.status !== 'erledigt') : []);

  function bereichStatus(s: string): { text: string; ton: 'signal' | 'neutral' | 'gut' } {
    if (s === 'in-arbeit') return { text: 'in Arbeit', ton: 'signal' };
    if (s === 'fertig' || s === 'erledigt') return { text: 'fertig', ton: 'gut' };
    return { text: s.replace(/-/g, ' '), ton: 'neutral' };
  }

  function bereichLink(name: string): string {
    return `#/bereiche/${encodeURIComponent(name)}`;
  }

  // Direkt von der Startseite abhaken — der häufigste Handgriff überhaupt.
  // Sammelaufgaben bleiben gesperrt, die hängen an ihren Unterpunkten.
  async function abhaken(a: AufgabeAntwort, erledigt: boolean): Promise<void> {
    if (a.kinder?.length || store.beschaeftigt) return;
    await store.aufgabePatch(a.id, a.datei ?? '', { status: erledigt ? 'erledigt' : 'offen' });
  }

</script>

{#if d && k}
  <!-- ------------------------------------------------------ Kopfzeile -->
  <section class="held">
    <div class="held-zahl">
      <p class="ueber">Ausbaustand</p>
      <p class="prozent"><span class="zahl-gross">{Math.round(anteil * 100)}</span><span class="einheit">%</span></p>
      <p class="satz">
        <strong>{k.aufgaben_fertig}</strong> von {k.aufgaben_gesamt} Aufgaben erledigt,
        <span class="laeuft">{laeuftGesamt} laufen</span> gerade.
      </p>
    </div>

    <!-- Vier Zahlen, jede ein Weg in die Ansicht, die sie ganz zeigt. -->
    <dl class="eckdaten">
      <div>
        <dt>Geplant</dt>
        <dd><a href="#/bilanz"><span class="zahl">{euro.format(k.kosten)}</span><small>€</small></a></dd>
      </div>
      <div>
        <dt>Bestellt</dt>
        <dd><a href="#/einkauf"><span class="zahl">{euro.format(k.kosten_bestellt)}</span><small>€</small></a></dd>
      </div>
      <div>
        <dt>Zuladung</dt>
        <dd><a href="#/bilanz/gewicht"><span class="zahl">{kg.format(k.gewicht)}</span><small>kg</small></a></dd>
      </div>
      <div class:offen={k.offene_entscheidungen > 0}>
        <dt>Offen</dt>
        <dd><span class="zahl">{k.offene_entscheidungen}</span><small>Entsch.</small></dd>
      </div>
    </dl>

    <!-- Bauleiste: jede Aufgabe ein Feld, gruppiert nach Bauabschnitt -->
    <div class="bauleiste" role="img" aria-label="{k.aufgaben_fertig} von {gesamt} Aufgaben erledigt, nach Bauabschnitt">
      {#each abschnitte as ab}
        {#if ab.aufgaben.length}
          <a class="gruppe" href={bereichLink(ab.bereich.name)} style:flex-grow={ab.aufgaben.length + 2} title="{ab.bereich.name}: {ab.erledigt}/{ab.aufgaben.length}">
            <span class="felder">
              {#each ab.aufgaben as a, j}
                <span class="feld {a.status}" style:animation-delay="{Math.min(ab.start + j, 80) * 14}ms" title={a.titel}></span>
              {/each}
            </span>
            <span class="gruppen-text">
              <span class="nr">{ab.nr}</span>
              <span class="name">{ab.bereich.name}</span>
              <span class="bruch">{ab.erledigt}/{ab.aufgaben.length}</span>
            </span>
          </a>
        {/if}
      {/each}
    </div>
    <div class="legende" aria-hidden="true">
      <span><i class="feld erledigt"></i>erledigt</span>
      <span><i class="feld laeuft"></i>läuft</span>
      <span><i class="feld offen"></i>offen</span>
    </div>
  </section>

  <!-- ---------------------------------------------------- Hauptraster -->
  <div class="raster">
    <section class="abschnitte">
      <Rubrik titel="Bauabschnitte" zahl={String(abschnitte.length).padStart(2, '0')} />
      <ol class="liste">
        {#each abschnitte as ab}
          {@const st = bereichStatus(ab.bereich.status)}
          <li>
            <a href={bereichLink(ab.bereich.name)} title={ab.bereich.kurz}>
              <span class="nr" class:aktiv={ab.bereich.status === 'in-arbeit'}>{ab.nr}</span>
              <span class="kern">
                <span class="zeile1">
                  <span class="name">{ab.bereich.name}</span>
                  <Etikett ton={st.ton}>{st.text}</Etikett>
                </span>
                <span class="zeile2">
                  {#if ab.naechste}
                    <span class="pfeil">{ab.naechste.status === 'laeuft' ? 'läuft' : 'als Nächstes'}</span>
                    {ab.naechste.titel}
                  {:else if ab.aufgaben.length}
                    alles erledigt
                  {:else}
                    {ab.bereich.kurz}
                  {/if}
                </span>
              </span>
              <span class="fortschritt">
                <FortschrittBalken
                  wert={ab.aufgaben.length ? ab.erledigt / ab.aufgaben.length : 0}
                  zusatz={ab.aufgaben.length ? ab.laeuft / ab.aufgaben.length : 0}
                  teilung={ab.aufgaben.length}
                  hoehe={8}
                  zahl="{ab.erledigt}/{ab.aufgaben.length}"
                />
              </span>
              <span class="los"><IconPfeil size={16} strokeWidth={1.8} /></span>
            </a>
          </li>
        {/each}
      </ol>
    </section>

    <section class="jetzt">
      <Rubrik titel="Jetzt dran" zahl={String(laufend.length).padStart(2, '0')} />
      <Karte polster="keins">
        {#if laufend.length}
          <ul class="aufgabenliste">
            {#each laufend as a (a.id)}
              <li>
                <Schreibbar>
                  {#snippet children()}
                    <Kontrollkaestchen
                      checked={false}
                      disabled={!!a.kinder?.length || store.beschaeftigt}
                      titel={a.kinder?.length ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'erledigt'}
                      onchange={(an) => abhaken(a, an)}
                    />
                  {/snippet}
                </Schreibbar>
                <Statusmarke status={a.status} kompakt />
                <span class="a-text">
                  <span class="a-titel">{a.titel}</span>
                  <span class="a-meta">
                    <a href={bereichLink(a.bereich)}>{a.bereich}</a>
                    {#if a.braucht?.length}<span class="braucht">braucht {a.braucht.join(', ')}</span>{/if}
                  </span>
                </span>
              </li>
            {/each}
          </ul>
        {:else}
          <Leerzustand kompakt icon={IconWerkzeug} titel="Nichts in Arbeit" text="Eine Aufgabe auf „läuft“ setzen, dann steht sie hier." />
        {/if}
        {#if alsNaechstes.length}
          <p class="zwischenkopf">Als Nächstes · wichtig</p>
          <ul class="aufgabenliste">
            {#each alsNaechstes as { a, frei } (a.id)}
              <li class:gesperrt={!frei}>
                <Schreibbar>
                  {#snippet children()}
                    <Kontrollkaestchen
                      checked={false}
                      disabled={!!a.kinder?.length || store.beschaeftigt}
                      titel={a.kinder?.length ? 'Sammelaufgabe — Haken an den Unterpunkten' : 'erledigt'}
                      onchange={(an) => abhaken(a, an)}
                    />
                  {/snippet}
                </Schreibbar>
                <Statusmarke status={frei ? 'offen' : 'blockiert'} kompakt titel={frei ? 'offen' : 'wartet auf andere Aufgaben'} />
                <span class="a-text">
                  <span class="a-titel">{a.titel}</span>
                  <span class="a-meta">
                    <a href={bereichLink(a.bereich)}>{a.bereich}</a>
                    {#if !frei}<span class="braucht">wartet auf {a.braucht?.join(', ')}</span>{/if}
                  </span>
                </span>
                <Etikett ton={a.prio === 'kritisch' ? 'warn' : 'neutral'}>{a.prio}</Etikett>
              </li>
            {/each}
          </ul>
        {/if}
      </Karte>
    </section>
  </div>

  <!-- Entscheidungen haben keine eigene Ansicht; Claude pflegt sie im Vault.
       Deshalb stehen sie hier — und nur sie. Budget, Teilestufen und Kosten je
       Kategorie standen früher daneben und wiederholten nur, was `#/bilanz`
       und `#/teile` vollständig zeigen. -->
  <section class="entscheidungen-block">
    <Rubrik titel="Offene Entscheidungen" zahl={String(offeneEntscheidungen.length).padStart(2, '0')} />
    <Karte ton={offeneEntscheidungen.length ? 'signal' : 'flaeche'}>
      {#if offeneEntscheidungen.length}
        <ul class="entscheidungen">
          {#each offeneEntscheidungen as e (e.datei)}
            <li>
              <a href={bereichLink(e.bereich)}>
                <span class="e-titel">{e.titel}</span>
                <span class="e-bereich">{e.bereich}</span>
              </a>
            </li>
          {/each}
        </ul>
        <p class="fussnote">Offene Entscheidungen halten oft Aufgaben und Bestellungen auf.</p>
      {:else}
        <Leerzustand kompakt icon={IconWegweiser} titel="Alles entschieden" />
      {/if}
    </Karte>
  </section>

{/if}

<style>
  /* ------------------------------------------------------------ Held */
  .held {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: end;
    gap: var(--a-5) var(--a-7);
    margin-bottom: var(--a-7);
  }
  .ueber {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .prozent { display: flex; align-items: flex-start; line-height: 0.85; margin: var(--a-2) 0 var(--a-3); }
  .zahl-gross {
    font-size: clamp(4.5rem, 8vw, 7.5rem);
    font-weight: 800;
    font-stretch: 125%;
    letter-spacing: -0.05em;
    font-variant-numeric: tabular-nums;
  }
  .einheit {
    margin: 0.35rem 0 0 0.3rem;
    font-size: 2rem;
    font-weight: 700;
    font-stretch: 125%;
    color: var(--farbe-signal);
  }
  .satz { color: var(--farbe-text-2); font-size: var(--text-l); max-width: 40ch; }
  .satz strong { color: var(--farbe-text); font-weight: 650; }
  .satz .laeuft { color: var(--farbe-signal); font-weight: 600; }

  .eckdaten { display: flex; margin: 0; padding-bottom: 6px; }
  .eckdaten div {
    padding: 0 var(--a-5);
    border-left: 1px solid var(--farbe-linie-stark);
    min-width: 120px;
  }
  .eckdaten dt {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .eckdaten dd { margin: 6px 0 0; font-size: 1.75rem; font-weight: 600; line-height: 1; white-space: nowrap; }
  .eckdaten dd .zahl { letter-spacing: -0.04em; }
  .eckdaten small { font-size: var(--text-s); color: var(--farbe-text-2); margin-left: 4px; font-weight: 500; }
  .eckdaten .offen dd { color: var(--farbe-signal); }
  /* Die Zahlen führen in die Ansicht, die sie ganz zeigt — sichtbar erst
     beim Überfahren, damit die Kopfzeile ruhig bleibt. */
  .eckdaten dd a {
    color: inherit;
    text-decoration: none;
    border-bottom: 2px solid transparent;
    transition: border-color var(--t-kurz);
  }
  .eckdaten dd a:hover { border-bottom-color: var(--farbe-signal); }

  .bauleiste { grid-column: 1 / -1; display: flex; gap: 10px; align-items: flex-start; }
  .gruppe {
    flex-basis: 0;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: inherit;
    text-decoration: none;
    border-radius: var(--r-s);
  }
  .felder {
    display: flex;
    gap: 3px;
    height: 40px;
    padding-top: 8px;
    border-top: 1px solid var(--farbe-linie-stark);
    position: relative;
  }
  .felder::before,
  .felder::after {
    content: '';
    position: absolute;
    top: -5px;
    height: 9px;
    width: 1px;
    background: var(--farbe-linie-stark);
  }
  .felder::before { left: 0; }
  .felder::after { right: 0; }
  .feld {
    flex: 1;
    min-width: 3px;
    border-radius: 2px;
    background: var(--farbe-flaeche);
    box-shadow: inset 0 0 0 1px var(--farbe-linie-stark);
    animation: feld-ein var(--t-lang) var(--kurve) both;
    transition: transform var(--t-kurz) var(--kurve);
  }
  .feld.erledigt { background: var(--farbe-gut); box-shadow: none; }
  .feld.laeuft {
    background: repeating-linear-gradient(-45deg, var(--farbe-signal) 0 3px, transparent 3px 6px), var(--farbe-signal-grund);
    box-shadow: inset 0 0 0 1px var(--farbe-signal);
  }
  .feld.blockiert { background: var(--farbe-warn-grund); box-shadow: inset 0 0 0 1px var(--farbe-warn); }
  .gruppe:hover .feld { transform: translateY(-3px); }
  .gruppe:hover .name { color: var(--farbe-signal); }
  @keyframes feld-ein { from { opacity: 0; transform: scaleY(0.2); } }

  .gruppen-text { display: flex; align-items: baseline; gap: 6px; min-width: 0; font-size: var(--text-s); }
  .gruppen-text .nr { font-family: var(--schrift-mono); font-size: 0.6875rem; color: var(--farbe-text-3); }
  .gruppen-text .name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color var(--t-kurz); }
  .gruppen-text .bruch { margin-left: auto; font-family: var(--schrift-mono); font-size: 0.6875rem; color: var(--farbe-text-2); }

  .legende { grid-column: 1 / -1; display: flex; gap: var(--a-4); margin-top: calc(-1 * var(--a-3)); font-size: var(--text-xs); color: var(--farbe-text-2); }
  .legende span { display: inline-flex; align-items: center; gap: 6px; }
  .legende i { display: inline-block; width: 10px; height: 10px; animation: none; }

  /* --------------------------------------------------------- Raster */
  .raster {
    display: grid;
    grid-template-columns: minmax(0, 1.7fr) minmax(320px, 1fr);
    gap: var(--a-6);
    margin-bottom: var(--a-7);
  }

  .liste {
    list-style: none;
    margin: 0;
    padding: 0;
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-l);
    box-shadow: var(--schatten-1);
    overflow: hidden;
  }
  .liste li + li { border-top: 1px solid var(--farbe-linie); }
  .liste a {
    display: grid;
    grid-template-columns: 44px minmax(0, 1fr) minmax(140px, 220px) 20px;
    align-items: center;
    gap: var(--a-4);
    padding: 14px var(--a-5) 14px var(--a-4);
    color: inherit;
    text-decoration: none;
    transition: background-color var(--t-kurz);
  }
  .liste a:hover { background: var(--farbe-flaeche-hoch); }
  .liste .nr {
    font-family: var(--schrift-mono);
    font-size: 1.375rem;
    font-weight: 300;
    letter-spacing: -0.04em;
    color: var(--farbe-text-3);
    text-align: right;
  }
  .liste .nr.aktiv { color: var(--farbe-signal); font-weight: 500; }
  .kern { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .zeile1 { display: flex; align-items: center; gap: var(--a-2); }
  .zeile1 .name { font-size: 1.0625rem; font-weight: 650; font-stretch: 106%; letter-spacing: -0.01em; }
  .zeile2 {
    font-size: var(--text-s);
    color: var(--farbe-text-2);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .zeile2 .pfeil {
    font-family: var(--schrift-mono);
    font-size: 0.6875rem;
    color: var(--farbe-text-3);
    margin-right: 4px;
  }
  .zeile2 .pfeil::after { content: ' →'; }
  .los { color: var(--farbe-text-3); opacity: 0; transform: translateX(-4px); transition: all var(--t-mittel) var(--kurve); display: inline-flex; }
  .liste a:hover .los { opacity: 1; transform: none; color: var(--farbe-signal); }

  .aufgabenliste { list-style: none; margin: 0; padding: var(--a-2) 0; }
  .aufgabenliste li {
    display: flex;
    align-items: flex-start;
    gap: var(--a-3);
    padding: 9px var(--a-5) 9px var(--a-4);
  }
  .aufgabenliste :global(.ui-status) { margin-top: -1px; }
  .aufgabenliste :global(.ui-etikett) { margin-left: auto; flex: none; }
  .a-text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
  .a-titel { font-size: var(--text-s); font-weight: 550; line-height: 1.35; }
  .gesperrt .a-titel { color: var(--farbe-text-2); }
  .a-meta { display: flex; gap: var(--a-2); font-size: var(--text-xs); color: var(--farbe-text-2); margin-top: 2px; flex-wrap: wrap; }
  .a-meta a { color: var(--farbe-text-2); text-decoration: none; font-weight: 600; }
  .a-meta a:hover { color: var(--farbe-signal); }
  .braucht { font-family: var(--schrift-mono); font-size: 0.6875rem; color: var(--farbe-text-3); }
  .zwischenkopf {
    margin: 0 var(--a-4);
    padding: var(--a-3) 0 var(--a-1);
    border-top: 1px dashed var(--farbe-linie-stark);
    font-size: 0.6875rem;
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }

  /* --------------------------------------------------- Entscheidungen */
  .entscheidungen-block { margin-bottom: var(--a-7); }
  .fussnote { margin-top: var(--a-4); padding-top: var(--a-3); border-top: 1px dashed var(--farbe-linie); font-size: var(--text-xs); color: var(--farbe-text-2); }

  /* Über die ganze Breite: mehrere nebeneinander statt einer Spalte
     langgezogener Kästen. */
  .entscheidungen {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: var(--a-2);
  }
  .entscheidungen a {
    display: flex;
    flex-direction: column;
    padding: 10px var(--a-3);
    background: var(--farbe-flaeche);
    border: 1px solid color-mix(in srgb, var(--farbe-signal) 25%, transparent);
    border-radius: var(--r-m);
    color: inherit;
    text-decoration: none;
    transition: border-color var(--t-kurz), transform var(--t-kurz) var(--kurve);
  }
  .entscheidungen a:hover { border-color: var(--farbe-signal); transform: translateX(2px); }
  .e-titel { font-weight: 600; font-size: var(--text-m); }
  .e-bereich { font-size: var(--text-xs); color: var(--farbe-text-2); }

  @media (max-width: 1280px) {
    .held { grid-template-columns: 1fr; }
    .eckdaten div:first-child { border-left: 0; padding-left: 0; }
  }
  @media (max-width: 1100px) {
    .raster { grid-template-columns: 1fr; }
    .dreier { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 820px) {
    .dreier { grid-template-columns: 1fr; }
    .eckdaten { flex-wrap: wrap; row-gap: var(--a-4); }
    .bauleiste { flex-wrap: wrap; }
    .gruppe { flex-basis: 40%; }
    .liste a { grid-template-columns: 32px minmax(0, 1fr); }
    .liste .fortschritt, .los { display: none; }
  }
</style>
