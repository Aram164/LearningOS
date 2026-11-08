# Baseline-Bericht: Material-Suche in LearningOS (Stufe 1 & 2)

Datum: 2026-11-08  
Autor: Antigravity / LearningOS Pair  
Status: **Stufe 1 (Ground Truth) und Stufe 2 (Baseline) abgeschlossen — FTS5-Spike noch nicht implementiert**

---

## 1. Management Summary

Wir haben die Stufen 1 und 2 des überarbeiteten Plans zur Evaluierung einer Materialsuche in LearningOS umgesetzt. Vor dem Bau jeglicher FTS5-Infrastruktur wurden zwei getrennte, empirische Vergleichs-Arme gegen einen verifizierten, 37 Fragen umfassenden Fragenkatalog gemessen:

1. **Baseline A (Heutiger offizieller LearningOS-Workflow)**: `material.context` $\to$ Routen-/Locator-Inspektion $\to$ `material.span --extract`.
2. **Baseline B (Direkte lexikalische Suche über `generated/text-cache/`)**: Naive Dateisuche ohne SQLite über 72.199 extrahierte Seiten $\to$ `material.span`-Verifikation.

### Die wichtigsten Messergebnisse

| Metrik | Baseline A (Offizieller Workflow) | Baseline B (Lexikalischer Text-Grep) | Delta / Beobachtung |
|---|---|---|---|
| **Auswertbare Fragen (Dev)** | 25 | 25 | – |
| **Nicht beantwortbare Fragen** | 2 | 2 | – |
| **Recall@1** | **0,0 %** | **20,0 %** | Baseline A findet keine exakte Seite auf Rang 1 |
| **Recall@3** | **8,0 %** | **48,0 %** | Baseline B liefert sechsmal mehr relevante Seiten in Top-3 |
| **Recall@5** | **8,0 %** | **64,0 %** | Text-Cache-Zugriff erschließt fast zwei Drittel der Evidenz |
| **MRR (Mean Reciprocal Rank)** | **0,03** | **0,35** | 11-fache Steigerung der Ranking-Position |
| **Verifizierte Evidenz-Rate** | **28,0 %** | **44,0 %** | `material.span` bestätigt Fundstellen |
| **False Source Rate (Top-1)** | **48,0 %** | **64,0 %** | Naives Wort-Zählen führt oft zu falschen Quellen |
| **Unanswerable Accuracy** | **100,0 %** | **0,0 %** | Naiver Grep findet immer Rausch-Treffer; Core verweigert sauber |
| **Ø Tool-Aufrufe / Frage** | **2,48** | **1,81** | 27 % weniger Pipeline-Aufrufe |
| **Ø Übertragene Bytes** | **9.297 B** | **1.255 B** | 86 % weniger Kontext-Ballast |
| **Median (P50) Latenz** | **1.426,7 ms** | **4.548,0 ms** | Baseline B ist durch Platten-Scans 3,2× langsamer |
| **P95 Latenz** | **3.205,0 ms** | **6.288,0 ms** | Grep über 72.199 Dateien skaliert schlecht |

---

## 2. Struktur des Evaluationskorpus (Ground Truth)

Der Korpus liegt unter `workbench/material_search_eval/` und ist in zwei Datensätze aufgeteilt:
- **`questions_dev.yaml`** (27 Fragen): Für Baseline-Messung und Spike-Entwicklung.
- **`questions_heldout.yaml`** (10 Fragen): **Zurückgehalten** für die finale Blind-Evaluation (Vermeidung von Überanpassung an FTS5).

Alle 37 Fragen wurden mit `workbench/material_search_eval/ground_truth_verifier.py` gegen den realen Datenbestand auf der Festplatte geprüft:
- **100 % der Zitate** (`evidence_quote`) sind echte, belegte Teilstrings in den extrahierten Textseiten (`generated/text-cache/<sha256>/pp-XXXX.txt`).
- **100 % der Routenverknüpfungen** existieren in `LearningOSRepo` und lösen auf exakt dieselbe Quell-SHA-256 auf.
- Keine Ground Truth wurde erfunden.

### Verteilung nach Kategorien

| Kategorie | Anzahl (Dev / Heldout) | Beispiel |
|---|---|---|
| `german_terms` | 5 / 2 | *Mittelwertsatz der Differentialrechnung*, *Vollständige Induktion* |
| `english_terms` | 5 / 2 | *Stochastic gradient descent*, *PageRank*, *Multilayer Perceptron* |
| `math_notation` | 3 / 1 | Formeln: `(1 + x)n ≥ 1 + nx`, `f ′ (x0 ) =`, `w(u, v) ≥ 0` |
| `definitions` | 3 / 1 | *Zahlenmengen N, Z, Q, R*, *Cauchy-Folgen in R*, *Kürzeste-Pfade* |
| `algorithms` | 2 / 1 | *Dijkstras Algorithmus*, *K-means clustering*, *SGDClassifier* |
| `derivations` | 2 / 1 | Beweis des Mittelwertsatzes über Hilfsfunktion $h$ (Lemma 6.11) |
| `examples` | 1 / 0 | Zahlbereichserweiterungen von $\mathbb{N}$ nach $\mathbb{Z}$ und $\mathbb{Q}$ |
| `paraphrases` | 2 / 1 | „Wie beweist man mathematische Behauptungen schrittweise?“ $\to$ Induktion |
| `unmapped` | 2 / 0 | Vorlesungsfolien ohne LearningOS-Route (`Sweep-Line`, `Data Access`) |
| `unanswerable` | 2 / 1 | *Shor-Algorithmus*, *Raft Log-Kompaktierung*, *Haskell Monad-Transformer* |

---

## 3. Analyse der Baseline-Ergebnisse

### Warum Baseline A (Official Workflow) bei Volltext versagt
1. **Funktionale Blindheit**: `material.context` durchsucht per Design ausschließlich die 29 registrierten `analysis_notes` und 63 `assessments`. Es hat **keinerlei Sicht auf die 72.199 PDF-Seiten**. Bei Fragen nach konkreten Sätzen, Definitionen oder Formeln liefert `material.context` in 100 % der Fälle `items: []`.
2. **Reine Routen-Heuristik**: Der Agent muss daher raten, welche Einheit relevant sein könnte, und die Freitext-`locator`-Strings prüfen. Nur wenn im Locator explizit Seitenzahlen stehen (z. B. `Kapitel 1, printed p. 1 (PDF p. 11)–printed p. 6 (PDF p. 16)`), kann `material.span` überhaupt Text extrahieren.
3. **Ergebnis**: Recall@1 ist **0,0 %**, Recall@3 ist **8,0 %**, und die übertragene Datenmenge ist mit **9.297 Bytes pro Anfrage** enorm, weil ganze Einheiten und Routenstrukturen geladen werden müssen.

### Was Baseline B (Lexikalischer Text-Grep) zeigt
1. **Hohes Potenzial für Evidenz-Auffindung**: Sobald der extrahierte Text der 512 PDFs direkt durchsucht wird, springt der Recall@5 von 8,0 % auf **64,0 %** und der MRR von 0,03 auf **0,35**.
2. **Warum naiver Grep trotzdem unzureichend ist**:
   - **Laufzeit-Katastrophe**: Mit **4.525 ms P50-Latenz** und Spitzen von über 6 Sekunden ist das sequentielle Lesen von 72.199 Dateien viel zu langsam für interaktive Agenten.
   - **Schlechtes Ranking (False Source Rate 64,0 %)**: Ein naives Zählen von Term-Vorkommen bevorzugt lange Dokumente, in denen Wörter wie *Gradient*, *Descent* oder *Beweis* häufiger fallen, und verdrängt die eigentliche Definitionsseite auf Rang 4 oder 5 (daher Recall@1 nur 20,0 %).
   - **Keine semantische Verweigerung**: Bei unlösbaren Fragen (z. B. *Raft-Konsensprotokoll*) findet die Wortsuche immer zufällige Treffer für Wörter wie *Protokoll*, anstatt sauber `hits: []` zu melden (Unanswerable Accuracy 0,0 %).
   - **Unicode & Ligaturen**: Komposita und diakritische Zeichen (NFC vs. NFD) führen ohne Normalisierung zu vermeidbaren Misses.

---

## 4. Konkrete Ziel-Gates für den FTS5-Spike (Stufe 3)

Aus den gemessenen Baselines leiten sich die harten Akzeptanzkriterien für einen FTS5-Spike ab:

| Kriterium | Baseline B (Ist-Zustand) | FTS5-Spike Ziel-Gate | Begründung |
|---|---|---|---|
| **Recall@3** | 48,0 % | **$\ge$ 65,0 %** | BM25-Ranking muss relevante Seiten weiter nach oben holen |
| **Recall@1** | 20,0 % | **$\ge$ 40,0 %** | Signifikante Verbesserung des direkten Treffers |
| **MRR** | 0,35 | **$\ge$ 0,50** | Mittlere Position des ersten Treffers muss unter Top-2 liegen |
| **P50 Latenz** | 4.548 ms | **$<$ 50 ms** | Invertierter Index statt 72.199 Einzelfeilen-Scans |
| **P95 Latenz** | 6.288 ms | **$<$ 150 ms** | Garantierte Reaktionszeit für Agenten-Loops |
| **False Source Rate** | 64,0 % | **$\le$ 35,0 %** | Reduzierung falscher Quellen durch IDF-Gewichtung |
| **Unanswerable Accuracy** | 0,0 % | **$\ge$ 80,0 %** | Schwellenwert / leere Treffermenge bei themenfremden Fragen |

---

## 5. Halt-Befehl per Anweisung

Per Anweisung wurde die Arbeit **nach Stufe 2 gestoppt**. 

- Es wurden **keine Änderungen an Core-Code, kanonischen Daten oder Verträgen** vorgenommen.
- Die gesamte Evaluationsumgebung liegt isoliert in `workbench/material_search_eval/`.
- Die Baseline-Daten sind reproduzierbar unter `workbench/material_search_eval/baseline_results_dev.json` dokumentiert.

**Entscheidungsvorlage für Aram**: Liegen die Ergebnisse der Baselines vor, kann nun fundiert über die Freigabe von **Stufe 3 (FTS5-Spike im Workbench)** entschieden werden.
