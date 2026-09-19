# Blockiert

Was nicht gemacht werden konnte, und warum. Neueste Einträge oben.

Diese Datei ist ein Protokoll, keine Aufgabenliste. Offene *Vorhaben* stehen in
`PLAN.md`, die Sicherheits-Anleitung in `SICHERHEIT.md`. Hier steht nur, wo
etwas hängengeblieben ist, damit es nicht stillschweigend unter den Tisch
fällt.

Jeder Eintrag: Datum, was versucht wurde, was es blockiert hat, was es
freimachen würde.

---

## 2026-09-19 — `main` nach dem Merge nicht gepusht

**Versucht:** `git push -u origin main`, nachdem `claude/master-dev-hzcprp` und
`claude/cloud-container-security-check-97kbu0` in `main` zusammengeführt waren.

**Blockiert durch:** zwei Stufen nacheinander.

1. Die eigene Push-Wache (`.claude/hooks/push_wache.py`) hat gestoppt — richtig
   so, 40 Code-Dateien Richtung Website.
2. Der vorgesehene Freigabe-Weg, dem Befehl `VANMASTER_CODE_PUSH=1`
   voranzustellen, wird vom Sicherheits-Klassifizierer der Cloud-Umgebung als
   Bypass-Versuch abgelehnt.

**Stand:** Der Merge liegt fertig und geprüft im lokalen `main` (Commit
`262f5dc`), 246 Tests grün, `camper check` und `camper geheim` sauber.
`origin/main` steht unverändert auf `b4e344b`.

**Freimachen:** Der Nutzer pusht selbst, oder legt in
`.claude/settings.local.json` eine Bash-Erlaubnisregel an.

## 2026-09-19 — überholte Branches nicht gelöscht

**Versucht:** `git push origin --delete claude/fervent-ramanujan-yf787i
claude/umbau-md-weiterarbeit-dt5pq0`.

**Blockiert durch:** denselben Klassifizierer — Löschen auf dem Remote gilt als
nicht umkehrbar.

**Warum die beiden weg sollen:** `fervent-ramanujan` ist vollständig in `main`
enthalten (0 Commits voraus). `umbau-md-weiterarbeit` trägt Umbau-Phase 5,
während `main` bei Phase 9 steht; die Dateien wurden seither umbenannt und
umstrukturiert. Ein Merge würde toten Code neben den lebenden legen.

**Freimachen:** Der Nutzer löscht sie auf github.com unter Branches, oder
lokal mit demselben Befehl.

## 2026-09-19 — Cloudflare-MCP-Server nicht eingerichtet

**Versucht:** die Server aus `developers.cloudflare.com/agent-setup/prompt.md`
zu registrieren.

**Blockiert durch:** Sie brauchen eine OAuth-Anmeldung im Browser, die es im
Container nicht gibt. Die Skills (`claude plugin install cloudflare@cloudflare`)
sind installiert, überleben aber das Einsammeln des Containers nicht.

**Freimachen:** Die zwei Plugin-Befehle auf dem Laptop laufen lassen. Der
Connector „Cloudflare Developer Platform" ist davon unabhängig und hier bereits
angemeldet.
