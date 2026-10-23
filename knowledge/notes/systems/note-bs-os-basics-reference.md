---
id: note-bs-os-basics-reference
type: note
role: reference
title: 'BS - Betriebssystemgrundlagen: Referenz zum älteren Foliensatz'
created: '2026-10-23'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  source_id: source-bs-hu-prior-slides
  material: data-systems/architecture/bs-hu-prior-slides/02_structure.pdf
  recorded_source_digest: b82d9c9e6652bffcef034e405f740615a5134011457fd1fef7fc1a93dfdbd9bf
  live_source_digest: b82d9c9e6652bffcef034e405f740615a5134011457fd1fef7fc1a93dfdbd9bf
  inspected_range:
    start: 1
    end: 46
  frozen_input_sha256: 3096815f13a72bb09848932233a1b4c1d13bcf6838a2849ba96b836b5112d831
  frozen_input_bytes: 9199
---

# Betriebssystemgrundlagen: Architektur, Schutz und Systemaufrufe

**Arbeitsgrundlage:** `02_structure.pdf`, HU Berlin, Mai 2006, 46 PDF-Seiten. Diese Referenz erschließt den von Aram ausgewählten älteren Foliensatz. Historische Beispiele beschreiben den Stand beziehungsweise das Lehrmodell der Folien; sie belegen weder den heutigen Implementierungsstand noch den aktuellen Prüfungsumfang. Alle Seitenangaben beziehen sich auf die PDF-Seiten. Es ist kein Lernstand festgestellt.

## 1. Was ein Betriebssystem vermittelt

Das Betriebssystem liegt zwischen Anwendungen und Hardware. Seine drei verbundenen Aufgaben sind **Abstraktionen**, **Ressourcenverwaltung** und **Schutz einschließlich kontrollierter gemeinsamer Nutzung**. Eine Anwendung soll mit brauchbaren virtuellen Ressourcen arbeiten können, während das Betriebssystem die tatsächlichen Ressourcen auf mehrere Programme beziehungsweise Benutzer verteilt. Schutz verhindert, dass ein fehlerhaftes Programm die Ausführung anderer Programme oder das Betriebssystem selbst beschädigt. Das ist mehr als eine komfortable Funktionsbibliothek: Wer Ressourcen teilen will, muss ihre Nutzung begrenzen können. [PDF S. 3, 14]

Die Hardwaredarstellung beginnt mit CPU, Speicher, Bus und Controllern für Ein-/Ausgabegeräte. Ein Controller bedient einen Gerätetyp und besitzt einen lokalen Puffer. Im dargestellten Modell bewegt die CPU Daten zwischen Hauptspeicher und Controllerpuffer; die eigentliche Geräteübertragung liegt zwischen Gerät und Puffer. CPU-Arbeit und Ein-/Ausgabe können sich zeitlich überlappen. Die Folien stellen dem gemeinsamen Bus einen Switch gegenüber, der mehrere gleichzeitige Kommunikationsvorgänge ermöglicht. **Gleichzeitige Aktivität** der Komponenten bedeutet daher nicht, dass alle Arbeiten auf derselben CPU ausgeführt werden. [PDF S. 5–7]

## 2. Unterbrechung: Ursache, Auswahl und Bearbeitung

Ein **Interrupt** entsteht nach der Begriffsabgrenzung auf Seite 9 asynchron durch ein externes Ereignis, etwa eine abgeschlossene Geräteoperation. Ein **Trap** entsteht synchron zur Programmausführung, durch einen Fehler oder eine besondere Trap-Instruktion. Entscheidend ist die Beziehung zum gerade ausgeführten Programm: Eine Gerätefertigmeldung ist unabhängig davon; ein absichtlich ausgeführtes `INT` gehört zu dessen Instruktionsfolge. Die späteren Folien nennen `INT` zugleich „software generated interrupt beziehungsweise programmed interrupt“. Diese Bezeichnung hebt die frühere synchron/asynchron-Unterscheidung nicht auf. [PDF S. 7–9, 23–25, 30]

Der **Interruptvektor** enthält Adressen der Serviceroutinen; er ist keine Liste wartender Aufträge. Bei einer Unterbrechung werden Register und Programmzähler gesichert, damit die unterbrochene Ausführung wiederhergestellt werden kann. Die Ursache wird über Statusinformationen oder einen vektorisierten Mechanismus bestimmt. Der gezeigte **Dispatcher/Interrupt Service Routine** sichert den Maschinenzustand und ruft den passenden **Handler** auf. Dieser bearbeitet das konkrete Gerät, etwa indem er dessen Unterbrechungsanforderung beendet oder die nächste Operation startet. Mehrere Geräte können sich eine Unterbrechung teilen. Abschließend wird der Zustand einschließlich Modus und Interruptfreigabe wiederhergestellt. [PDF S. 9–11]

**IRQ und IRQL sind verschiedene Begriffe.** Das IRQL ist im gezeigten Modell die Vorrangstufe und Teil des Prozessorzustands. Während der Bearbeitung steigt es auf die Stufe der jeweiligen Unterbrechung: Anforderungen gleicher und niedrigerer Stufe werden maskiert. Daraus folgt nicht, dass jede höher eingestufte Anforderung ebenfalls maskiert ist. Benutzermodus ist hier auf IRQL 0 begrenzt. Die konkrete Tabelle mit Stufen bis 31 ist das historische Beispiel der Folie, keine universelle Nummerierung für jedes Betriebssystem. [PDF S. 12]

## 3. Speicher schützen und Adressen übersetzen

Die einfache **MPU** nutzt Basis und Limit: Die Basis ist die kleinste erlaubte physische Adresse, das Limit die **Größe** des Bereichs. Bei Basis 300040 und Größe 120900 reicht der Bereich im Folienbeispiel von 300040 bis unmittelbar vor 420940. Das Limit ist weder die größte Adresse noch automatisch eine virtuelle Seitennummer. [PDF S. 16]

Die **MMU** fügt eine Übersetzungsebene hinzu. Die CPU liefert bei einem Lade-/Speicherzugriff eine virtuelle Adresse; die MMU bildet sie auf eine physische Adresse ab. Das trennt die im Programm verwendete Adresse vom tatsächlichen Speicherort. Die Seitenabbildung zerlegt die logische Adresse in Seitennummer **p** und Versatz **d**. **p** wählt den Eintrag der Seitentabelle; dieser liefert den physischen Rahmen **f**. Die physische Adresse besteht aus **f** und demselben **d**. Seiten und Rahmen haben dafür dieselbe Größe, beispielsweise 4 KiB. Verschoben wird die Zuordnung der ganzen Seite, nicht die Position eines Bytes innerhalb der Seite. [PDF S. 17–18]

Rechenbeispiel zur Abbildung: Bei 4096 Byte Seitengröße hat virtuelle Adresse 9230 die Seitennummer 2 und den Versatz 1038. Steht im Eintrag 2 der Rahmen 7, lautet die physische Adresse `7 × 4096 + 1038 = 29710`. Die Zahlen sind ein eigenes Übungsbeispiel. Das Deck erklärt an dieser Stelle weder Seitenfehlerbehandlung noch Auslagerungsalgorithmen oder einen vollständigen Aufbau von Zugriffsrechten in Seitentabellen. [PDF S. 18]

## 4. Privilegien und der kontrollierte Eintritt in den Kernel

Das Dual-Mode-Modell unterscheidet Benutzer- und privilegierten Modus. Ein Modusbit gehört zum CPU-Zustand; Interrupt oder Fehler führen hardwaregestützt in den privilegierten Modus. Bestimmte Operationen sind dort erlaubt, etwa Adressabbildungen ändern, Systemregister laden oder Ein-/Ausgabe ausführen. Ein Benutzerprogramm erhält diese Befugnisse nicht dadurch, dass es eine gewöhnliche Funktion passend benennt. Der gezeigte Rückweg nutzt `IRET`. Die Bitwerte 1/0 im Dual-Mode-Modell und die x86-Ringe 3/0 sind unterschiedliche Darstellungen; die Folien sagen, dass viele Systeme vor allem Ring 0 und 3 nutzen. [PDF S. 20–22]

Ein **Systemaufruf** ist eine kontrollierte Anforderung eines Prozesses an das Betriebssystem. Die historische x86/Linux-Darstellung zeigt: Ein Bibliotheks-Wrapper legt Aufrufnummer und Argumente in Register, führt `int $0x80` aus und übernimmt später das Ergebnis. Am Eintritt werden Kernelstack und Kontext gesichert beziehungsweise gewechselt, die Nummer geprüft und die passende Kernelroutine ausgewählt. Parameter sind vor der Ausführung zu prüfen. Nach Bearbeitung folgen Ergebnisübergabe und Wiederherstellung des Benutzerkontexts. Wrapper, Dispatcher und eigentliche Serviceroutine sind damit drei verschiedene Aufgaben. Ein gewöhnlicher Bibliotheksaufruf muss dagegen keinen solchen Eintritt auslösen. [PDF S. 24, 26–31, 35–36]

Parameter können in Registern, über eine Speicherstruktur samt Adresse oder über einen Stack übergeben werden. Ein Register mit einer Pufferadresse enthält **den Verweis**, nicht den ganzen Puffer. Die Folien zeigen dafür `copy_from_user` und `copy_to_user`; eine beliebige Benutzeradresse ist kein automatisch vertrauenswürdiger Kernelzeiger. Begrenzte Registeranzahl, mehrere Resultate und Fehlerrückgabe sind eigene Schnittstellenfragen. Das historische libc-Beispiel bildet einen Fehler auf Rückgabewert −1 und `errno` ab. Die alten Makros, Pfade und Interruptnummern dienen dem Verständnis des Mechanismus, nicht als heutige Implementierungsanleitung. [PDF S. 26–34]

## 5. Die Laufzeitstruktur entscheidet über Grenzen

**Monolithisch:** Quellcode kann gut organisiert sein, obwohl Kernelprozeduren sich zur Laufzeit unmittelbar aufrufen und keine erzwungenen Schutzgrenzen zwischen ihnen bestehen. Das begünstigt direkte Zusammenarbeit und Leistung; Fehler können sich im gemeinsamen Kernelraum auswirken. **Geschichtet:** Jede Schicht verbirgt Information und folgt einer Abhängigkeitsordnung. Das erleichtert Abstraktion und Zuständigkeitstrennung, kann aber zusätzliche Wege und starre Abhängigkeiten erzeugen. Die MS-DOS-Abbildung zeigt sogar Pfeile, die Schichten überspringen: Ein gezeichnetes Schichtenbild allein beweist keine streng erzwungene Grenze. [PDF S. 37–40]

**Mikrokernel:** Dienste laufen als reguläre Prozesse und kommunizieren über Nachrichten. Getrennte Adressräume unterstützen Fehlerisolation und Anpassbarkeit, erzeugen aber Grenzübergänge. Ein Dienst außerhalb des Kernels kann weiterhin Betriebssystemdienst sein. Windows NT wird im Deck ausdrücklich **nicht** als akademisch reiner Mikrokernel eingeordnet: Kernelkomponenten und Treiber teilen einen Adressraum. Formale Schnittstellen und Benutzerprozesse für Betriebssystempersönlichkeiten motivieren hier die Bezeichnung „modified microkernel“. Die Abbildungen auf Seiten 42–43 und die Einschränkung auf Seite 44 müssen gemeinsam gelesen werden. [PDF S. 36, 41–44]

**Offene Deckgrenze:** „DMA“ sowie synchrone/asynchrone Ein-/Ausgabe stehen im Vokabelanhang, werden aber in diesem Satz nicht als eigene Mechanismen ausgearbeitet. Diese Referenz behauptet dafür keine ausreichende Behandlung. [PDF S. 46]
