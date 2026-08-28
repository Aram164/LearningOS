---
description: Codex plant (read-only, xhigh), Claude fuehrt aus. Schritt 1 von plan -> execute -> review.
argument-hint: <was geplant werden soll>
allowed-tools: Bash(codex:*), Read, Grep, Glob
---

## Schritt 1 - Codex planen lassen

Fuehre genau diesen Befehl aus (Bash tool, timeout 900000):

```bash
cd "$CLAUDE_PROJECT_DIR" && codex exec \
  --sandbox read-only \
  -m gpt-5.6-sol \
  -c model_reasoning_effort="ultra" \
  -o work/codex-plan.md \
  "Du bist der PLANER. Du schreibst KEINEN Code und aenderst KEINE Dateien.

Lies zuerst AGENTS.md, dann system/OPERATOR.md. Halte dich an den dortigen
Operating Contract. Scanne das Repository NICHT rekursiv und fasse
Schwester-Repos wie Stratum/ oder Job/ nicht an.

AUFGABE: $ARGUMENTS

Liefere einen Implementierungsplan mit exakt diesen Abschnitten:
1. Verstaendnis - was hier tatsaechlich verlangt ist, in 3 Saetzen.
2. Betroffene Dateien - konkrete Pfade, jeweils mit einem Satz warum.
3. Schritte - nummeriert, jeder Schritt einzeln pruefbar.
4. Risiken - was kaputtgehen kann, und woran man es merkt.
5. Verifikation - konkrete Befehle bzw. Tests, die den Erfolg beweisen.
6. Explizit ausserhalb des Scopes.

Sei konkret. Keine Platzhalter, keine generischen Ratschlaege."
```

## Schritt 2 - Plan pruefen

Lies `work/codex-plan.md`. Bevor du irgendetwas implementierst:

- Widersprechen die Schritte dem Operating Contract in `system/OPERATOR.md`?
- Sind Dateipfade genannt, die es nicht gibt?
- Fehlt ein Verifikationsschritt?

Melde dem Nutzer jede Abweichung, die du findest. Codex hat das Repo nur lesend
gesehen, du hast den Kontext dieser Session. Der Plan ist ein Vorschlag, kein
Befehl.

## Schritt 3 - Umsetzen

Setze den Plan um, Schritt fuer Schritt. Fuehre die Verifikation aus Abschnitt 5
tatsaechlich aus.

## Schritt 4 - Review durch Codex

Wenn die Umsetzung steht, sage dem Nutzer, dass jetzt

    /codex:adversarial-review

(bzw. `/codex:review` fuer einen normalen Review) dran ist. Starte den Review
nicht selbst - der Nutzer entscheidet, ob im Vordergrund oder mit --background.
