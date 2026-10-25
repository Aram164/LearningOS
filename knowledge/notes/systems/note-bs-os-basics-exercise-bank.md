---
id: note-bs-os-basics-exercise-bank
type: note
role: exercise-bank
title: BS - Übungen zu Betriebssystemstruktur und Schutz
created: '2026-10-23'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
sources:
- source-bs-hu-prior-slides
contexts:
- workspace-bs-foundations
---

# Übungsbank: Betriebssystemstruktur und Schutz

**Quelle und Grenze:** eigene Aufgaben zum von Aram ausgewählten Foliensatz `02_structure.pdf` (HU Berlin, Mai 2006, 46 PDF-Seiten). Die Fälle prüfen dessen Grundmechanismen; historische Betriebssystembeispiele sind entsprechend datiert. Es sind keine Originalklausuraufgaben und keine Feststellung von Beherrschung. Bearbeite zuerst ohne Lösung, und begründe jede Einordnung in zwei bis vier Sätzen. Seitenangaben erlauben die gezielte Nacharbeit.

## Aufgaben

### A1. Betriebssystemaufgaben und Hardware

Ein Texteditor sieht die Ressource „Datei“. Tatsächlich teilen sich mehrere Programme ein Laufwerk. Ein Programm versucht, den Speicher eines anderen zu überschreiben. Ordne die Beobachtungen Abstraktion, Ressourcenverwaltung und Schutz zu. Ein Controller überträgt während einer CPU-Berechnung Daten zwischen Gerät und lokalem Puffer: Erkläre, weshalb dies möglich ist und wie der Controller den Abschluss melden kann. Nenne den Unterschied, den das Deck zwischen Bus und Switch hervorhebt. [Grundlage: PDF S. 3, 5–8, 14]

### A2. Unterbrechungsursache, Dispatcher und IRQL

Ordne jeweils **extern/asynchron** oder **programmbedingt/synchron** zu: (a) Ein Gerät meldet Abschluss. (b) Ein Programm führt absichtlich eine `INT`-Instruktion aus. (c) Eine ausgeführte Instruktion verursacht einen Fehler. Erkläre die Wörter Interrupt und Trap nach Seite 9 sowie den späteren Ausdruck „software generated interrupt“. Zwei Geräte teilen sich anschließend eine Unterbrechungsquelle: Wer muss die konkrete Ursache bestimmen? Welche Anforderungen maskiert eine IRQL-Schwelle von 6 bei neu eintreffenden Stufen 3, 6 und 9? Nenne zwei wiederherzustellende Zustandsbestandteile. [Grundlage: PDF S. 9–12, 24–25]

### A3. Basis und Limit: den Rand richtig prüfen

Eine MPU hat Basis 12000 und Limit 3000. Beurteile die physischen Adressen 11999, 12000, 14999 und 15000. Gib den erlaubten Bereich an und begründe beide Randfälle. Eine Mitschülerin liest 3000 als „größte erlaubte Adresse“: Zeige den Begriffsfehler und erkläre das Schutzziel gegenüber einem fremden Programm. [Grundlage: PDF S. 14, 16; Zahlen sind ein eigenes Beispiel]

### A4. Seitenabbildung: was bleibt erhalten?

Bei 1024 Byte Seitengröße wird virtuelle Adresse 2500 über eine Seitentabelle übersetzt; Seite 2 zeigt auf Rahmen 9. Bestimme Seitennummer, Versatz und physische Adresse. Zeichne den Weg `p,d → Seitentabelle → f,d`. Erkläre, warum der Versatz erhalten bleibt und weshalb die Rahmennummer nicht das Limit aus Aufgabe A3 ist. [Grundlage: PDF S. 16–18; Zahlen sind ein eigenes Beispiel]

### A5. Benutzer- und Kernelmodus unterscheiden

Ein Benutzerprogramm will unmittelbar die Adressabbildung ändern und einen Prozessor anhalten. Es kann außerdem ganz normale Recheninstruktionen ausführen. Welche Unterschiede macht das Dual-Mode-Modell? Zeichne den kontrollierten Eintritt und Rückweg, und erkläre, weshalb die Bitwerte 1/0 auf Seite 20 nicht einfach die Ringnummern auf Seite 22 sind. [Grundlage: PDF S. 20–22]

### A6. Ein Wrapper ist noch kein Kernel

Ein Benutzerprogramm ruft eine Funktion `read` auf. Der Wrapper übergibt Dienstnummer und Argumente und führt im historischen Folienmodell `int $0x80` aus. Zeichne eine Folge mit fünf bis sieben Stationen bis zur Rückkehr. Verorte Wrapper, Prüfung der Aufrufnummer, Auswahl der Serviceroutine, Parameterprüfung und Ergebnisübergabe. Reicht das Umbenennen einer gewöhnlichen Funktion in `system_read`, um privilegierte I/O-Befehle ausführen zu dürfen? [Grundlage: PDF S. 20–21, 24, 26–30]

### A7. Linux-Beispiel und Pufferparameter

Für `write(fd, buf, count)` stehen nur wenige Argumentregister zur Verfügung. Eine Entwicklerin behauptet: „Wenn `buf` im Register steht, liegen alle zu schreibenden Bytes bereits in diesem Register. Außerdem kann der Kernel jede übergebene Adresse ohne Prüfung benutzen.“ Prüfe beide Teilaussagen. Nenne die drei Parameterwege, die Rolle der beiden `copy_*_user`-Routinen und die Fehlerdarstellung des historischen libc-Beispiels. Kennzeichne, welche Details du ohne aktuelle Quelle nicht als heutige Linux-Anleitung übernehmen würdest. [Grundlage: PDF S. 24, 26–34]

### A8. Architektur anhand der wirksamen Grenze

Drei Systeme werden beschrieben: **A:** ordentlich in Quelldateien gegliedert; alle Kernelteile können sich direkt im gemeinsamen Adressraum aufrufen. **B:** Module verbergen Informationen und folgen einer Schichtenordnung. **C:** ein Dateidienst läuft als regulärer Prozess und erhält Nachrichten über den kleinen Kernel. Ordne die Architekturmodelle zu und gib je einen Vor- und Nachteil. Ein viertes System hat formale Kernel-Schnittstellen, aber Treiber und Kernel teilen denselben Adressraum: Reicht das laut Deck für einen akademisch reinen Mikrokernel? [Grundlage: PDF S. 37–44]

<details>
<summary>Lösungen und typische Verwechslungen — erst nach eigener Bearbeitung öffnen</summary>

### A1

„Datei“ ist die Abstraktion; die Verteilung des Laufwerks ist Ressourcenverwaltung; die Abwehr fremder Speicherzugriffe ist Schutz. CPU und Gerät/Controller können gleichzeitig tätig sein. Im Folienmodell läuft die Geräteübertragung über den Controllerpuffer; die CPU bewegt Daten zwischen diesem und dem Hauptspeicher. Der Controller kann einen Interrupt auslösen; manche Geräte setzen stattdessen nur ein Statusbit. Der Switch erlaubt mehrere gleichzeitige Kommunikationsvorgänge. Gemeinsame Ressourcennutzung braucht kontrollierte Befugnisse. [PDF S. 3, 5–8, 14]

### A2

a: extern/asynchroner Interrupt. b: programmbedingt/synchron, nach Seite 9 durch Trap-Instruktion ausgelöster Eintritt. c: synchroner Trap durch Fehler. „Software generated interrupt“ benennt den programmierten Eintritt; b wird dadurch nicht extern. Der Dispatcher bestimmt beziehungsweise verteilt die Ursache und ruft den passenden Gerätehandler auf. IRQL 3 und 6 werden maskiert; 9 wird durch **diese Schwelle** nicht maskiert. Register, Programmzähler, Modus und Interruptfreigabe gehören zum wiederherzustellenden Zustand. IRQL ist die Vorrangstufe und nicht dasselbe wie IRQ. [PDF S. 9–12, 24–25, 30]

### A3

11999 verboten; 12000 erlaubt; 14999 erlaubt; 15000 verboten. Der Bereich ist `12000 ≤ Adresse < 15000`, weil 3000 die Größe ist. Die größte zulässige ganzzahlige Adresse ist 14999. Außerhalb des Bereichs liegender Speicher ist geschützt, etwa Speicher anderer Programme oder des Betriebssystems. [PDF S. 14, 16]

### A4

`2500 = 2 × 1024 + 452`: Seite 2, Versatz 452, physisch `9 × 1024 + 452 = 9668`. Die Seitennummer wählt den Eintrag, dieser liefert den Rahmen. Seite und Rahmen haben dieselbe Größe; der Versatz bezeichnet dieselbe Position innerhalb dieser Einheit. Die Rahmennummer bezeichnet den Zielrahmen, während das MPU-Limit die Größe eines zulässigen physischen Bereichs ist. [PDF S. 16–18]

### A5

Adressabbildung ändern und Prozessor anhalten sind privilegierte Operationen, normale Recheninstruktionen sind im Benutzermodus möglich. Interrupt/Trap führt hardwaregestützt in den privilegierten Modus; der dargestellte Rückweg nutzt `IRET`. Das Programm darf sich diese Befugnisse nicht selbst durch eine gewöhnliche Funktion geben. Seite 20 stellt zwei Modi mit einem Bit 1/0 dar; Seite 22 zeigt vier x86-Ringe und die häufige Nutzung von Ring 3/0. Die Zahlen gehören zu verschiedenen Darstellungen. [PDF S. 20–22]

### A6

Anwendung → Benutzer-Wrapper mit Argumenten/Aufrufnummer → `INT` und privilegierter Eintritt → Kernelstack/Kontextsicherung → Nummer und Parameter prüfen, Serviceroutine auswählen und ausführen → Ergebnis bereitstellen → Kontext/Benutzerstack wiederherstellen, `IRET`, Wrapper liefert Ergebnis. Die Prüfung ist sicherheitsrelevant, weil Benutzerkode und dessen Angaben beliebig sein können. Ein Name ändert den CPU-Modus nicht. [PDF S. 20–21, 24, 26–30]

### A7

Im Register steht eine Adresse, die auf die Nutzdaten im Benutzerspeicher verweist; eine Adresse ist kein Beweis für deren Zulässigkeit. Wege: Register; Tabelle im Speicher plus Adresse im Register; Stack. `copy_from_user` kopiert aus dem Benutzerbereich, `copy_to_user` in ihn. Der historische Wrapper bildet Fehler auf −1 und `errno` ab. `int $0x80`, `_syscall*`-Makros und die genannten Kernelpfade sind als Beispiele von Mai 2006 zu behandeln. Das Deck nennt „Zero Copy“ als Wunsch, liefert hier aber kein vollständiges Verfahren. [PDF S. 24, 26–34]

### A8

A monolithisch: direkte Aufrufe/Leistung, aber geringe Fehlerisolation im Kernel. B geschichtet: Abstraktion/Zuständigkeitstrennung, aber mögliche Ineffizienz und Starrheit. C Mikrokernel: Dienste leichter isolier- und entwickelbar, aber viele Grenzübergänge. Für das vierte System reicht die formale Schnittstelle nicht: Die auf Seite 44 verwendete akademische Definition fordert getrennte Adressräume der Komponenten und Treiber. Dies ist die Begründung der dortigen NT-Einschränkung. [PDF S. 37–44]

</details>
