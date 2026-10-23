---
id: note-bs-os-basics-self-test
type: note
role: mock-exam
title: 'BS - Selbsttest: Betriebssystemgrundlagen und Struktur'
created: '2026-10-23'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
sources:
- source-bs-hu-prior-slides
contexts:
- workspace-bs-foundations
---

# Selbsttest: Betriebssystemgrundlagen und Struktur

**Dauer:** 35 Minuten. **Umfang:** 30 Punkte, fünf eigene Transferfälle. Bearbeite die Aufgaben ohne Folien und öffne die Lösungen erst nach der Zeit. Erlaubt sind Papier und ein einfacher Taschenrechner. Notiere zu jeder Antwort die Begründung; bloße Schlagwörter erhalten nur die dafür ausgewiesenen Punkte.

**Geltungsbereich:** ausschließlich `02_structure.pdf` (HU Berlin, Mai 2006, 46 PDF-Seiten), von Aram als älteres Studienmaterial ausgewählt. Die Aufgaben sind neu formuliert und keine Originalprüfung. Ohne aktuelle Prüfungsaufgaben, offiziellen Prüfungsumfang und Zeitvergleich ist dieser Test **kein nachgewiesenes Äquivalent einer echten Klausur**. Ein Ergebnis beschreibt nur die Bearbeitung dieses Tests und erklärt weder Beherrschung noch Prüfungsreife.

## Aufgabenblatt

### Fall 1 — Zwei Wege in denselben privilegierten Bereich (6 Punkte, 7 Minuten)

Während Programm P eine Rechenfunktion ausführt, meldet eine Netzwerkkarte den Abschluss einer Übertragung. Später führt P bewusst eine besondere Instruktion aus, um einen Betriebssystemdienst anzufordern.

1. Unterscheide die Ursachen nach Synchronität und Herkunft. Verwende dabei die Begriffe von Seite 9 und erkläre, warum spätere Folien beide Eintrittswege mit dem Wort „Interrupt“ beschreiben können. (3 P)
2. Nenne zwei zu sichernde Bestandteile des CPU-Zustands. (1 P)
3. Begründe den Wechsel in den privilegierten Modus und erkläre, warum der spätere Rückweg den ursprünglichen Zustand wiederherstellen muss. (2 P)

### Fall 2 — Eine harmlose Bibliotheksfunktion? (7 Punkte, 8 Minuten)

Eine Bibliothek bietet `send_note(fd, ptr, length)` an. Ihr Wrapper stellt eine Dienstnummer bereit und nutzt im historischen Folienmodell `int $0x80`. Eine fremde Anwendung kann `ptr` und `length` frei wählen. Eine Entwicklerin schlägt vor, die Dienstnummer ungeprüft als Zieladresse zu behandeln und sämtliche Nutzdaten aus Argumentregistern zu lesen.

1. Beschreibe den Weg vom Wrapper über den Kerneleintritt bis zur ausgewählten Serviceroutine und zurück. Nenne dabei den Kernelstack und die Ergebnisübergabe. (3 P)
2. Erkläre die beiden Fehler des Vorschlags und den richtigen Umgang mit Pufferdaten auf dem Abstraktionsniveau des Decks. (3 P)
3. Muss jede gewöhnliche Bibliotheksfunktion einen Systemaufruf auslösen? Begründe. (1 P)

### Fall 3 — Dieselbe Adresse, zwei Modelle (6 Punkte, 7 Minuten)

**Maschine A** erlaubt einem Programm im MPU-Modell einen physischen Bereich mit Basis 48000 und Limit 2048. **Maschine B** nutzt Seiten von 2048 Byte. Dort zeigt Seitentabelleneintrag 5 auf Rahmen 12; P greift auf virtuelle Adresse 10757 zu.

1. Prüfe für A die Adressen 47999, 48000, 50047 und 50048. Gib den zulässigen Bereich an. (2 P)
2. Berechne für B Seitennummer, Versatz und physische Adresse. Zeige den Rechenweg. (3 P)
3. Erkläre in einem Satz, weshalb eine virtuelle Adresse nicht einfach die tatsächliche RAM-Adresse sein muss. (1 P)

### Fall 4 — Vorrang und Gerätezuordnung (5 Punkte, 6 Minuten)

Ein Dispatcher bearbeitet eine Geräteanforderung auf IRQL 5. Die Geräte U und V teilen sich die Unterbrechungsquelle. Gleichzeitig werden Anforderungen der Stufen 2, 5 und 8 ausgelöst. Ein Entwickler will deshalb jedem Gerät automatisch eine eigene IRQL-Zahl zuweisen und jeden Gerätehandler auslassen, sobald der Dispatcher erreicht wurde.

1. Welche der drei Anforderungen maskiert die auf 5 angehobene IRQL-Schwelle? Welche Aussage lässt sie über Stufe 8 zu? (2 P)
2. Warum sind IRQL, Unterbrechungsquelle und Geräteidentität hier nicht austauschbar? (1 P)
3. Nenne je eine Aufgabe des Dispatchers und des Gerätehandlers. (2 P)

### Fall 5 — Ein Etikett für einen Kernel (6 Punkte, 7 Minuten)

System R besitzt einen kleinen Nachrichtenkern. Der Dateidienst und der Druckdienst laufen in eigenen Prozessen. System S hat sorgfältig dokumentierte Schnittstellen und viele getrennte Quellmodule; seine Treiber und übrigen Kernelkomponenten teilen jedoch einen Adressraum und können sich direkt aufrufen.

1. Welches Strukturmodell passt zu R? Begründe anhand einer wirksamen Laufzeitgrenze und nenne einen Nutzen sowie einen Preis. (3 P)
2. Belegt die Beschreibung von S einen akademisch reinen Mikrokernel? Begründe mit dem Kriterium, das die Folien bei Windows NT verwenden. (2 P)
3. Was würde eine Schichtenordnung zusätzlich über die Abhängigkeiten aussagen, das allein aus getrennten Quelldateien nicht folgt? (1 P)

<details>
<summary>Bewertungsraster, Musterantworten und gezielte Nacharbeit</summary>

## Fall 1 — 6 Punkte

1. Netzwerkkarte: extern und asynchron (1 P); absichtliche Instruktion: programmbedingt und synchron, nach Seite 9 Trap-Instruktion (1 P); „software generated interrupt beziehungsweise programmed interrupt“ benennt auf den späteren Folien den programmierten Eintritt, ohne ihn zu einem externen Ereignis zu machen (1 P). [PDF S. 7–9, 23–25, 30]
2. Register und Programmzähler, zusammen 1 P; zwei passende konkrete Bestandteile genügen. [PDF S. 10–11]
3. Der privilegierte Bereich ermöglicht die geschützte Betriebssystembearbeitung (1 P). Zur korrekten Fortsetzung sind Kontext und ursprünglicher Modus/Interruptzustand wiederherzustellen (1 P). Eine Aussage wie „P darf nun beliebige Kernelbefehle ausführen“ erhält diesen Punkt nicht. [PDF S. 10–11, 20–21]

## Fall 2 — 7 Punkte

1. Wrapper setzt Nummer/Argumente und löst Eintritt aus (1 P); Kernelstack/Kontext sichern, Aufruf prüfen und passende Serviceroutine auswählen (1 P); Ergebnis bereitstellen, Kontext/Benutzerstack wiederherstellen und zurückkehren (1 P). [PDF S. 24, 26–30]
2. Eine benutzerbestimmte Nummer ist zu prüfen und bezeichnet die Auswahl über die Dispatchtabelle, keine beliebig vertrauenswürdige Zieladresse (1 P). `ptr` ist ein Verweis; ein Register enthält nicht den gesamten Puffer (1 P). Adresse/Länge müssen geprüft werden; die Folien zeigen Kopieren zwischen Benutzer- und Kernelbereich mit `copy_from_user`/`copy_to_user` (1 P). [PDF S. 24, 27, 30, 32–33]
3. Nein: Bibliothekskode kann vollständig im Benutzermodus arbeiten; der besondere Eintritt ist nötig, wenn ein entsprechender Kernelservice angefordert wird (1 P). [PDF S. 35–36]

## Fall 3 — 6 Punkte

1. Bereich `48000 ≤ Adresse < 50048` (1 P); damit verboten, erlaubt, erlaubt, verboten in der gegebenen Reihenfolge (1 P). Das Limit 2048 ist die Größe. [PDF S. 16]
2. `10757 = 5 × 2048 + 517`: Seite 5 (1 P), Versatz 517 (1 P), physisch `12 × 2048 + 517 = 25093` (1 P). Bei einem reinen Rechenfehler kann ein korrekt dargestellter Mechanismus die übrigen Teilpunkte behalten. [PDF S. 17–18]
3. Die MMU übersetzt die vom Programm verwendete virtuelle Adresse anhand einer Zuordnung in eine physische Adresse (1 P). [PDF S. 17]

## Fall 4 — 5 Punkte

1. Die Anforderungen auf 2 und 5 werden maskiert (1 P); 8 liegt oberhalb der Schwelle und wird durch **diese Schwelle** nicht maskiert (1 P). Das Deck begründet damit keine vollständige Garantie des tatsächlichen Ausführungszeitpunkts. [PDF S. 12]
2. IRQL ist eine Vorrangstufe; eine Quelle kann geteilt sein und identifiziert daher nicht notwendig ein einzelnes Gerät (1 P). [PDF S. 11–12]
3. Dispatcher: Maschinenzustand sichern, Ursache verteilen oder passenden Handler aufrufen (eine davon, 1 P). Gerätehandler: Gerät prüfen, Unterbrechungsanforderung beenden oder nächste Geräteoperation starten (eine davon, 1 P). [PDF S. 10–11]

## Fall 5 — 6 Punkte

1. R entspricht dem Mikrokernelmodell: Dienstprozesse und Nachrichten statt aller Dienste im gemeinsamen Kernelraum (1 P); Nutzen etwa Fehlerisolation/leichter entwickelbare Dienste (1 P); Preis zusätzliche Grenzübergänge (1 P). [PDF S. 41]
2. Nein (1 P). Dokumentierte Schnittstellen schaffen keine getrennten privaten Adressräume der Komponenten und Treiber; dieses Kriterium verwendet die NT-Einschränkung (1 P). [PDF S. 44]
3. Eine Schichtenordnung legt gerichtete Abhängigkeiten und Informationsverbergung zwischen Ebenen fest; die bloße Aufteilung der Quellen tut das nicht (1 P). [PDF S. 37–40]

## Auswertung ohne Statusbehauptung

Notiere Punkte **pro Fall** und markiere jeden unsicheren Teil: Begriff verwechselt, Mechanismus fehlt, Rechnung fehlerhaft oder Begründung fehlt. Ein Gesamtergebnis allein versteckt gezielte Lücken. Wiederhole nur die fehlenden Teile mit einer abgeänderten eigenen Situation; ein direktes Abschreiben der Musterantwort ist keine unabhängige Evidenz.

- Fall 1: Ursache und Zustand auf PDF S. 9–12, 20 prüfen.
- Fall 2: Ablauf und Parameter auf PDF S. 24, 26–33 prüfen.
- Fall 3: beide Modelle auf PDF S. 16–18 nebeneinander zeichnen.
- Fall 4: Rollen und IRQL-Schwelle auf PDF S. 10–12 prüfen.
- Fall 5: Laufzeitgrenzen und NT-Einschränkung auf PDF S. 37–44 prüfen.

Die Punktzahl kann später als konkrete Bearbeitungsevidenz festgehalten werden. Hier wird kein Ergebnis vorweggenommen und kein Lernstatus verändert.

</details>
