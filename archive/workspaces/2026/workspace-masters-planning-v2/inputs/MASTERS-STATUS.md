# MASTERS-STATUS — Kontrollzentrum Masters-Planning

> **Stand:** 2026-06-11 · Lies zuerst `MASTERS-HANDOFF.md`, dann das hier.
> Plan selbst: `MASTERS-MODULE-PLAN.md` · Datenbasis: `MTS-Ground-Truth.md` + 3 PDFs.

---

## §0 Health Dashboard

| Bereich | Status | Notiz |
|---|---|---|
| Phase 1.1 Ground Truth | 🟢 done | Moses verifiziert, 3 offizielle PDFs lokal |
| Phase 1.2 Semesterlayout | 🟢 done | Entwurf C v2, Turnus-korrigiert, Buckets geschlossen |
| Phase 1.3 Wahlbereich/HU-Sichtung | 🟡 optional | WB ist bereits TU-intern voll (30 LP benotet) — HU-Module nur noch als Tauschoption |
| Phase 2 Ressourcen-Bibliotheken | 🟢 **komplett** | Alle 6 Achsen: 🔧 🤖 (+ML 1-X/AMLS) 🧮 ⚙️ 🚀 📊 (`MASTERS-*-RESOURCES.md`, 2026-06-11) |
| Bachelor (Voraussetzung für alles) | 🔴 kritisch | Mathe 2 Drittversuch SoSe 26 |
| TU-Bewerbung WiSe 27/28 | 🟡 offen | Zugangs-Check + Deadlines ungeklärt |

## §1 Phasen-Tracker

- ✅ **1.1** Ground Truth aus MTS/Moses (2026-06-10)
- ✅ **1.2** Semesterlayout neu gebaut, C-strikt ersetzt (2026-06-11)
- ✅ **1.3** Deliverables aufgesetzt (HANDOFF / STATUS / MODULE-PLAN) (2026-06-11)
- ⬜ **1.4** Zugangsvoraussetzungen vs. HU-Transcript (s. Risiko R2)
- ⬜ **1.5** Bewerbungs-Deadlines + Unterlagen WiSe 27/28
- ⬜ **2.x** Pro-Modul-Ressourcenbibliotheken (LEARNING-RESOURCES-Konvention)
- ✅ **3.1** Wissensarchitektur gesät (2026-07-10): ARCHITECTURE + DEGREE-WIRING + CONCEPT-INDEX + Templates + 6 Modul-Card-Stubs
- ✅ **3.1b** **Rebuild v2** (2026-07-10): Frontmatter-Konventionen (Anchor-File-Regel), `Masters-Planning/tools/check_system.py` (Validator, grün über 122 Dateien), LECTURE-UNIT-Template, TOOLING.md, skills-src/ (3 Skills), Retrofit: 28 Dateien (12 Unit-Anker + 8 Referenzdocs SoSe 26 + Degree-Dateien, rein additiv); Bonus-Fund: `learningcontent`-Ordner hatte trailing space → renamed
- ⬜ **3.2** Promotions-Ritual SoSe 26 ausführen (nach den Prüfungen, ~Aug/Okt): Cards füllen, Index/Wiring updaten, danach ggf. Skills als Plugin paketieren

## §2 Risiken (Priorität absteigend)

| # | Risiko | Impact | Mitigation |
|---|---|---|---|
| **R1** | **Mathe 2 Drittversuch (SoSe 26)** — letzter Versuch; Nichtbestehen = Bachelor endgültig weg | existenziell | Hat absoluten Vorrang vor allem Masters-Planning; Prüfungstermin noch nicht erfasst → nachtragen |
| **R2** | **TU-Zugangsvoraussetzung: 36 LP GdI inkl. 12 LP Theoretische Informatik** — „<5% der Bewerber erfüllten die Kriterien" | Bewerbung scheitert | HU-Transcript-Mapping machen (Logik? ToC? AlgoDat-Anteile?) **bevor** Bewerbungsunterlagen erstellt werden; ggf. Wahlpflicht im Bachelor-Endspurt gezielt TheoInf-lastig wählen |
| **R3** | Bachelor nicht fertig bis Ende WiSe 26/27 | Start rutscht auf SoSe 28 | Plan ist WiSe-Start-optimiert; bei SoSe-Start Layout spiegeln (M1↔M2-Logik), Ground Truth bleibt gültig |
| **R4** | Kapazität max-8-Seminare (BDASEM, RS DEEM) | Seminarpflicht verzögert | IMSEM-Fallback fest eingeplant (MODULE-PLAN §4) |
| **R5** | Katalogdrift bis 27/28 (Prüfungsformen/Turnus ändern sich) | Slots kippen | Vor jeder Anmeldung Moses-Re-Check; Ground-Truth-Datei aktualisieren |
| **R6** | DEEM-Anbindung (Schelter) materialisiert nicht | Thesis-Pipeline | Stratum-Arbeit weiterführen; Backup: BDSPRO + DIMA-Orbit (Markl) oder Böhm (DILA/ML&DMS) |

## §3 Offene Punkte (nächste Sessions)

1. **R2-Check:** HU-Leistungsspiegel gegen TU-Zugangsprofil mappen (12 LP TheoInf!). Braucht aktuellen Leistungsspiegel als Upload.
2. Mathe-2-Prüfungstermin erfassen.
3. Bewerbungs-Deadline WiSe 27/28 + Suitability-Form + B2-Nachweis klären (~Frühjahr 2027, rechtzeitig prüfen).
4. „Data Science and Engineering Track"-Zertifikat (Fak. IV) prüfen — könnte das Profil offiziell labeln.
5. Phase 2 starten, sobald SoSe-26-Last es erlaubt.

## §4 Wichtigste Entscheidungen (Log)

| Datum | Entscheidung |
|---|---|
| 2026-06 | 5 Semester, WiSe-27/28-Start, ~129 LP, Thesis M5 bei DEEM |
| 2026-06-10 | Szenario 1 bestätigt (DIMA-Spine = Hauptgebiet DSE) |
| 2026-06-11 | C-strikt ersetzt durch **Entwurf C v2** (DBTLAB+MDS→WiSe/M3 bzw. M1, IMPRO + Bayesian-Slot gestrichen) |
| 2026-06-11 | Pflichtprojekt = **Responsible DE Project (Schelter)** statt BDSPRO; BDSPRO = Backup |
| 2026-06-11 | Pflichtseminar = **BDASEM** (benotet); Research Seminar DEEM nur als unbenotetes Zusatzmodul |
| 2026-06-11 | Wahlbereich komplett TU-intern gefüllt (30 LP benotet) — HU-Module nicht mehr nötig |
| 2026-06-11 | **LP-Budget auf max 140 erhöht** (Aram); Projektziel erweitert: Modul-**Menü** statt Einzelplan → `MASTERS-MODULE-MENU.md` (54 Module, 6 Profilachsen, Moses-Links verifiziert) |
| 2026-06-11 | **Voll-Scan aller 332 Katalogmodule** → MENU §1b: +GPU Computing (Steuwer, übersehen!), +4 Projekt- & 6 Seminar-Alternativen, DSN-Annex, WB-Füller. Sweep vollständig — nichts Profilrelevantes fehlt mehr |
| 2026-06-11 | **Frontier-Lab-Delta** in RUNTIME-RESOURCES ergänzt (Schicht 3: Ultra-Scale Playbook, Bekman-Buch, Megatron/ZeRO-Paperkette, GPU MODE, Triton/FlashAttention, PagedAttention + Wochenendprojekt) — Profil-Lernsystem damit final vollständig |
| 2026-06-11 | **Mega-Sweep über alle 6 RESOURCES-Dateien**: je Nachtrag mit Übungsblättern/Lösungen, fremden Klausurarchiven (MIT OCW 6.046/18.657/6.262, Berkeley CS186/CS189, Caltech, EE364a, CS143), Lern-Repos (egg!, Calcite, toydb, chibicc, benchbase, tinygrad, mlinspect …); Arams `Ultimate-Index.md` integriert + Kopie in Masters-Planning/ |

## §5 Session-Log

- **2026-06-10:** Phase 1.1 — Moses-Recherche, MTS-Ground-Truth.md + 3 PDFs.
- **2026-06-11:** Phase 1.2/1.3 — Layout C v2, Buckets, Notenstrategie, Kapazitätsplan; Deliverables erstellt; C-strikt deprecated.
- **2026-06-11 (2):** MASTERS-MODULE-MENU.md gebaut — Versionsnummern aus 888-S.-Katalog extrahiert, Moses-Link-Pattern live verifiziert (DBT + ADM II), Slot-Alternativen M1–M4, Profil-Rezepte, Budget ≤140 LP.
- **2026-07-10:** Wissensarchitektur gesät (aus dem Semester-Projekt heraus, sanktioniert): `MASTERS-ARCHITECTURE.md` (2-Schichten-Modell + Kickoff/Promotions-Ritual), `DEGREE-WIRING.md` (SoSe-26→Master-Kanten je Achse), `CONCEPT-INDEX.md` (geseedet aus AML L02–L07 + SaD L01–L05/L11 Units, Bridges, Deep Plan), `templates/` (MODULE-CARD, SEMESTER-KICKOFF), `module-cards/` (6 Stubs). Entscheidung: Markdown-only, Index zeigt in Units (kopiert nie), Sync nur beim Promotions-Ritual.
