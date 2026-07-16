# MASTERS-HANDOFF — Masters-Planning Brain

> **Created:** 2026-06-11 · **Purpose:** Eine frische Session liest diese Datei zuerst, dann `MASTERS-STATUS.md`. Analog zu `semestercontext/HANDOFF.md` (SoSe-2026-System).

---

## Wer

**Aram Aljanadi** (aramaljanadi2003@gmail.com) — BSc Informatik HU Berlin (104/180 LP, Stand 04/2026), arbeitet bei BIFOLD/DEEM an **Stratum** (algebraische DAG-Rewrites + symbolische schema-aware Column Selectors, mit Dr. Phani & Elias Strauß). Ziel: MSc Computer Science TU Berlin ab **WiSe 27/28**, Profil ML/Data Systems + Runtime/Optimizer Engineering, Thesis bei DEEM (Schelter). Ambitioniertes Tempo, strukturierte Führung ohne Hand-Holding.

## Systemgrenzen (wichtig!)

- **`semestercontext/` außerhalb von `Masters-Planning/` = SoSe-2026-System → NICHT modifizieren.** Es bleibt autoritativ für das laufende Semester (Brain: `SEMESTER-STATUS.md`).
- Alles Masters-bezogene lebt in **`semestercontext/Masters-Planning/`**.
- `Planing Masters/` (separater Cowork-Ordner): Alt-Entwürfe. `Masterplan-C-strikt.md` ist **deprecated** (Turnus-Fehler), `00-MASTERPLAN.md` = strategischer Hintergrund (Entwürfe A–D, Thesis-Framing, Stratum-Prioritäten — weiterhin gültig).

## Dateien hier

| Datei | Zweck |
|---|---|
| **MASTERS-STATUS.md** | **DAS BRAIN.** Health Dashboard, Phasen-Tracker, Risiken, Entscheidungs-Log. Nach dieser Datei lesen. |
| **MASTERS-MODULE-PLAN.md** | Der Default-Plan: Slot-Tabelle M1–M5, LP-Buckets, Noten-/Kapazitätsstrategie. |
| **MASTERS-MODULE-MENU.md** | **Das Menü:** 54 Module nach 6 Profilachsen (Mathe/ML/DataEng/Algo/Runtime-Optimizer/Benchmarking), Slot-Alternativen pro Semester, Profil-Rezepte, alle mit verifizierten Moses-Links. Budget ≤140 LP. |
| **MASTERS-DATAENG-RESOURCES.md** | Phase-2-Lernbibliothek für den 🔧-Block: pro Modul offene Uni-Kurse (CMU/MIT/Berkeley/TUM/HPI/Böhms eigene DIA-Folien), Bücher, Papers, Hands-on — mit Einsatz-Timing. |
| **MASTERS-ML-RESOURCES.md** | Phase-2-Lernbibliothek 🤖-Block (ML 2-X, DL1/2, ML Lab, MI I/II, Adversarial ML + Fundament ML 1-X/AMLS): Modulprofile aus den offiziellen Katalog-Lehrinhalten, Ressourcen mit Einsatz-Timing. |
| **MASTERS-MATH-RESOURCES.md** | Phase-2-Lernbibliothek 🧮-Block (MathML, FoSP, OptAlgos, ADM II/III): u. a. SSBD = faktisches Kursbuch von MathML, Toussaints öffentliches Komplett-Skript. |
| **MASTERS-ALGO-RESOURCES.md** | Phase-2-Lernbibliothek ⚙️-Block (HA, CC, RandAlgo, ParamAlgo, ADS, AE II, LSA, MTDA): AKT/Niedermeier-Kanon (Cygan frei + Invitation), O'Donnell-Videos, CS168, Grädel-Skripte, TLA+. |
| **MASTERS-RUNTIME-RESOURCES.md** | Phase-2-Lernbibliothek 🚀-Block (TPS, Compiling Techniques, Compiler Design, Lambda-Kalkül): TAPL/Appel/CS6120/MLIR-Toy; Steuwer-Linie = Thesis-Rampe; TPS-vs-LK-Entscheidung dokumentiert. |
| **MASTERS-BENCHMARKING-RESOURCES.md** | Phase-2-Lernbibliothek 📊-Block (CSB, Scalability Eng, Sustainable Computing, ROC): CSB-Kursbuch öffentlich (cloudservicebenchmarking.github.io), Builders' Library, Jain/McGeoch/Hoefler-Methodikkanon = Thesis-Evaluations-Vorschule. **Damit Phase 2 komplett (alle 6 Achsen).** |
| **SYSTEM-MANUAL.md** | **Das Betriebshandbuch:** Mentales Modell, Komponenten-Karte, die 5 Workflows (W0–W5), 10 Invarianten, Command-Cheatsheet, Lifecycle. Lesen, wenn unklar ist, WIE man mit dem System arbeitet. |
| **MASTERS-ARCHITECTURE.md** | **Das Wissenssystem-Blueprint** (2026-07-10): operative vs. Wissens-Schicht, Semester-Kickoff- + Promotions-Ritual, Konventionen (stabile Modul-IDs). Lesen bei allen Wissensarchitektur-Fragen. |
| **DEGREE-WIRING.md** | Modul↔Modul-Routing über das ganze Studium (Analog zu `Plans/WIRING.md`, eine Ebene höher). Gepflegt bei Kickoff + Promotion. |
| **CONCEPT-INDEX.md** | **Die Retrieval-Schicht:** Konzept → ausgearbeitete Notiz (tier-3 Units, Bridges). Wächst pro Semester. |
| **module-cards/** | Ein Pass pro abgeschlossenem Modul (6 SoSe-26-Stubs angelegt; füllen beim Promotions-Ritual). |
| **templates/** | MODULE-CARD- + SEMESTER-KICKOFF- + **LECTURE-UNIT**-Template (tier-3-Standard, formalisiert v2). |
| **TOOLING.md** | Optionaler Tool-Stack (Obsidian/Dataview/Smart Connections, lychee, Anki-MCP, Zotero-MCP) — Setup + Adoptionszeitpunkte. Tools = Linsen, nie Abhängigkeit. |
| **skills-src/** | 3 installierbare Cowork-Skills (lecture-unit-builder, promotion-ritual, semester-kickoff) — via Settings → Capabilities installieren; als Plugin paketieren erst nach dem ersten Promotions-Ritual. |
| **tools/check_system.py** | **Der Validator** (zero-dep): Pfad-Zitate, Links, Card-Vollständigkeit, Frontmatter-Lint. `python3 Masters-Planning/tools/check_system.py` — grün = System konsistent. |
| **MTS-Ground-Truth.md** | Verifizierte Moses-Daten (SoSe 2026). **Regel: Nichts in den MODULE-PLAN, was hier nicht steht.** |
| 3 PDFs | Studiengangsaufbau (26 S.) · Modulkatalog (888 S.) · StuPO-Gesetzestext (AMBl) |

## Eiserne Regeln

1. **Nie Moduldaten erfinden** — nur aus MTS-Ground-Truth.md bzw. frischem Moses-Check; vor Anmeldungen re-verifizieren.
2. **AMLS + ML-Provenance-Projekt sind Bachelor-ÜWP → im Master tabu** (Doppelanrechnungsverbot).
3. **Mathe 2 Drittversuch schlägt alles** — kein Masters-Task verdrängt Bachelor-kritische Arbeit.
4. IS darf nie Hauptgebiet sein; Projekt ≥9 LP + Seminar müssen im Wahlpflichtbereich liegen; ≥12 benotete LP im Wahlbereich (Streichregel).

## Stand jetzt (2026-06-11)

Phase 1.1–1.3 ✅: Ground Truth komplett, Layout **Entwurf C v2** steht (129 LP, Buckets geschlossen: DSE 36 / Neben 24 / WB 30 / Thesis 30), Deliverables angelegt. **Nächstes:** R2-Check (12 LP TheoInf vs. HU-Transcript) und Mathe-2-Termin — siehe `MASTERS-STATUS.md` §3.
