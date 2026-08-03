# MASTERS-MODULE-PLAN — TU Berlin MSc Computer Science (StuPO 2015)

> **Stand:** 2026-06-11 · **Phase 1.2 abgeschlossen** · ersetzt `Planing Masters/Masterplan-C-strikt.md`
> **Datenbasis:** ausschließlich `MTS-Ground-Truth.md` (Moses, SoSe 2026) — kein Modul hier ist unverifiziert.
> **Annahmen:** Bachelor fertig bis Ende WiSe 26/27 · Start **WiSe 27/28** · **5 Semester** · ~129 LP Default, **Budget bis 140 LP** · Anker: Stratum/DEEM · Thesis M5.
> **Alternativen pro Slot + Profilachsen-Katalog mit Moses-Links: → `MASTERS-MODULE-MENU.md`** (dieses Dokument ist der Default daraus).

---

## §1 Slot-Tabelle (Entwurf C v2 — Turnus-korrigiert)

| Sem. | Modul 1 | Modul 2 | Modul 3 | Modul 4 | Modul 5 | Σ |
|---|---|---|---|---|---|---|
| **M1** WiSe 27/28 | **DBT** 6 (schriftl. 90min) | **Höhere Algorithmik** 9 (schriftl.) | **MDS** 6 (mündl.) | **TPS** 6 (mündl., Steuwer) | — | **27** |
| **M2** SoSe 28 | **ML 2-X** 12 (schriftl.) | **DMH** 6 (Portfolio) | **CSB** 6 (Portfolio) | **BDASEM** 3 (mündl., max 8!) | — | **27** |
| **M3** WiSe 28/29 | **DBTLAB** 6 (Portfolio, 150h) | **EDML** 6 (Portfolio, Schelter) | **Deep Learning 1** 6 (schriftl.) | **DILA** 6 (schriftl., Böhm) | **Research Seminar DEEM** 3 (unbenotet, max 8!) | **27** |
| **M4** SoSe 29 | **Responsible DE Project** 9 (Portfolio, Schelter — Pflichtprojekt + Thesis-Groundwork) | **MLMMI** 6 (Portfolio, Schelter) | **ML&DMS** 3 (Referat, Böhm) | *Thesis-Anmeldung Semesterende* | — | **18** |
| **M5** WiSe 29/30 | **Masterarbeit 30 — Stratum: Optimizer / Runtime / Dataflow (DEEM)** | | | | | **30** |

**Gesamt: 99 LP Module + 30 LP Thesis = 129 LP** → 9 LP Überhang über die zählenden 120.

### Warum so gestapelt

- **Alle WiSe-only-Module** (DBT, HA, MDS, TPS, DBTLAB, EDML, DL1, DILA) sitzen in M1/M3 — der Kern der C-strikt-Reparatur (DBTLAB & MDS liefen dort fälschlich im SoSe).
- **DBT (M1) → DBTLAB (M3):** Voraussetzung erfüllt, und die beiden DIMA-Implementierungsbrocken (DBT-Vorleistungen ~55h, DBTLAB-Lab 150h) liegen nie im selben Semester.
- **Prüfungsmix pro Semester ausbalanciert:** M1 = 2 Klausuren + 2 mündliche; M2 = 1 große Klausur (ML 2-X) + 2 Portfolios; M3 = 2 Klausuren + 2 Portfolios. Nie mehr als 2 Klausuren/Semester.
- **DEEM-Rampe:** M3 EDML + Research Seminar (Sichtbarkeit bei Schelter) → M4 Responsible DE Project + MLMMI (Thesis-Groundwork im Projekt) → M5 Thesis. M4 ist bewusst leicht (18 LP).
- **IMPRO gestrichen** (existiert nicht), „Probabilistic/Bayesian-Slot" gestrichen (kein passendes Modul; nächste Äquivalente bei Bedarf: Mathematics of ML 6, Foundations of Stochastic Processes 6, Uncertainty in ML 3).

---

## §2 LP-Buchhaltung der zählenden 120 (Default-Zuordnung)

| Bucket | Module | LP | Regel |
|---|---|---|---|
| **Hauptgebiet DSE** | DBT 6 · DBTLAB 6 · DMH 6 · MDS 6 · **Responsible DE Project 9 (= Pflichtprojekt ≥9 ✓)** · **BDASEM 3 (= Pflichtseminar ✓)** | **36** | 30–42 ✓ |
| **Weitere Studiengebiete/IS** | ML 2-X 12 (KS *oder* IS) · DL1 6 (KS) · TPS 6 (FC) | **24** | 18–36 ✓ |
| *Wahlpflicht gesamt* | | *60* | *60–66 ✓ (Projekt+Seminar drin ✓)* |
| **Wahlbereich** | HA 9 · CSB 6 · EDML 6 · DILA 6 · ML&DMS 3 — **alle benotet** | **30** | 24–30 ✓ |
| **Masterarbeit** | Stratum/DEEM | **30** | zählt immer |
| **Σ zählend** | | **120** | ✓ |
| Zusatzmodule (Überhang) | MLMMI 6 · Research Seminar DEEM 3 (ohnehin unbenotet) | 9 | im Zeugnis, nicht in der Note |

### Eingebaute Flexibilität (nach Notenlage umbuchbar)

1. **HA ist doppelt gelistet (DSE + FC)** → kann bei Bedarf ins Hauptgebiet (Tausch gegen z. B. DMH/MDS) oder ein FC-Nebengebiet auffüllen.
2. **ML 2-X ist KS + IS** → Nebenbucket maximal flexibel.
3. **EDML/DILA/CSB sind DSE** → können mit Hauptgebiet-Modulen getauscht werden, wenn dort eine schwache Note liegt.
4. **MLMMI (Zusatz)** kann ein schwächer benotetes DSE/WB-Modul aus der Wertung verdrängen.

---

## §3 Notenstrategie (§8-Streichregel)

- **30 LP schlechteste Module fliegen aus der Note, davon müssen 12 LP Wahlbereich sein.** Der Wahlbereich hat hier **30 benotete LP** → Streichregel voll nutzbar, nichts verschenkt.
- **Die beiden Großrisiken sind streichbar platziert:** HA 9 liegt im Wahlbereich, ML 2-X 12 im Nebenbucket (streichbar über die 18 Nicht-WB-LP). Beide schwach = abfederbar, aber nicht zusammen mit einem dritten Ausreißer.
- **Masterarbeit zählt immer** → Stratum-Anker ist der größte Notenhebel. 26 Wochen; Anmeldung erst, wenn Groundwork aus M4 (Responsible DE Project) steht.
- Große Module nie gestapelt: ML 2-X dominiert M2 allein.

---

## §4 Kapazitäts- & Anmeldestrategie

| Risiko | Module | Strategie |
|---|---|---|
| **max 8 Plätze** | BDASEM (M2) · Research Seminar DEEM (M3) | Anmeldung am ersten Tag; **Fallback: IMSEM 3 LP (WiSe+SoSe, max 8, Portfolio)** — erfüllt Seminarpflicht gleichwertig (IS/DSE) |
| **max 12** | BDSPRO (Backup-Projekt) | nur relevant, falls Responsible DE Project scheitert |
| **max 20–24** | CSB 20 · TPS 24 · EDML 24 · MLMMI 24 · Responsible DE Project 24 | früh anmelden, unkritisch bei normalem Verlauf |
| **DIMA-Tool** | DBT · DBTLAB · MDS · DMH | Anmeldung **vor Vorlesungsbeginn** über DIMA-Tool — Termine pro Semester prüfen |

**Backup-Projekt:** BDSPRO 40494 (9 LP, Portfolio, WiSe+SoSe, DSE+IS) ersetzt Responsible DE Project 1:1 als Pflichtprojekt, falls Kapazität/DEEM-Anbindung scheitert.

**Seminar-Hinweis:** Research Seminar DEEM ist **unbenotet** → bewusst NICHT als Pflichtseminar eingeplant (Erfüllbarkeit unklar), sondern als Zusatzmodul für DEEM-Sichtbarkeit. Pflichtseminar = BDASEM (benotet, DSE).

---

## §5 Festlegungen & Verbote

- **AMLS (TU) + ML-Provenance-Projekt (TU)** werden im HU-Bachelor als ÜWP verbucht → **Doppelanrechnungsverbot**, tauchen hier nirgends auf. (TU-AMLS 41078 wäre in DSE verfügbar — gesperrt.)
- ML 1-X, HU-Compilerbau: als erledigt behandelt, nicht anrechenbar.
- Modul-Daten = Stand SoSe 2026. **Vor jeder Anmeldung Turnus/Prüfungsform in Moses re-verifizieren** (Präzedenz: DBT-Prüfung wechselte Portfolio → Klausur).

## §6 Offene Punkte → siehe MASTERS-STATUS.md §3
