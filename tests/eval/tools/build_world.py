#!/usr/bin/env python3
"""Build the synthetic LearningOS evaluation world, deterministically.

    .venv/bin/python tests/eval/tools/build_world.py --out DIR
    .venv/bin/python tests/eval/tools/build_world.py --out DIR --source-rev WORKTREE
    .venv/bin/python tests/eval/tools/build_world.py --out DIR --scale 2000 --seed 7

The world is a complete, separate LearningOS installation: the product (code,
contracts, docs, tests) taken from one pinned LearningOS revision, with every
piece of learner data replaced by the synthetic learner history in
``tests/eval/corpus/``. It never touches the repository it is built from.

Layout under DIR:

    LearningOS/repository/   the installation; its own Git repository whose
                             history replays the synthetic timeline with fixed
                             author, committer and dates
    LearningOS/materials/    the synthetic external materials tree
    eval-drop/               arrivals: material that reaches the learner during
                             scenarios (never part of the installation at start)
    EVAL-WORLD.json          build record: product revision, corpus digest,
                             world HEAD, counts

Determinism: the same corpus, product revision, --scale and --seed produce the
same world HEAD commit id. ``selftest.py`` checks this by building twice.

Run it with an interpreter that has the LearningOS dependencies (PyYAML,
jsonschema, pypdf) — the repository's ``.venv`` — because the build finishes
by running the world's own validator to record its warning baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
REPO = EVAL.parents[1]
CORPUS = EVAL / "corpus"
sys.path.insert(0, str(HERE))

from bundle import read_bundle, read_bundles  # noqa: E402

BUILDER_VERSION = 1

# What the installation takes from the product revision. Everything else under
# the repository root is learner data and comes from the corpus.
PRODUCT_PATHS = [
    ".claude", ".codex", ".github", ".gitignore", "AGENTS.md", "CLAUDE.md", "Makefile",
    "README.md", "pyproject.toml", "requirements-dev.txt", "system", "tests", "tools",
    "curriculum/thematic-groups.yaml", "sources/topics.yaml",
]
PRODUCT_EXCLUDE_PREFIXES = ("tests/eval/", "tests/eval")

NOTE_FRONTMATTER_KEYS = [
    "id", "type", "title", "created", "reviewed", "role", "state", "authorship",
    "transcription", "semantic_review", "concepts", "sources", "attachments", "contexts",
    "evidence", "supersedes",
]
WORKSPACE_FRONTMATTER_KEYS = [
    "id", "type", "title", "created", "status", "standing", "deadline", "concepts", "notes",
    "sources", "program_ids", "module_ids", "unit_ids", "project_id",
]
PUBLIC_ARRIVAL_FIELDS = ["kind", "arrives", "channel", "context"]


class BuildError(RuntimeError):
    pass


# ----------------------------------------------------------------- helpers
def dump_yaml(data) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def frontmatter(meta: dict, keys: list[str]) -> str:
    ordered = {k: meta[k] for k in keys if k in meta and meta[k] not in (None, [])}
    unknown = sorted(set(meta) - set(keys))
    if unknown:
        raise BuildError(f"unknown frontmatter keys {unknown} for {meta.get('id')}")
    return "---\n" + dump_yaml(ordered) + "---\n\n"


def iso(date) -> str:
    return str(date)


def corpus_digest(corpus: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in corpus.rglob("*") if p.is_file()):
        rel = path.relative_to(corpus).as_posix()
        h.update(rel.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def git(cwd: Path, *args: str, env: dict | None = None, capture: bool = False) -> str:
    base = {k: v for k, v in os.environ.items()
            if not k.startswith("GIT_") or k in ("GIT_EXEC_PATH",)}
    base.update({"LC_ALL": "C", "TZ": "UTC"})
    if env:
        base.update(env)
    result = subprocess.run(["git", *args], cwd=cwd, env=base, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise BuildError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout if capture else ""


# ---------------------------------------------------------------- product
def resolve_revision(rev: str) -> str:
    if rev == "WORKTREE":
        return "WORKTREE"
    return git(REPO, "rev-parse", "--verify", f"{rev}^{{commit}}", capture=True).strip()


def product_files(rev: str) -> dict[str, tuple[bytes, int, str | None]]:
    """relpath -> (bytes, mode, symlink target) for the product at ``rev``."""
    files: dict[str, tuple[bytes, int, str | None]] = {}
    if rev == "WORKTREE":
        listed = git(REPO, "ls-files", "--cached", "--others", "--exclude-standard", "-z",
                     "--", *PRODUCT_PATHS, capture=True)
        for rel in sorted(filter(None, listed.split("\0"))):
            if rel.startswith(PRODUCT_EXCLUDE_PREFIXES):
                continue
            path = REPO / rel
            if path.is_symlink():
                files[rel] = (b"", 0o120000, os.readlink(path))
            elif path.is_file():
                mode = 0o755 if os.access(path, os.X_OK) else 0o644
                files[rel] = (path.read_bytes(), mode, None)
        return files
    raw = subprocess.run(["git", "archive", "--format=tar", rev, "--", *PRODUCT_PATHS],
                         cwd=REPO, capture_output=True)
    if raw.returncode != 0:
        raise BuildError(f"git archive {rev} failed: {raw.stderr.decode().strip()}")
    with tarfile.open(fileobj=io.BytesIO(raw.stdout)) as tar:
        for member in tar.getmembers():
            rel = member.name
            if rel.startswith(PRODUCT_EXCLUDE_PREFIXES):
                continue
            if member.issym():
                files[rel] = (b"", 0o120000, member.linkname)
            elif member.isfile():
                data = tar.extractfile(member).read()
                mode = 0o755 if member.mode & 0o111 else 0o644
                files[rel] = (data, mode, None)
    return files


def skeleton_dirs(product: dict) -> list[str]:
    """Directories the product's tree contract declares (minus gitignored ones)."""
    raw = product.get("system/contracts/tree-contract.yaml")
    if raw is None:
        return []
    contract = yaml.safe_load(raw[0].decode("utf-8"))
    out: list[str] = []

    def walk(entries):
        for entry in entries or []:
            if "path" not in entry:  # glob rows describe files, not directories
                continue
            out.append(entry["path"])
            walk(entry.get("children"))

    walk(contract.get("directories"))
    return [p for p in out if p not in ("bases",)]


# ------------------------------------------------------------------ corpus
class World:
    """Every rendered file with the date it enters the history."""

    def __init__(self, corpus: Path):
        self.corpus = corpus
        self.meta = yaml.safe_load((corpus / "world.yaml").read_text(encoding="utf-8"))
        self.start = iso(self.meta["timeline"]["start"])
        self.as_of = iso(self.meta["timeline"]["as_of"])
        # date -> relpath -> text ; later dates overwrite earlier content
        self.events: dict[str, dict[str, str]] = {}
        self.messages: dict[str, list[str]] = {}
        self.arrivals: list[dict] = []
        self.note_ids: set[str] = set()

    def put(self, date, rel: str, text: str | None, message: str) -> None:
        """Record ``rel`` with ``text`` at ``date``; ``None`` deletes it then."""
        date = iso(date)
        if not (self.start <= date <= self.as_of):
            raise BuildError(f"{rel}: date {date} outside timeline {self.start}..{self.as_of}")
        self.events.setdefault(date, {})[rel] = text
        self.messages.setdefault(date, []).append(message)

    # -- registries -------------------------------------------------------
    def registries(self) -> None:
        reg = yaml.safe_load((self.corpus / "registries.yaml").read_text(encoding="utf-8"))
        headers = {
            "knowledge/concepts.yaml": ("concepts", "# Concept identities (synthetic evaluation world).\n"),
            "knowledge/concept-relations.yaml": (
                "relations", "# Concept-to-concept semantic edges only (no related-to).\n"),
        }
        for rel, (key, header) in headers.items():
            self._dated_registry(rel, key, reg.get(key, []), header)
        # sources are partitioned by subject, like the product's own registry
        partitions: dict[str, list] = {}
        for src in reg.get("sources", []):
            partitions.setdefault(src.get("partition", "general"), []).append(src)
        for name, rows in sorted(partitions.items()):
            self._dated_registry(f"sources/registry/{name}.yaml", "sources", rows,
                                 f"# Source records — {name} partition.\n", drop=("partition",))
        self.put(self.start, "sources/sources.yaml",
                 "# Consolidated registry intentionally empty; records live in "
                 "sources/registry/.\nsources: []\n", "Set up source registry")
        self.put(self.start, "knowledge/abilities.yaml",
                 "# Independently reviewed ability identities. These do not attest learner "
                 "work.\n" + dump_yaml({"abilities": reg.get("abilities", []),
                                        "bridges": reg.get("ability_bridges", [])}),
                 "Set up abilities registry")
        for prog in reg.get("programs", []):
            rec = {k: v for k, v in prog.items() if k != "added"}
            self.put(prog.get("added", self.start), f"curriculum/programs/{rec['id']}.yaml",
                     dump_yaml(rec), f"Add program {rec['id']}")

    def _dated_registry(self, rel, key, rows, header, drop=()):
        dates = sorted({iso(r.get("added", self.start)) for r in rows} | {self.start})
        for date in dates:
            present = [{k: v for k, v in r.items() if k not in ("added", *drop)}
                       for r in rows if iso(r.get("added", self.start)) <= date]
            self.put(date, rel, header + dump_yaml({key: present}),
                     f"Update {rel.rsplit('/', 1)[-1]}")

    # -- notes ------------------------------------------------------------
    def notes(self) -> None:
        for item in read_bundles(self.corpus / "notes"):
            meta = dict(item.meta)
            domain = meta.pop("domain")
            updated = iso(meta.pop("updated", meta["created"]))
            note_id = item.key
            meta = {"id": note_id, "type": "note", **meta}
            rel = f"knowledge/notes/{domain}/{note_id}.md"
            self.note_ids.add(note_id)
            for rev in item.revisions:
                rmeta = {**meta, **{k: v for k, v in rev.meta.items() if k != "domain"}}
                self.put(rev.revision, rel, frontmatter(rmeta, NOTE_FRONTMATTER_KEYS) + rev.body,
                         f"Note {note_id} (draft)")
            self.put(updated, rel, frontmatter(meta, NOTE_FRONTMATTER_KEYS) + item.body,
                     f"Note {note_id}")

    # -- curriculum -------------------------------------------------------
    def curriculum(self) -> None:
        cur = yaml.safe_load((self.corpus / "curriculum.yaml").read_text(encoding="utf-8"))
        stage_bodies = {i.key: i for i in read_bundle(self.corpus / "stage-notes.md")}
        used_stage_bodies: set[str] = set()
        snapshot = []
        for mod in cur["modules"]:
            mid = mod["id"]
            base = f"curriculum/modules/{mid}"
            record = {"id": mid, "type": "module", **mod["record"],
                      "unit_order": [u["id"] for u in mod["units"]],
                      "source_map": "source-map.yaml"}
            self.put(mod["date"], f"{base}/module.yaml", dump_yaml(record), f"Module {mid}")
            smap = {"type": "module-source-map", "module_id": mid, "sources": mod["source_map"]}
            self.put(mod["date"], f"{base}/source-map.yaml", dump_yaml(smap),
                     f"Source map {mid}")
            snap = {"id": mid, "title": record["title"], "status": record["status"]}
            for key in ("institution", "attempts"):
                if key in record:
                    snap[key] = record[key]
            snapshot.append(snap)
            for unit in mod["units"]:
                uid = unit["id"]
                ubase = f"{base}/units/{uid}"
                urec = {"id": uid, "type": "unit", "module_id": mid, **unit["record"]}
                if "scope_sources" not in urec:
                    # Every real unit names what defines its scope; default to the
                    # module's first (course-material or spine) source.
                    first = mod["source_map"][0]
                    urec["scope_sources"] = [{
                        "source_id": first["source_id"],
                        "authority": "slides" if first["role"] == "course-material"
                        else "reference",
                        "locator": urec["title"]}]
                smap_rec = unit.get("study_map")
                if smap_rec:
                    urec["current_study_map"] = smap_rec["id"]
                self.put(unit.get("date", mod["date"]), f"{ubase}/unit.yaml", dump_yaml(urec),
                         f"Unit {uid}")
                if not smap_rec:
                    continue
                stages = []
                for number, stage in enumerate(smap_rec["stages"], start=1):
                    note_rel = f"{ubase}/stages/{stage['id']}/notes.md"
                    stage = {"id": stage["id"], "number": number, **{
                        k: v for k, v in stage.items() if k != "id"}}
                    stage.setdefault("working_note", note_rel)
                    stage.setdefault("attachments", [])
                    stage.setdefault("source_feedback", [])
                    stages.append(stage)
                    body = stage_bodies.get(note_rel)
                    if body is not None:
                        used_stage_bodies.add(note_rel)
                        for rev in body.revisions:
                            self.put(rev.revision, note_rel, rev.body, f"Stage note {stage['id']}")
                        self.put(body.meta["date"], note_rel, body.body,
                                 f"Stage note {stage['id']}")
                    else:
                        self.put(smap_rec.get("date", unit.get("date", mod["date"])), note_rel,
                                 "", f"Stage note {stage['id']}")
                srec = {"id": smap_rec["id"], "type": "study-map", "plan_template_version": 1,
                        "unit_id": uid,
                        **{k: v for k, v in smap_rec.items()
                           if k not in ("id", "stages", "date", "history")},
                        "stages": stages}
                final_date = iso(smap_rec.get("date", unit.get("date", mod["date"])))
                # Earlier progress states first, each strictly before the final
                # state: a same-date history entry would overwrite the final
                # map (both land in one commit, last write wins).
                for past in smap_rec.get("history", []):
                    if iso(past["date"]) >= final_date:
                        raise BuildError(f"{srec['id']}: history date {past['date']} is not "
                                         f"before the map's final date {final_date}")
                    earlier = json.loads(json.dumps(srec))
                    earlier["current_stage"] = past["current_stage"]
                    for st in earlier["stages"]:
                        st["status"] = past["statuses"].get(st["id"], st["status"])
                    self.put(past["date"], f"{ubase}/study-map.yaml", dump_yaml(earlier),
                             f"Progress in {srec['id']}")
                self.put(final_date, f"{ubase}/study-map.yaml", dump_yaml(srec),
                         f"Study map {srec['id']}")
        unused = sorted(set(stage_bodies) - used_stage_bodies)
        if unused:
            raise BuildError(f"stage notes without a stage: {unused}")
        resume = cur.get("resume")
        if resume:
            self.put(resume["updated"], "curriculum/resume.yaml",
                     dump_yaml({"type": "resume-pointer", **resume}), "Resume pointer")
        self.put(self.start, "records/modules.yaml",
                 "# Frozen compatibility snapshot; module facts live in curriculum/modules/.\n"
                 + dump_yaml({"modules": snapshot}), "Module snapshot")

    # -- work tree ----------------------------------------------------------
    def work(self) -> None:
        for item in read_bundle(self.corpus / "workspaces.md"):
            meta = dict(item.meta)
            date = iso(meta.pop("date"))
            archived = meta.pop("archived", False)
            history = meta.pop("history", [])
            meta = {"id": item.key, "type": "workspace", **meta}
            active = f"work/active/{item.key}/CONTEXT.md"
            rel = f"archive/workspaces/{item.key}/CONTEXT.md" if archived else active
            text = frontmatter(meta, WORKSPACE_FRONTMATTER_KEYS) + item.body
            for rev in item.revisions:
                rmeta = {**meta, **rev.meta}
                self.put(rev.revision, active,
                         frontmatter(rmeta, WORKSPACE_FRONTMATTER_KEYS) + rev.body,
                         f"Workspace {item.key}")
            for touch in history:
                # before archiving, the workspace lived under work/active/
                self.put(touch, active, text, f"Workspace {item.key}")
            if archived:
                self.put(date, active, None, f"Archive workspace {item.key}")
            self.put(date, rel, text, f"Workspace {item.key}")
            for sub, extra in (item.meta.get("files") or {}).items():
                self.put(date, f"{rel.rsplit('/', 1)[0]}/{sub}", extra,
                         f"Workspace {item.key} file")
        coord = read_bundle(self.corpus / "coordination.md")[0]
        for rev in coord.revisions:
            self.put(rev.revision, "work/COORDINATION.md",
                     "---\nid: coordination\ntype: coordination\n---\n\n" + rev.body,
                     "Coordination")
        self.put(coord.meta["date"], "work/COORDINATION.md",
                 "---\nid: coordination\ntype: coordination\n---\n\n" + coord.body, "Coordination")
        for item in read_bundle(self.corpus / "inbox.md"):
            self.put(item.meta["date"], f"work/inbox/{item.key}", item.body, "Capture")
            if item.meta.get("routed"):
                self.put(item.meta["routed"], f"work/inbox/{item.key}", None, "Route capture")
        for item in read_bundle(self.corpus / "garden.md"):
            for rev in item.revisions:
                self.put(rev.revision, f"knowledge/garden/{item.key}", rev.body, "Garden")
            self.put(item.meta["date"], f"knowledge/garden/{item.key}", item.body, "Garden")

    def projects(self) -> None:
        data = yaml.safe_load((self.corpus / "projects.yaml").read_text(encoding="utf-8"))
        for proj in data.get("projects", []):
            rec = {k: v for k, v in proj.items() if k not in ("date",)}
            self.put(proj["date"], f"projects/registry/{rec['id']}.yaml", dump_yaml(rec),
                     f"Project {rec['id']}")
        self.put(self.start, "projects/relations/project-relations.yaml",
                 dump_yaml({"relations": data.get("relations", [])}), "Project relations")
        self.put(self.start, "projects/aliases.yaml",
                 dump_yaml({"aliases": data.get("aliases", {})}), "Project aliases")

    def arrivals_index(self) -> None:
        for item in read_bundle(self.corpus / "arrivals.md"):
            public = {k: item.meta[k] for k in PUBLIC_ARRIVAL_FIELDS if k in item.meta}
            public["arrives"] = iso(public.get("arrives", self.as_of))
            unknown = sorted(set(item.meta) - set(PUBLIC_ARRIVAL_FIELDS) - {"filename"})
            if unknown:
                raise BuildError(f"arrival {item.key}: non-public header keys {unknown}")
            self.arrivals.append({"id": item.key, **public,
                                  "file": item.meta.get("filename", f"{item.key}.md"),
                                  "body": item.body})

    def build(self) -> None:
        self.registries()
        self.notes()
        self.curriculum()
        self.work()
        self.projects()
        self.arrivals_index()


# ------------------------------------------------------------------- scale
SCALE_TOPICS = {
    "mathematics": ["series convergence tests", "complex numbers", "matrix norms",
                    "combinatorial identities", "Markov inequality", "Taylor expansion"],
    "machine-learning": ["decision stumps", "k-means initialisation", "ROC curves",
                         "early stopping", "one-hot encoding", "learning-rate warmup"],
    "systems": ["interrupt handling", "file descriptors", "copy-on-write", "signals",
                "memory-mapped files", "context-switch cost"],
    "data-systems": ["B+ tree fanout", "column encodings", "CSV parsing pitfalls",
                     "partition pruning", "idempotent loads", "late-arriving data"],
    "programming": ["borrow checker", "iterator adapters", "error enums",
                    "property-based tests", "code review checklists", "lexer states"],
}
SCALE_SENTENCES = [
    "Revisited {t} while tidying old material; the main point still holds.",
    "Worked a small example on {t} and wrote down the steps I kept forgetting.",
    "Short reminder about {t}: check the edge case before trusting the result.",
    "Copied from an older notebook page about {t}, lightly cleaned up.",
    "Question I still have about {t}: when does the simple rule stop working?",
    "The textbook treatment of {t} is terse; my own wording is below.",
]


def scale_notes(world: World, count: int, seed: int) -> None:
    rng = random.Random(seed)
    domains = sorted(SCALE_TOPICS)
    for n in range(1, count + 1):
        domain = domains[rng.randrange(len(domains))]
        topic = SCALE_TOPICS[domain][rng.randrange(len(SCALE_TOPICS[domain]))]
        note_id = f"note-archive-{domain}-{n:05d}"
        lines = [SCALE_SENTENCES[rng.randrange(len(SCALE_SENTENCES))].format(t=topic)
                 for _ in range(rng.randint(2, 6))]
        meta = {"id": note_id, "type": "note", "title": f"Archive: {topic} ({n})",
                "created": "2026-03-01", "role": "reference", "state": "rough",
                "authorship": "user"}
        world.events.setdefault(world.as_of, {})[
            f"knowledge/notes/{domain}/{note_id}.md"] = (
            frontmatter(meta, NOTE_FRONTMATTER_KEYS) + "\n\n".join(lines) + "\n")
    world.messages.setdefault(world.as_of, []).append(f"Import {count} archived notes")


# ------------------------------------------------------------------- write
def write_file(root: Path, rel: str, data: bytes, mode: int = 0o644,
               link: str | None = None) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.exists():
        path.unlink()
    if link is not None:
        os.symlink(link, path)
        return
    path.write_bytes(data)
    os.chmod(path, mode)


def commit(repo: Path, date: str, index: int, message: str, identity: dict) -> None:
    stamp = f"{date}T{9 + index // 60:02d}:{index % 60:02d}:00+02:00"
    env = {"GIT_AUTHOR_NAME": identity["name"], "GIT_AUTHOR_EMAIL": identity["email"],
           "GIT_COMMITTER_NAME": identity["name"], "GIT_COMMITTER_EMAIL": identity["email"],
           "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "--no-verify",
        "-m", message, env=env)


def materials_manifest(materials: Path, as_of: str) -> str:
    rows = {}
    total = 0
    for path in sorted(p for p in materials.rglob("*") if p.is_file()):
        rel = path.relative_to(materials).as_posix()
        data = path.read_bytes()
        rows[rel] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        total += len(data)
    header = ("# Generated — do not hand-edit. Rebuild with:\n"
              "#     python tools/materials_manifest.py --build\n")
    return header + dump_yaml({"schema_version": 1, "captured": as_of,
                               "totals": {"files": len(rows), "bytes": total}, "files": rows})


def run_world(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=repo, capture_output=True, text=True,
                          env={**os.environ, "LC_ALL": "C.UTF-8"}, timeout=900)


def build(out: Path, rev: str, scale: int, seed: int, validate: bool) -> dict:
    out = out.resolve()
    try:
        out.relative_to(REPO)
        raise BuildError(f"--out must be outside the LearningOS repository ({REPO})")
    except ValueError:
        pass
    world_meta = yaml.safe_load((CORPUS / "world.yaml").read_text(encoding="utf-8"))
    if rev is None:
        rev = world_meta["product"]["pinned_revision"]
    resolved = resolve_revision(rev)
    product = product_files(resolved)
    if "tools/los.py" not in product:
        raise BuildError(f"revision {rev} has no tools/los.py; not a LearningOS product revision")

    umbrella = out / "LearningOS"
    repo = umbrella / "repository"
    if repo.exists() and any(repo.iterdir()):
        raise BuildError(f"{repo} is not empty; pass a fresh --out or use --force")
    repo.mkdir(parents=True, exist_ok=True)
    materials = umbrella / "materials"
    materials.mkdir(parents=True, exist_ok=True)

    world = World(CORPUS)
    world.build()
    if scale:
        scale_notes(world, scale, seed)

    identity = world_meta["learner"]["git"]
    git(repo, "init", "-q", "--initial-branch=main")
    git(repo, "config", "user.name", identity["name"])
    git(repo, "config", "user.email", identity["email"])
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")

    # 1. the product install at the start of the timeline
    for rel, (data, mode, link) in sorted(product.items()):
        write_file(repo, rel, data, mode, link)
    for rel in skeleton_dirs(product):
        (repo / rel).mkdir(parents=True, exist_ok=True)
        keep = repo / rel / ".gitkeep"
        if not any((repo / rel).iterdir()):
            keep.write_bytes(b"")
    commit(repo, world.start, 0, f"Install LearningOS ({str(resolved)[:12]})", identity)

    # 2. the synthetic timeline
    for date in sorted(world.events):
        for rel, text in sorted(world.events[date].items()):
            if text is None:
                gone = repo / rel
                gone.unlink(missing_ok=True)
                parent = gone.parent
                while parent != repo and parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                continue
            write_file(repo, rel, text.encode("utf-8"))
        msgs = world.messages[date]
        subject = msgs[0] if len(msgs) == 1 else f"{msgs[0]} (+{len(msgs) - 1} more)"
        commit(repo, date, 1, subject, identity)

    # 3. external materials, then the records that describe them
    for path in sorted(p for p in (CORPUS / "materials").rglob("*") if p.is_file()):
        rel = path.relative_to(CORPUS / "materials")
        write_file(materials, rel.as_posix(), path.read_bytes())
    write_file(repo, "records/materials-manifest.yaml",
               materials_manifest(materials, world.as_of).encode("utf-8"))
    for keep in sorted(repo.rglob(".gitkeep")):
        if keep.parent.name != "generated" and len(list(keep.parent.iterdir())) > 1:
            keep.unlink()
    commit(repo, world.as_of, 50, "Record materials inventory", identity)

    # 4. arrivals: outside the installation
    drop = out / "eval-drop"
    drop.mkdir(parents=True, exist_ok=True)
    index = []
    for arrival in world.arrivals:
        (drop / arrival["file"]).write_text(arrival["body"], encoding="utf-8")
        index.append({k: v for k, v in arrival.items() if k != "body"})
    (drop / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")

    report = {"validation": "skipped"}
    if validate:
        result = run_world(repo, "tools/warning_baseline.py", "--update", "--note",
                           "Evaluation world at build time: every warning here is part of the "
                           "synthetic starting state.")
        if result.returncode != 0:
            raise BuildError("world baseline failed:\n" + result.stdout + result.stderr)
        baseline = repo / "operations/validation-warning-baseline.yaml"
        text = re.sub(r"^recorded: .*$", f"recorded: '{world.as_of}'",
                      baseline.read_text(encoding="utf-8"), count=1, flags=re.M)
        baseline.write_text(text, encoding="utf-8")
        commit(repo, world.as_of, 51, "Record validation baseline", identity)
        check = run_world(repo, "tools/validate.py", "--compact", "--no-report")
        tail = [line for line in check.stdout.splitlines() if line.strip()][-1:]
        report = {"validation": tail[0] if tail else "", "validate_exit": check.returncode}
        if check.returncode != 0:
            raise BuildError("world does not validate:\n" + check.stdout[-4000:])
        views = run_world(repo, "tools/generate.py")
        report["generate_exit"] = views.returncode
        if views.returncode != 0:
            raise BuildError("world views do not build:\n" + (views.stdout + views.stderr)[-4000:])
        # A fresh installation starts without views, like a fresh clone.
        for child in sorted((repo / "generated").iterdir()):
            if child.name == ".gitkeep":
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        if git(repo, "status", "--porcelain", capture=True).strip():
            raise BuildError("world has uncommitted changes after verification")
        caps = run_world(repo, "tools/los.py", "capabilities", "--compact", "--json")
        if json.loads(caps.stdout).get("root") != str(repo):
            raise BuildError("world CLI resolved a different repository root")

    head = git(repo, "rev-parse", "HEAD", capture=True).strip()
    record = {
        "builder_version": BUILDER_VERSION,
        "product_revision": resolved,
        "product_revision_requested": rev,
        "corpus_sha256": corpus_digest(CORPUS),
        "scale": scale,
        "seed": seed,
        "timeline": {"start": world.start, "as_of": world.as_of},
        "world_head": head,
        "commits": int(git(repo, "rev-list", "--count", "HEAD", capture=True)),
        "notes": sum(1 for _ in (repo / "knowledge/notes").rglob("*.md")),
        "arrivals": len(world.arrivals),
        "paths": {"repository": str(repo), "materials": str(materials), "drop": str(drop)},
        **report,
    }
    (out / "EVAL-WORLD.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source-rev", default=None,
                        help="product revision (default: pinned in corpus/world.yaml); "
                             "WORKTREE uses the current working tree")
    parser.add_argument("--scale", type=int, default=0, help="add N filler notes")
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--force", action="store_true", help="replace an existing --out")
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args(argv)
    if args.force and args.out.exists():
        target = args.out.resolve()
        if not (target / "EVAL-WORLD.json").exists() and any(target.iterdir()):
            print(f"refusing --force: {target} is not a previous evaluation world",
                  file=sys.stderr)
            return 2
        shutil.rmtree(target)
    try:
        record = build(args.out, args.source_rev, args.scale, args.seed, not args.no_validate)
    except BuildError as exc:
        print(f"build_world: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
