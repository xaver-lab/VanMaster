<script lang="ts">
  import { store } from '../lib/daten.svelte';
  import type { AufgabeAntwort, BereichAntwort } from '../lib/api-typen';
  import Karte from '../lib/ui/Karte.svelte';
  import Rubrik from '../lib/ui/Rubrik.svelte';
  import Etikett from '../lib/ui/Etikett.svelte';
  import Statusmarke from '../lib/ui/Statusmarke.svelte';
  import FortschrittBalken from '../lib/ui/FortschrittBalken.svelte';
  import Leerzustand from '../lib/ui/Leerzustand.svelte';
  import { IconEuro, IconPfeil, IconTeile, IconWegweiser, IconWerkzeug } from '../lib/ui/icons';

  const euro = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 });
  const kg = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 1 });

  const REIHENFOLGE: Record<string, number> = { erledigt: 0, laeuft: 1, blockiert: 2, offen: 3, verworfen: 4 };
  const TEILE_STUFEN = ['Idee', 'Recherche', 'Entschieden', 'Bestellt', 'Geliefert', 'Verbaut'];
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

  let teileStufen = $derived.by(() => {
    if (!d) return [];
    const zaehl = new Map<string, number>();
    for (const t of d.teile) zaehl.set(t.status, (zaehl.get(t.status) ?? 0) + 1);
    const bekannte = TEILE_STUFEN.filter((s) => zaehl.has(s));
    const andere = [...zaehl.keys()].filter((s) => !TEILE_STUFEN.includes(s));
    return [...bekannte, ...andere].map((s) => ({ name: s, zahl: zaehl.get(s) ?? 0 }));
  });
  let ohnePreis = $derived(d ? d.teile.filter((t) => !t.preis.trim()).length : 0);

  let offeneEntscheidungen = $derived(d ? d.entscheidungen.filter((e) => e.status !== 'entschieden' && e.status !== 'erledigt') : []);

  function bereichStatus(s: string): { text: string; ton: 'signal' | 'neutral' | 'gut' } {
    if (s === 'in-arbeit') return { text: 'in Arbeit', ton: 'signal' };
    if (s === 'fertig' || s === 'erledigt') return { text: 'fertig', ton: 'gut' };
    return { text: s.replace(/-/g, ' '), ton: 'neutral' };
  }

  function stufenKlasse(name: string): string {
    const i = TEILE_STUFEN.indexOf(name);
    return i >= 0 ? `s${i}` : 's0';
  }

  function bereichLink(name: string): string {
    return `#/bereiche/${encodeURIComponent(name)}`;
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

    <dl class="eckdaten">
      <div>
        <dt>Geplant</dt>
        <dd><span class="zahl">{euro.format(k.kosten)}</span><small>€</small></dd>
      </div>
      <div>
        <dt>Bestellt</dt>
        <dd><span class="zahl">{euro.format(k.kosten_bestellt)}</span><small>€</small></dd>
      </div>
      <div>
        <dt>Zuladung</dt>
        <dd><span class="zahl">{kg.format(k.gewicht)}</span><small>kg</small></dd>
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
            {#each laufend as a}
              <li>
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
            {#each alsNaechstes as { a, frei }}
              <li class:gesperrt={!frei}>
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

  <div class="dreier">
    <Karte titel="Budget" icon={IconEuro} href="#/teile">
      <p class="grosszahl"><span class="zahl">{euro.format(k.kosten)}</span> <small>€ geplant</small></p>
      <FortschrittBalken wert={k.kosten ? k.kosten_bestellt / k.kosten : 0} ton="signal" hoehe={10} />
      <div class="budget-zeilen">
        <span><i class="punkt signal"></i>bestellt <b class="zahl">{euro.format(k.kosten_bestellt)} €</b></span>
        <span><i class="punkt"></i>offen <b class="zahl">{euro.format(Math.max(0, k.kosten - k.kosten_bestellt))} €</b></span>
      </div>
      {#if ohnePreis}
        <p class="fussnote">{ohnePreis} von {d.teile.length} Teilen haben noch keinen Preis — die Summe wächst noch.</p>
      {/if}
    </Karte>

    <Karte titel="Teile" icon={IconTeile} zusatz={d.teile.length} href="#/teile">
      <div class="stufenbalken" aria-hidden="true">
        {#each teileStufen as s}
          <span class="stufe {stufenKlasse(s.name)}" style:flex-grow={s.zahl} title="{s.name}: {s.zahl}"></span>
        {/each}
      </div>
      <ul class="stufen">
        {#each teileStufen as s}
          <li><i class="stufe {stufenKlasse(s.name)}"></i><span>{s.name}</span><b class="zahl">{s.zahl}</b></li>
        {/each}
      </ul>
    </Karte>

    <Karte titel="Offene Entscheidungen" icon={IconWegweiser} zusatz={offeneEntscheidungen.length} ton={offeneEntscheidungen.length ? 'signal' : 'flaeche'}>
      {#if offeneEntscheidungen.length}
        <ul class="entscheidungen">
          {#each offeneEntscheidungen as e}
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
  </div>

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

  /* ---------------------------------------------------------- Dreier */
  .dreier {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--a-5);
    margin-bottom: var(--a-7);
  }
  .grosszahl { margin-bottom: var(--a-3); font-size: var(--text-2xl); font-weight: 600; line-height: 1; letter-spacing: -0.04em; }
  .grosszahl small { font-family: var(--schrift); font-size: var(--text-s); letter-spacing: 0; color: var(--farbe-text-2); font-weight: 500; }
  .budget-zeilen { display: flex; justify-content: space-between; margin-top: var(--a-3); font-size: var(--text-s); color: var(--farbe-text-2); }
  .budget-zeilen span { display: inline-flex; align-items: center; gap: 6px; }
  .budget-zeilen b { color: var(--farbe-text); font-weight: 600; }
  .punkt { width: 8px; height: 8px; border-radius: 2px; background: var(--farbe-flaeche-hoch); box-shadow: inset 0 0 0 1px var(--farbe-linie-stark); display: inline-block; }
  .punkt.signal { background: var(--farbe-signal); box-shadow: none; }
  .fussnote { margin-top: var(--a-4); padding-top: var(--a-3); border-top: 1px dashed var(--farbe-linie); font-size: var(--text-xs); color: var(--farbe-text-2); }

  .stufenbalken { display: flex; gap: 2px; height: 10px; margin: 6px 0 var(--a-4); }
  .stufenbalken .stufe { flex-basis: 0; border-radius: 2px; min-width: 4px; }
  .stufe.s0 { background: var(--farbe-linie-stark); }
  .stufe.s1 { background: var(--farbe-info); }
  .stufe.s2 { background: var(--farbe-signal); }
  .stufe.s3 { background: color-mix(in srgb, var(--farbe-signal) 55%, var(--farbe-gut)); }
  .stufe.s4 { background: var(--farbe-gut); }
  .stufe.s5 { background: var(--farbe-text); }
  .stufen { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
  .stufen li { display: flex; align-items: center; gap: var(--a-2); font-size: var(--text-s); }
  .stufen i { width: 10px; height: 10px; border-radius: 2px; }
  .stufen b { margin-left: auto; font-weight: 600; }

  .entscheidungen { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--a-2); }
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
