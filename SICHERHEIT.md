# Sicherheit

Was geschützt wird, womit, und was der Nutzer selbst einrichten muss.

## Lage

Das Repo war öffentlich. Damit lagen nicht nur die Website, sondern Vault,
CSVs und alle Medien offen auf github.com. Ein Passwort vor der Website hätte
daran nichts geändert — der erste Schritt ist deshalb immer „Repo privat".

## Von Hand einzurichten

Diese vier Schritte kann nur der Nutzer machen, sie brauchen Konto- und
Adminrechte.

### 1. Repo auf privat stellen

github.com/xaver-lab/VanMaster → Settings → unten „Danger Zone" →
*Change repository visibility* → Private.

Damit hört GitHub Pages auf zu bauen (Pages aus privaten Repos setzt GitHub
Pro voraus). Das ist gewollt — Cloudflare übernimmt.

### 2. Cloudflare Pages anlegen

1. Konto auf dash.cloudflare.com anlegen (kostenlos).
2. Workers & Pages → Create → Pages → *Direct Upload*, Projektname
   `vanmaster`. Der Name muss zu `--project-name=vanmaster` in
   `.github/workflows/cloudflare.yml` passen.
3. API-Token: My Profile → API Tokens → Create Token → Vorlage
   *Edit Cloudflare Workers*, oder ein eigenes mit der Berechtigung
   `Account → Cloudflare Pages → Edit`.
4. Account-ID steht rechts im Dashboard.

### 3. Secrets in GitHub hinterlegen

Repo → Settings → Secrets and variables → Actions →
New repository secret:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Vorher fährt der Workflow absichtlich ins Leere statt rot zu laufen.
Die Tokens gehören **nur** hierhin, nie ins Repo.

### 4. Cloudflare Access davorsetzen

Zero Trust → Access → Applications → Add an application → Self-hosted,
Domain `vanmaster.pages.dev`. Policy: *Allow*, Include → Emails →
die eigene Adresse. Login läuft dann über einen Einmalcode per Mail.
Kostenlos bis 50 Nutzer.

Ohne diesen Schritt ist die Cloudflare-Seite öffentlich erreichbar, nur unter
anderer Adresse. Access ist der eigentliche Schutz.

### Optional: Branch-Schutz

Repo → Settings → Rules → Rulesets → `main` schützen, „Require a pull
request before merging". Das ist die einzige *harte* Grenze gegen
versehentliche Code-Pushes; die Push-Wache unten ist nur ein Geländer.

Danach kann `.github/workflows/pages.yml` weg.

## Was im Repo schon eingebaut ist

### Geheimnis-Wache

`tools/geheim.py` sucht nach Zugangsdaten, Bankverbindungen, Fahrzeug- und
Personendaten. Muster und Schweregrade stehen dort.

    python camper.py geheim            # alle versionierten Dateien
    python camper.py geheim --staged   # nur was zum Commit vorgemerkt ist

`.githooks/pre-commit` fährt den zweiten Aufruf bei jedem Commit und bricht
bei einem Fund ab. Aktiv, sobald einmal

    git config core.hooksPath .githooks

gelaufen ist — der SessionStart-Hook in `.claude/settings.json` setzt das in
jeder Claude-Sitzung selbst. Notausgang: `git commit --no-verify`.
Falscher Alarm: `geheim-ok` in die Zeile schreiben.

### Push-Wache

`.claude/hooks/push_wache.py` hängt als PreToolUse-Hook an der Bash-Nutzung
und stoppt einen Push, der auf den Website-Branch zielt und Code mitbringt.
Daten (`vault/`, `data/`) gehen durch, und ein Push auf einen eigenen Branch
geht immer durch — der Branch ist der Weg, auf dem Code zur Sichtung kommt.
Die Regel dazu steht in `CLAUDE.md`.

Geprüft wird der rohe Befehlstext. Ein Befehl, der die Wortfolge nur
erwähnt — etwa ein Skript, das sie in einen String schreibt —, wird deshalb
mitgeprüft und kann fälschlich anschlagen. Lieber einmal zu viel.

Das ist ein Geländer gegen automatisches Durchpushen, **keine
Sicherheitsgrenze**: wer den Befehl schreibt, kann sie mit
`VANMASTER_CODE_PUSH=1` davor auch öffnen. Die harte Grenze ist der
Branch-Schutz oben.

## Wenn doch etwas rausgerutscht ist

Löschen reicht nicht — die Historie bleibt, und bei einem öffentlichen Repo
ist alles längst geklont und indiziert.

1. Das Geheimnis **zurückziehen**: Token löschen, Passwort ändern.
2. Erst danach aufräumen (`git filter-repo` oder neuer Verlauf).

Schritt 1 ist der wichtige. Schritt 2 allein hilft nicht.
