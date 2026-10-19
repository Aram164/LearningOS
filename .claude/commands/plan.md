---
description: Frontier-Runde, dann plant Codex (read-only), dann setze ich um.
argument-hint: [--fast|--model <name>] <was geplant werden soll>
disable-model-invocation: true
allowed-tools: Bash(codex:*), Read, Grep, Glob
---

## Schritt 0 - Frontier-Runde

`codex exec` ist nicht interaktiv und kann Aram nichts fragen. Das Befragen ist
deine Aufgabe, hier, bevor der teure Call rausgeht.

Wenn die Aufgabe ungeklaerte Entscheidungen enthaelt, stelle eine Runde:

- **Alle** Fragen, deren Voraussetzungen bereits geklaert sind - auf einmal.
- Nie zwei Fragen in einer Runde, wenn eine von der anderen abhaengt. Was von
  einer offenen Antwort abhaengt, gehoert in eine spaetere Runde.
- Nummeriert, jede mit deiner Empfehlung auf einer eigenen Zeile, damit Aram
  per Nummer antworten kann.
- **Fakten schlaegst du selbst nach.** Was das Repo beantworten kann - existiert
  eine Datei, wie heisst ein Feld, was tut ein Kommando - liest du, statt zu
  fragen.
- **Entscheidungen beantwortest du nicht selbst.** Warte darauf.

Weitere Runden, bis nichts mehr offen ist. Ist die Aufgabe eindeutig, sag das
und ueberspringe den Schritt.

## Schritt 1 - Codex beauftragen

Modellwahl aus dem Argument, bevor du den Befehl baust:

| Argument beginnt mit | Modell | Effort |
| --- | --- | --- |
| nichts davon (Default) | `gpt-5.6-sol` | `ultra` |
| `--fast` | `gpt-5.6-terra` | `high` |
| `--model <name>` | `<name>` | `high` |

`--fast` ist fuer kleine, klar umrissene Aufgaben. Aram laeuft mit dem Default
regelmaessig in seine Codex-Limits; wenn eine Aufgabe offensichtlich klein ist,
weise ihn einmal auf `--fast` hin, entscheide aber nicht fuer ihn.

Entferne das Flag aus der Aufgabenbeschreibung, trage die geklaerten
Entscheidungen ein, dann (Bash, timeout 900000):

```bash
cd "${CLAUDE_PROJECT_DIR}" && codex exec \
  --sandbox read-only \
  -m <MODELL> \
  -c model_reasoning_effort="<EFFORT>" \
  -o /tmp/codex-plan.md \
  "Du bist der PLANER. Du schreibst KEINEN Code und aenderst KEINE Dateien.

Lies zuerst AGENTS.md, dann system/OPERATOR.md. Halte dich an den dortigen
Operating Contract. Scanne das Repository NICHT rekursiv und fasse
Schwester-Repos wie Stratum/ oder legacy/ nicht an.

AUFGABE: <Aufgabe ohne Flag>

BEREITS ENTSCHIEDEN (nicht neu aufrollen):
<Antworten aus Schritt 0, oder 'nichts vorab geklaert'>

Liefere einen Implementierungsplan mit exakt diesen Abschnitten:
1. Verstaendnis - was hier verlangt ist, in 3 Saetzen.
2. Betroffene Dateien - konkrete Pfade, jeweils mit einem Satz warum.
3. Schritte - nummeriert, jeder Schritt einzeln pruefbar.
4. Risiken - was kaputtgehen kann, und woran man es merkt.
5. Verifikation - konkrete Befehle bzw. Tests, die den Erfolg beweisen.
6. Explizit ausserhalb des Scopes.

Markiere jede Aussage, die du nicht im Repo verifiziert hast, als ANNAHME.
Eine ungepruefte Vermutung, die wie eine Tatsache dasteht, wird vom Executor
als Vertrag gelesen und nicht nachgeprueft."
```

Der Plan liegt bewusst unter `/tmp`, nicht im Repo: er ist Transitware, die du
einmal liest, kein Artefakt. `work/` ist getrackt und hat eine eigene Struktur
(`COORDINATION.md`, `active/<workspace>/`, `inbox/`); ein loser Planentwurf
gehoert dort nicht hin. Will Aram einen Plan behalten, kopierst du ihn nach
`work/active/<workspace>/inputs/`.

## Schritt 2 - Plan pruefen

Lies `/tmp/codex-plan.md`. Vor jeder Umsetzung:

- Widerspricht ein Schritt `system/OPERATOR.md`?
- Sind Pfade genannt, die es nicht gibt?
- Fehlt die Verifikation?
- **Steht irgendwo eine Behauptung ueber den Repo-Zustand, die nicht als
  ANNAHME markiert ist und die du nicht selbst gesehen hast?** Pruefe sie nach,
  bevor du darauf baust. Codex hat kalt gelesen; du hast den Sitzungskontext.

Melde Aram jede Abweichung. Der Plan ist ein Vorschlag, kein Befehl.

## Schritt 3 - Umsetzen

Schritt fuer Schritt. Fuehre die Verifikation aus Abschnitt 5 tatsaechlich aus.

## Schritt 4 - Review

Wenn es steht, sag Aram, dass `/codex:adversarial-review` dran ist. Starte ihn
nicht selbst - er entscheidet ueber Vordergrund oder `--background`.
