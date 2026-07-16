---
id: masters-tooling
type: brain
status: live
---

# TOOLING — Optional Stack Setup (researched 2026-07-10 · extended 2026-07-11: git ✅, PDF extractors, OCRmyPDF, arxiv-mcp adopted)

> Everything here is a **lens over the markdown**, never a dependency (`MASTERS-ARCHITECTURE.md` §9/§10). All free; OSS noted.

## 1. Obsidian — viewer, graph, queries (~30 min, anytime)

1. Install Obsidian (free; files stay yours) → "Open folder as vault" → select `semestercontext/`.
2. Settings → Community plugins → install exactly these:
   - **Dataview** — query the frontmatter like a database
   - **Breadcrumbs** — hierarchy/trail views (mirrors the wiring docs)
   - **Smart Connections** (OSS, local embeddings, no API key) — semantic "related notes" = automatic complement to `CONCEPT-INDEX.md`
   - *(optional, post-M2)* **Spaced Repetition** — flashcards inline in notes; skip if going the Anki route (§3)
3. Keep it under ~5 plugins (startup cost, conflict risk).

**Starter Dataview queries** (paste into any note):

```dataview
TABLE module, depth FROM "Plans" WHERE type = "unit" SORT module
```
```dataview
LIST FROM "Plans" WHERE type = "unit" AND depth != "full"
```
```dataview
TABLE concepts FROM "" WHERE contains(concepts, "mle")
```
```dataview
TABLE status FROM "Masters-Planning/module-cards" WHERE status = "stub"
```

OSS alternatives if Obsidian ever rankles: Foam (VS Code) · Logseq.

## 2. lychee — link checker (✅ installed 2026-07-10, config tuned)

Config: **`lychee.toml` at repo root** (auto-loaded — excludes auth-gated HU/TU systems, archives, repos/materials; accepts 403/429 bot-blocks; 7-day cache). From `semestercontext/`:

```
lychee --offline .    # fast, local file links only — weekly
lychee .              # + web URLs (LEARNING-RESOURCES etc.) — promotion ritual
```

**Scope note:** lychee checks real markdown links; our backtick path citations are validated by `Masters-Planning/tools/check_system.py`. Run both at every promotion ritual.

## 3. Anki + Anki MCP — spaced repetition (adopt AFTER M2, for the Aug–Okt exam block)

Anki desktop + AnkiConnect add-on + an MCP server (e.g. [ankimcp](https://github.com/ankimcp/anki-mcp-server) or [mcp-ankiconnect](https://lobehub.com/mcp/samefarrar-mcp-ankiconnect)). Then any Claude session can batch-convert Exercise Banks / Mock Exams into decks ("make cards from `AML_L05_Exercise_Bank.md`"). Cards live in Anki; units stay the single source (no card syntax inside notes → §10 no-duplication rule).

## 4. Zotero + zotero-mcp — literature layer (adopt at Masters kickoff, latest before thesis)

Zotero (OSS) + [zotero-mcp](https://github.com/54yyyu/zotero-mcp). Papers/PDFs per module, annotations searchable from Claude, cite-keys referenced in Module Cards. Start collecting DEEM/Stratum papers early.

## 5. git — vault version control (✅ adopted 2026-07-11, KW 28)

Repo initialized at `semestercontext/` root (initial commit `cf081c8`, branch `main`, identity set repo-local). **Philosophy: git tracks the knowledge SYSTEM (~600 md/config/tool files), not the material archives** — `.gitignore` excludes course binaries (PDFs/books/media, ~10 GB), nested team/external repos (mlprov `Project/`, `amls-project/`, `stratum/` — each has its own git), venvs/caches, Obsidian volatile state. Material still needs a normal backup (Time Machine / cloud) — git is history + rollback for the system, not the archive.

- **Pre-commit hook** runs `check_system.py` — a commit that breaks references is rejected (bypass: `git commit --no-verify`).
- **Ritual:** one commit after each work session, message ≈ the SESSION-LOG entry headline. Restructures (the Jun-13/Jul-2/Jul-10 kind) get a commit BEFORE and after.
- **Remote + CI (prepared 2026-07-11, awaiting push):** `.github/workflows/weekly-hygiene.yml` runs a **weekly web link-rot sweep** (`lychee`, Mondays 08:00 Berlin + manual dispatch). CI checks web links ONLY — local-path checks (check_system.py, `lychee --offline`) would false-fail in CI since material files are gitignored; those stay local (pre-commit + weekly ritual). **To activate:** create a **private** repo on github.com (no README/license — repo must be empty), then from `semestercontext/`:
  ```
  git remote add origin git@github.com:<USER>/semestercontext.git
  git push -u origin main
  ```
  (HTTPS variant: `git remote add origin https://github.com/<USER>/semestercontext.git`.) After the first push, check the Actions tab → run weekly-hygiene once manually to verify. From then on: end-of-session `git push` = offsite backup.
- [obsidian-git](https://github.com/Vinzent03/obsidian-git) plugin for auto-commit remains optional (would be plugin #4 of 5 — CLI works fine without it).
- ⚠️ Found during setup: `Plans/ML/mlprov/zitfCqCT` — stray unnamed **300 MB zip** (Jul 3). Ignored in git; identify → rename or delete.

## 6. PDF → Markdown extractors (adopted 2026-07-11; install at first unit-build need, Aug–Okt window)

Replaces raw `pdftotext` for building lecture units from decks/books. Pick per job:

| Tool | Best at | Install (Mac) |
|---|---|---|
| **[MinerU](https://github.com/opendatalab/MinerU)** ⭐ | **formula recognition → LaTeX** (UniMERNet) — math-heavy SaD/AN/AML decks, multi-column | `pipx install "mineru[core]"` (pulls models on first run) |
| **[Marker](https://github.com/datalab-to/marker)** | fastest bulk PDF→md, clean output | `pipx install marker-pdf` (weights: non-commercial license — fine for personal study) |
| **[Docling](https://github.com/docling-project/docling)** (IBM, MIT) | **PPTX/DOCX too**, structured output, best complex tables | `pipx install docling` |

**Workflow:** deck → extractor → md draft → lecture-unit-builder works from the md instead of pdftotext dumps. Try MinerU first for the S.X AMLS units (slides are formula+diagram heavy); fall back to pdftotext for simple decks (it's instant).

## 7. OCRmyPDF — searchable scanned PDFs (adopted 2026-07-11; use on demand)

[OCRmyPDF](https://github.com/ocrmypdf/ocrmypdf) (MPL, Tesseract-based) adds a text layer to scanned PDFs → they become searchable + `pdftotext`/extractor-compatible. Relevant for scanned items in the `Klausuren-extern/` banks and any handwritten-then-scanned notes.

```
brew install ocrmypdf
ocrmypdf --deskew -l deu+eng scan.pdf scan_ocr.pdf
```

## 8. arxiv-mcp-server — paper search from Claude (adopted 2026-07-11; wire up with Zotero at Masters kickoff)

[arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) — search/download/read arXiv papers from any Claude session. Primary use: DEEM/Stratum literature (JK) + thesis prep; pairs with zotero-mcp (§4): arxiv-mcp finds → Zotero keeps. **Setup:** add as custom MCP connector in Claude settings (Settings → Connectors → custom), command: `uv tool run arxiv-mcp-server --storage-path <papers dir>`. Point storage at the owning module's `papers/` folder so check_system.py indexes the downloads.

## 9. Rejected (2026-07-10 · extended 2026-07-11)

Notion/Craft/Mem-class migrations (proprietary silos) · Khoj (self-host overkill vs Smart Connections) · InfraNodus (paid) · >5 Obsidian plugins · **Obsidian MCP servers** (2026-07-11: Cowork already has direct vault file access — pure duplication) · **LightRAG/Cognee knowledge-graph MCPs** (2026-07-11: Smart Connections + CONCEPT-INDEX cover retrieval; same overkill reason as Khoj) · **extra Obsidian flashcard plugins** (2026-07-11: conflicts with the Anki-MCP route §3 + plugin budget).
