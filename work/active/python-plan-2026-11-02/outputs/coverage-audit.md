# Python fluency coverage audit - final review 2026-11-03

Scope authority: Aram's material-only brief, preserved in `HANDOFF.md` and the current chat. The goal is Python fluency for Stratum; no signature memorisation, interpreter internals or required exercises. This is one existing skill unit, not a taught lecture course.

Package: `build/build_package.py` creates the exact external `state-*/package.yaml` reviewed by the import. The canonical audit destination is `work/active/python-plan-2026-11-02/outputs/coverage-audit.md`.

Review boundary: the current Python module source map and all 10 stages; the local Fluent Python and Effective Python full texts and 3e contents sample; existing depth-drill and handbook sources; candidates explicitly named by the handoff; all existing stage URLs; and the primary documentation pages in the proposed stages. Stratum remains external unmanaged code: only the named code paths are checked. Handoff observations about the earlier code-frequency audit are inherited evidence, not a repeated repository scan.

## Local material inventory

| Material | Disposition | Evidence and reason |
|---|---|---|
| Fluent Python 2e, `material://source-fluent-python/fluent-python.pdf` | Selected spine, exact sections | PDF outline, verified section starts and inspected same-page boundaries; avoid bytecode, closure cells, garbage collection, descriptors, metaclasses and memory benchmarks. Relevant closure page rendered and inspected. |
| Effective Python full text, `material://source-slatkin-effective-python/effective-python.pdf` | Helpful optional items | 2e, copyright 2020, 90 items. Item starts verified against the local PDF, ranges derived to the next item. Copyright page rendered and inspected. Every new EP placement is helpful-now; none is required. |
| Effective Python 3e contents sample | Reference-only, unplaced | Contents/sample, not the readable 2e full text. No 3e item numbering is used in the new path. No purchase required. |
| Python depth drills, all existing notebooks and guides | Deferred | Preserve old rows, notes and attachments; no exercises or answer keys are inspected, authored or repaired in this continuation. Earlier content judgments are the handoff's observations. |
| Python Data Science Handbook | Reference-only | Preserve the existing source-map entry, with an explicit reason: older data-library examples are not the Python-language spine. No additional handbook reading is assigned. |
| Architecture Patterns with Python | Deferred | Preserve the existing source and optional architecture stages; web-app architecture is outside this reading goal. |
| Automate the Boring Stuff | Out-of-scope | Handoff candidate; beginner automation material is outside the selected intermediate language path. |
| Corey Schafer OOP transcripts | Out-of-scope | Handoff candidate; the tutorial plus selected class chapters provide the required class foundation here. |
| Python/data-science cheat sheets | Out-of-scope | Retain where already owned; not the language-reading spine. |
| Polars book | Out-of-scope | Owned by the separate Polars learning plan. |

The local file appendix below comes from the recorded materials manifest. It is metadata inventory, not a claim to have reread excluded exercises or every handbook notebook. Selected PDF byte hashes are recorded in `build/pdf-evidence.json`. No material file was modified.

## Linked web material inventory

Every row below is a distinct primary URL in the new package. The named locator defines scope; an HTTP success alone is not a content-quality verdict. Observations and extracted page text are retained in `build/web-evidence.json` and `build/web-observations/`. Baseline Python pages are pinned to 3.11; the final delta topic uses each version's own release notes.

| URL | Topic | Disposition | Exact locator | Verified |
|---|---|---|---|---|
| https://docs.python.org/3.11/tutorial/datastructures.html | 1 | selected reading; HTTP 200 | Page "Python tutorial - Data Structures": Sections 5.1-5.6; stop before 5.7 More on Conditions | 2026-11-02 |
| https://docs.python.org/3.11/library/collections.html | 1 | reference-only; HTTP 200 | Page "Python library - collections": Counter, defaultdict and deque | 2026-11-02 |
| https://docs.python.org/3.11/library/itertools.html | 1 | reference-only; HTTP 200 | Page "Python library - itertools": Function summary table; look up individual functions only when needed | 2026-11-02 |
| https://nedbatchelder.com/text/names.html | 2 | helpful optional; HTTP 200 | Page "Facts and myths about Python names and values": Written article: names, assignment, rebinding, mutation and aliasing; stop before any garbage-collection discussion | 2026-11-02 |
| https://docs.python.org/3.11/library/functools.html#functools.wraps | 4 | selected reading; HTTP 200 | Page "functools.wraps": functools.wraps section | 2026-11-02 |
| https://docs.python.org/3.11/tutorial/classes.html | 5 | selected reading; HTTP 200 | Page "Python tutorial - Classes": Sections 9.1-9.7; skip 9.8+ iterators until topic 9 | 2026-11-02 |
| https://docs.python.org/3.11/library/dataclasses.html | 6 | selected reading; HTTP 200 | Page "dataclasses documentation": Module example; dataclass decorator options init, repr, eq, frozen, slots; field default_factory; post-init and ClassVar | 2026-11-02 |
| https://docs.python.org/3.11/howto/enum.html | 6 | selected reading; HTTP 200 | Page "Enum HOWTO": Opening Weekday/Color examples; Programmatic access; Iteration; Comparisons; Allowed members; Functional API; IntEnum note | 2026-11-02 |
| https://docs.python.org/3.11/reference/datamodel.html | 7 | reference-only; HTTP 200 | Page "Python data model reference": Basic customization: __repr__, __str__, __eq__, __hash__, __bool__; Customizing attribute access | 2026-11-02 |
| https://docs.python.org/3.11/tutorial/modules.html | 8 | selected reading; HTTP 200 | Page "Python tutorial - Modules": Sections 6.1-6.4; package and import examples; skip 6.1.3 Compiled Python files | 2026-11-02 |
| https://docs.python.org/3.11/reference/import.html | 8 | reference-only; HTTP 200 | Page "Python import reference": 5.2 Packages; 5.4.2 Submodules; 5.7 Package Relative Imports | 2026-11-02 |
| https://docs.python.org/3.11/library/unittest.mock.html#where-to-patch | 8 | helpful optional; HTTP 200 | Page "unittest.mock - Where to patch": Where to patch section | 2026-11-02 |
| https://typing.python.org/en/latest/guides/modernizing.html | 10 | selected reading; HTTP 200 | Page "Modernizing superseded typing features": Introduction, built-in generics, union syntax, TypeAlias and TypeVar notes; check the stated minimum version for each feature | 2026-11-02 |
| https://docs.python.org/3.11/library/typing.html | 10 | reference-only; HTTP 200 | Page "typing reference": Any, Callable, Iterable, TypeVar, Generic, Protocol, TYPE_CHECKING and get_type_hints | 2026-11-02 |
| https://typing.python.org/en/latest/reference/generics.html | 10 | reference-only; HTTP 200 | Page "Typing - Generics": Generic classes and TypeVar; distinguish Python 3.11 forms from 3.12+ syntax | 2026-11-02 |
| https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html | 10 | reference-only; HTTP 200 | Built-in types, collections, functions, classes and protocols; stop before advanced examples | 2026-11-02 |
| https://docs.python.org/3.11/library/abc.html | 11 | reference-only; HTTP 200 | Page "abc reference": ABC and abstractmethod examples only | 2026-11-02 |
| https://docs.python.org/3.11/library/functools.html#functools.singledispatch | 11 | selected reading; HTTP 200 | Page "functools.singledispatch": singledispatch: definition, register examples and dispatch on first argument | 2026-11-02 |
| https://typing.python.org/en/latest/reference/protocols.html | 11 | helpful optional; HTTP 200 | Page "Typing - Protocols": Simple user-defined protocols; protocol members; structural subtyping | 2026-11-02 |
| https://docs.python.org/3.11/tutorial/errors.html | 12 | selected reading; HTTP 200 | Page "Python tutorial - Errors and Exceptions": 8.1-8.8; exception groups in 8.9 are optional background | 2026-11-02 |
| https://docs.python.org/3.11/howto/logging.html | 12 | selected reading; HTTP 200 | Page "Logging HOWTO": Basic Logging Tutorial; Advanced Logging Tutorial (flow and configuration); Configuring Logging for a Library | 2026-11-02 |
| https://docs.python.org/3.11/library/unittest.html | 13 | selected reading; HTTP 200 | Page "unittest - Basic example and TestCase": Basic example; Organizing test code; Distinguishing test iterations using subtests; setUp, tearDown, assertEqual and assertRaises examples | 2026-11-03 |
| https://docs.pytest.org/en/stable/how-to/fixtures.html | 13 | selected reading; HTTP 200 | Page "pytest - Fixtures": Requesting fixtures; scope; autouse; yield teardown | 2026-11-02 |
| https://docs.pytest.org/en/stable/how-to/parametrize.html | 13 | selected reading; HTTP 200 | Page "pytest - Parametrization": pytest.mark.parametrize; parametrized fixtures; basic examples | 2026-11-02 |
| https://docs.pytest.org/en/stable/how-to/monkeypatch.html | 13 | selected reading; HTTP 200 | Page "pytest - Monkeypatch": Patching functions, attributes, environment variables and dictionaries | 2026-11-02 |
| https://docs.pytest.org/en/stable/how-to/tmp_path.html | 13 | selected reading; HTTP 200 | Page "pytest - Temporary paths": The tmp_path fixture and basic Path example | 2026-11-02 |
| https://docs.pytest.org/en/stable/how-to/assert.html | 13 | selected reading; HTTP 200 | Page "pytest - Assertions and exceptions": Assertion introspection and Assertions about expected exceptions | 2026-11-02 |
| https://docs.pytest.org/en/stable/how-to/unittest.html | 13 | helpful optional; HTTP 200 | Page "pytest - unittest-based tests": Opening overview; pytest features in unittest.TestCase subclasses | 2026-11-03 |
| https://docs.python.org/3.11/library/unittest.mock.html#where-to-patch | 13 | helpful optional; HTTP 200 | Page "unittest.mock - Where to patch": Where to patch section | 2026-11-02 |
| https://docs.astral.sh/uv/guides/projects/ | 14 | selected reading; HTTP 200 | Page "uv - Working on projects": Project structure; managing dependencies; running commands; building distributions for context | 2026-11-02 |
| https://docs.astral.sh/uv/concepts/projects/sync/ | 14 | selected reading; HTTP 200 | Page "uv - Locking and syncing": Locking and syncing; automatic lock/sync; extras and dependency groups; exact versus inexact sync | 2026-11-02 |
| https://packaging.python.org/en/latest/specifications/pyproject-toml/ | 14 | reference-only; HTTP 200 | Page "pyproject.toml specification": [build-system], [project], optional-dependencies and [tool] tables | 2026-11-02 |
| https://www.maturin.rs/tutorial.html | 14 | helpful-now; HTTP 200 | Page "maturin tutorial": Introduction; mixed Python/Rust project layout; develop versus build | 2026-11-02 |
| https://docs.python.org/3.11/whatsnew/3.11.html | 15 | selected reading; HTTP 200 | Page "What's New in Python 3.11": Summary; improved error locations; exception groups and except* as recognition only; typing.Self and typing changes | 2026-11-02 |
| https://docs.python.org/3.12/whatsnew/3.12.html | 15 | selected reading; HTTP 200 | Page "What's New in Python 3.12": Summary; new type parameter and type alias syntax for recognition only; f-string syntax improvements | 2026-11-02 |
| https://docs.python.org/3.13/whatsnew/3.13.html | 15 | selected reading; HTTP 200 | Page "What's New in Python 3.13": Summary; improved errors and interactive interpreter; typing deprecations affecting annotations | 2026-11-02 |
| https://docs.python.org/3.14/whatsnew/3.14.html | 15 | selected reading; HTTP 200 | Page "What's New in Python 3.14": Summary; deferred evaluation of annotations (PEP 649/749); template string literals for recognition only | 2026-11-02 |
| https://docs.python.org/3.15/whatsnew/3.15.html | 15 | selected reading; HTTP 200 | Page "What's New in Python 3.15": Summary; UTF-8 default; explicit lazy imports; frozendict, sentinel and unpacking in comprehensions for recognition only | 2026-11-02 |
| https://arxiv.org/abs/2603.03589 | 16 | helpful optional; HTTP 200 | Page "Stratum paper - context only": Local Stratum paper, sections 3-4.3, PDF pp. 3-5; read only if architecture terms obscure the Python | 2026-11-02 |

### Existing linked material disposition

All prior stage URLs remain reachable from the preserved optional stages. Existing URL checks in the handoff are dated 2026-11-02; this continuation does not pretend to have repeated content review of excluded labs. An overlapping URL may have a narrower new placement above.

| Existing URL | Disposition and reason |
|---|---|
| https://arxiv.org/abs/2603.03589 | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/c-api/stable.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/howto/logging-cookbook.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/library/asyncio.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/library/concurrent.futures.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/library/graphlib.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://docs.python.org/3/tutorial/errors.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/HypothesisWorks/hypothesis | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/cosmicpython/book | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/encode/httpx | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/hynek/structlog | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/networkx/networkx/blob/main/networkx/algorithms/dag.py | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/pydantic/pydantic | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/pytest-dev/pluggy | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://github.com/pytest-dev/pytest/blob/main/CONTRIBUTING.rst | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://packaging.python.org/en/latest/specifications/pyproject-toml/ | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://packaging.python.org/en/latest/tutorials/packaging-projects/ | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://people.csail.mit.edu/matei/papers/2015/sigmod_spark_sql.pdf | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://pyo3.rs/ | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://skrub-data.org/stable/reference/data_ops.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://www.cosmicpython.com/book/preface.html | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |
| https://www.maturin.rs/ | Preserved on a deferred stage; old project/lab scope does not become a new requirement. |

### Supporting references and candidates

The mypy cheat sheet remains an optional external lookup. Typing's generics/protocol pages support the book. The pyproject specification belongs to PyPA and the maturin tutorial belongs to maturin; they are independent external pointers, not falsely attributed to uv. Stratum code paths are likewise external pointers rather than a registered managed repository. The Stratum paper is optional architecture context only. Real Python's decorators primer remains excluded because the prior audit could not verify automated access and the selected book already covers the topic.

## Current/prior and duplicate reconciliation

- The original 10 stages remain in their original relative order after the 16 new stages. Each stage and all its rows are deferred with a reason. IDs, statuses, old notes, attachments, progress and feedback are preserved.
- The diagnostic, repair list, optimizer theory, rewrite project and contribution loop cease to define the required path. Nothing is deleted and no achievement is inferred.
- Repeated Effective Python Item 38 has two purposes (functions as interfaces, then interfaces/dispatch); it is optional in both places and can be read once.
- The full Effective Python source's intake title/year are corrected to distinguish the 2020 2e full text from the 3e contents sample. Existing evaluations, crosswalks and other modules' placements are not rewritten.
- FP Ch 9 pp340-341 contain a disassembly sidebar; p344 contains closure-cell inspection. Their exclusion is explicit. The property material stops before descriptor construction; slots omit the memory benchmark. FP pp567-570 contain a now-outdated annotation forecast and are replaced by current official typing guidance.
- No future edition purchase or a claim that the existing book is the latest edition is needed. The Python 3.11 floor is verified from Stratum's pyproject.toml. 3.12+ syntax is recognition-only when incompatible with that floor.
- Five old Stratum path strings are corrected only in plan fields: the old ir base/ops paths and numeric/algebraic/CSE rewrite paths. Unit notes and orphan notes stay unchanged.

## Unit knowledge and material matrix

| # | Topic | Required spine | Optional/supporting material |
|---|---|---|---|
| 1 | Everyday data structures and expressions | Fluent Python selected PDF pages 55-67, 77-80, 86-88, 108-110, 113-124, 131-140; Python tutorial - Data Structures | EP 2e Items 5, 6, 7, 8, 13, 14, 16, 17, 27, 28; Python library - collections; Python library - itertools |
| 2 | Names, identity and mutation | Fluent Python selected PDF pages 232-248, 80-85 | EP 2e Items 24; Facts and myths about Python names and values |
| 3 | Functions, scope and closures | Fluent Python selected PDF pages 262-279, 338-340, 342-343, 345-347 | EP 2e Items 21, 22, 23, 25, 38 |
| 4 | Decorators and registration | Fluent Python selected PDF pages 334-338, 347-350, 359-362; functools.wraps | EP 2e Items 26 |
| 5 | Classes and inheritance | Fluent Python selected PDF pages 394-399, 412-414, 419-420, 518-529, 540-543; Python tutorial - Classes | EP 2e Items 37, 39, 40, 42 |
| 6 | Dataclasses, properties, enums and slots | Fluent Python selected PDF pages 194-198, 203-205, 209-216, 220-221, 887-889, 414-416, 418; dataclasses documentation; Enum HOWTO | EP 2e Items 44, 45 |
| 7 | Special methods and attribute handling | Fluent Python selected PDF pages 33-46, 404-407, 900-902 | EP 2e Items 75; Python data model reference |
| 8 | Modules and imports | Python tutorial - Modules | EP 2e Items 85, 86, 88; Python import reference; unittest.mock - Where to patch |
| 9 | Iterators, generators and with | Fluent Python selected PDF pages 624-645, 649-660, 662-668, 688-698 | EP 2e Items 30, 31, 33, 36, 66 |
| 10 | Type hints | Fluent Python selected PDF pages 284-326, 571-574; Modernizing superseded typing features | typing reference; Typing - Generics |
| 11 | Interfaces and dispatch | Fluent Python selected PDF pages 462-470, 472-488, 496-506, 354-358; functools.singledispatch | EP 2e Items 38, 43; abc reference; Typing - Protocols |
| 12 | Errors and logging | Python tutorial - Errors and Exceptions; Logging HOWTO | EP 2e Items 20, 65, 87 |
| 13 | Reading Python tests | unittest - Basic example and TestCase; pytest - Fixtures; pytest - Parametrization; pytest - Monkeypatch; pytest - Temporary paths; pytest - Assertions and exceptions | EP 2e Items 76, 78, 79, 80, 70; pytest - unittest-based tests; unittest.mock - Where to patch |
| 14 | Projects, environments and tooling | uv - Working on projects; uv - Locking and syncing | Stage pointers as listed |
| 15 | Reading newer Python while keeping a 3.11 floor | What's New in Python 3.11; What's New in Python 3.12; What's New in Python 3.13; What's New in Python 3.14; What's New in Python 3.15 | Stage pointers as listed |
| 16 | Read Stratum using the Python topics | Named Stratum files, read only | Stratum paper - context only |

## Explicit exclusions and unresolved gaps

- No required practice, diagnostic, cold reconstruction, portfolio work, signature tables, answer keys or Rust implementation.
- No interpreter implementation, bytecode, refcounts, closure-cell investigation, virtual-subclass machinery, descriptors, metaclasses, send/throw or asyncio path.
- HTTPX, structlog, NetworkX, Hypothesis, pluggy, pydantic, Catalyst and packaging/ABI labs stay reachable in their existing deferred stages. No new upstream-state claims about them are needed.
- Existing unit notes still describe the former goal, and orphan stage notes may contain obsolete paths. They are intentionally preserved pending a separately reviewed note revision, not passed off as current plan guidance.
- No learner source selections, results or mastery are inferred by this package.
- Full book prose is not exhaustively re-audited. Verified starts, explicit same-page boundaries, current docs and source hashes make the chosen reading reviewable; they do not prove every sentence is current.

## Completeness

All five original source-map entries and all 81 original resource rows are retained. Every existing URL has a disposition above; no hidden removal is used to satisfy the material-only scope. The map adds 16 topic knowledge nodes and one clearly labelled optional legacy-path node for the 10 deferred stages. Selected managed materials have rich routes; the three preserved deferred/reference sources use plain unit-adoption edges, without invented new covers claims about excluded material. Independent external code/tool lookups remain honest reference pointers. The same mock lookup in imports/testing shares one route covering both topics. Required material, helpful reading and reference-only pages are visibly different. `plan_template_version: 1` comes from the canonical generator, and the preflight/receipt reports are the evidence for routing, lineage, warnings and final file scope.

### Recorded local file appendix

| Manifest path | SHA-256 | Disposition |
|---|---|---|
| `software/python/automate-boring-stuff/Sweigart_Automate-the-Boring-Stuff.pdf` | `5a7d3a89f2e0a02668da97e2bd6975ee83db2326458e5ce8853959a2790c3338` | out-of-scope beginner material |
| `software/python/corey-schafer-oop/transcript/3ohzBxoFHAY.md` | `cecf17adce19f34aca573af850d40366cbce842a29dfd8e3109c258490b91fea` | out-of-scope candidate |
| `software/python/corey-schafer-oop/transcript/BJ-VvGyQxho.md` | `ad2eeac4e71a0d5ba148803544e9ee01ad6987b7457948823e6942659f9b2c9c` | out-of-scope candidate |
| `software/python/corey-schafer-oop/transcript/RSl87lqOXDE.md` | `2dce4ab232f817cf6d6651e2052f684380d2f262c0f0895ef84fa3b5b7a33e36` | out-of-scope candidate |
| `software/python/corey-schafer-oop/transcript/ZDa-Z5JzLYM.md` | `862e5fe22bf83aecf57816e73f3eef1b82bd7e2ddd5dc91a91424499a0d1ab97` | out-of-scope candidate |
| `software/python/corey-schafer-oop/transcript/jCzT9XFZ5bw.md` | `83f264abc75096e3786257e5217fced22d1f8134a03609b4fa3abba625ca8b59` | out-of-scope candidate |
| `software/python/corey-schafer-oop/transcript/rq8cL2XMM5M.md` | `83a661b08f82ae98b4acdd751cdded3c1c9dabbaff04cedbd0ddceef731020cb` | out-of-scope candidate |
| `software/python/fluent-python/fluent-python.pdf` | `db97c77518c68ce3db19da8f65e9f8dd8f9494fcbba59dddb0ed1796973f7e35` | selected sections |
| `software/python/pydata-handbook/PythonDataScienceHandbook/README.md` | `3b0013eeaa84fb1a77078d898e50e24f827ed9443ee8e832979a9f5361459466` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/00.00-Preface.ipynb` | `4a9dd14420392fdc6ae381bfff9b7a0561d7d219a4751c85d870029bbb71dfcf` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.00-IPython-Beyond-Normal-Python.ipynb` | `e90d86c143b188506c551d85bb8c7d3bd540d94b8b0c85582f880b0bc0ecbdb9` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.01-Help-And-Documentation.ipynb` | `02fe10e90a28fb097d77a368402846fba428dda885df0ea57259c4cb0a1673c8` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.02-Shell-Keyboard-Shortcuts.ipynb` | `a7dfaaa1ba8e5d01d9862ec9e7eabbe82021073c9accb3ddbfc9c17dc48a227e` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.03-Magic-Commands.ipynb` | `4b5198787f06be28dd575d889d02b29da12658d1140e0c2116845997bdac244f` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.04-Input-Output-History.ipynb` | `e9a76b91ed72060bb6ce3681ca92996031ba13523eb8e86c900e6812898f9f09` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.05-IPython-And-Shell-Commands.ipynb` | `b3263f38c3519a258d5b24612b9be5397f4735e332b525ea0f7363f63570c99c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.06-Errors-and-Debugging.ipynb` | `ba4e51c0331047063c5d6ee62dd83d2077086dcb43da5bdd88b3e74dedfc61e1` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.07-Timing-and-Profiling.ipynb` | `f6217a7964f966848fda440d6b5019780e65d8f646152c6e00800607a5de949d` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/01.08-More-IPython-Resources.ipynb` | `826f69b1a018ee7072a2342b9d67d39320a5eec2f047d63f47b9094075d2a0a2` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.00-Introduction-to-NumPy.ipynb` | `9f8a34c954b462480fbf8e3b8b020e886bb974a6ee165921e733b87290364c8c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.01-Understanding-Data-Types.ipynb` | `e6aef0d9a235b0f6081b1fd79c4b43430983b57b79c2524f9ddad289704c436e` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.02-The-Basics-Of-NumPy-Arrays.ipynb` | `556f718dba9187ce81bffeb2e2ffe7dc5cdabb7deac944d20f031afe91eeb915` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.03-Computation-on-arrays-ufuncs.ipynb` | `8978311c16a97c498fbce379d916d4ecbfd22ec2b530c279cc25d527d6018938` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.04-Computation-on-arrays-aggregates.ipynb` | `a5367e2c6a3a2e8947ce4e4d02c5a26e5c1760e28fca6dc27d22e5f3244db193` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.05-Computation-on-arrays-broadcasting.ipynb` | `26782a3127de8dc3a9c42b0b9c3266a19ef76aa5b8e864e5efd3ad7deb34a362` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.06-Boolean-Arrays-and-Masks.ipynb` | `b97b8bcf3bf8faefd2c97eac92df797ceac6cbaf50ea81600be8f4edae3aacc7` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.07-Fancy-Indexing.ipynb` | `cdfc01cbc9d670aae7dc448227ef48d85036620d6f091a53118ea208fe270cb8` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.08-Sorting.ipynb` | `f79329a848b1b1b5ff870dd68a4c73669333ee8982b5a93d851bd0c7be0547ea` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/02.09-Structured-Data-NumPy.ipynb` | `39c8459e7e5e5ed568141595b93369b2f5d9cda04fdb24cd7d3e5bade28855b1` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.00-Introduction-to-Pandas.ipynb` | `1b909dd24261160dda300ed9ddf880c93b3d1590cb4a281e90f9a2c11e3ad3af` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.01-Introducing-Pandas-Objects.ipynb` | `aafa916ead1d807c403ac5c530cb229499195a96d8de866f04466e769cc1bdef` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.02-Data-Indexing-and-Selection.ipynb` | `70d00d4824b58c88aae867809ae3f05f8b0704f168820b09e866d238d1f2564c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.03-Operations-in-Pandas.ipynb` | `abfe26a5a3f342e4cf95860170d3f378f10375abb1f372430b2d9f9a0499f9df` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.04-Missing-Values.ipynb` | `26c55e6f51bb406703e16011f722d0d7f8502426c5f14d93dec525fbae07f521` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.05-Hierarchical-Indexing.ipynb` | `0584fcac0f3a44523d844444ef808571b33be4152ff1afadbb338e26f8bbacf0` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.06-Concat-And-Append.ipynb` | `485559ab2e5035dd6d0e927226801fd286b47cd0843dd3ca5f7e2ff7cce3e580` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.07-Merge-and-Join.ipynb` | `0d71fee1082d5b1e3886987a3cbb8f71d25ee09bbc3a2db2b87958c26b6e6042` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.08-Aggregation-and-Grouping.ipynb` | `fcfd81b5607e9ca0331ac96568d1141bab977e8f57d5f644b64136ccf41ece27` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.09-Pivot-Tables.ipynb` | `ca4361b5e0b5d29f695bd537c41e2fc3eaec0d1149893e35db159bc17c357bb9` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.10-Working-With-Strings.ipynb` | `f1d500ec88dafa72b06156565282481b8f14cd6db5dea42f94f5acb5ab9695ed` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.11-Working-with-Time-Series.ipynb` | `7a30ebac052ed41aaa6bb1a22c6bcfca687839ca9a49e534ff49a8c4fd2791d3` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.12-Performance-Eval-and-Query.ipynb` | `d7b667ce895ee99780dd335b8393dfe450f58ac60ea5f7b259fb9223c3a175ae` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/03.13-Further-Resources.ipynb` | `d1841f0786504889bb136e60a0b0ef8e16e594f5f65cf59fa7819521d613f60e` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.00-Introduction-To-Matplotlib.ipynb` | `2739b47a80d36a2fdd72cbd383bb51f5bf7b39fa92fd234a340340d4fe74f6c6` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.01-Simple-Line-Plots.ipynb` | `2290c31c987c488fcee563c7238c972f1375d1983877a802ec9fbb5666c34f96` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.02-Simple-Scatter-Plots.ipynb` | `0a8eedf42ad76cdad38f1cab4d9f2bb38faec1d8b699059d1bc2a3d716b3f32c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.03-Errorbars.ipynb` | `13f53dd617266711abac02d2500138227485552a301f8d14dc452c4df56434f7` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.04-Density-and-Contour-Plots.ipynb` | `e8a4586baa504f9bd159d065d9415ae3a024cb458523dc50b443b34d0712e009` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.05-Histograms-and-Binnings.ipynb` | `6cb27a61db92018eb411fea1cc9ce4a114a0609cde53d86b69bebf550ef0e4fb` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.06-Customizing-Legends.ipynb` | `c1fdd582f98feb6337e6e4cb44d7ec37dd175d3199399cf40b6229524a122a19` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.07-Customizing-Colorbars.ipynb` | `3082858294fc980d262b00cc801df5a4db1cb819e250e3623f8d2fa14d67728a` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.08-Multiple-Subplots.ipynb` | `f57dd14fd61dbe41072c6537e8e35084aae818e971a3e7d8df03f43fdaa479fd` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.09-Text-and-Annotation.ipynb` | `271312adffb558a2bda206d94f814aff808fabe97d4a52cd0376468e8f05fca3` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.10-Customizing-Ticks.ipynb` | `16575104be68f9815781877e6af11ff712915b9224a9de357328d6989517daba` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.11-Settings-and-Stylesheets.ipynb` | `7a691d2072761cb55d87a319f120d1ef985b4433565cf016866c663b8d920bf4` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.12-Three-Dimensional-Plotting.ipynb` | `cb10d921c36e9d6b5025da177145f7e9227ea09c3b9a858272e3d9ae49d5518b` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.14-Visualization-With-Seaborn.ipynb` | `ff05a6dd6684de0954063f9e22f1d105ac6cd10b8193bdd689ac076ecb05b2d5` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/04.15-Further-Resources.ipynb` | `227b8a5905ff2411136aafefaf434ea4a28fa71121963ce51ebccb9412a650d6` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.00-Machine-Learning.ipynb` | `890692d264e109345d65d093415cdc4b804c6e1e834d3c9628b59198c386db86` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.01-What-Is-Machine-Learning.ipynb` | `f750ee8c6e6f0cc5716b3598be6fd7e9cb0d45560ce678c9acbfa57f4d8dff7a` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.02-Introducing-Scikit-Learn.ipynb` | `b2f66e5cc002bd163feb59f9b8600ad5b79dea6021bfc6a1db8e5b71b33a226b` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.03-Hyperparameters-and-Model-Validation.ipynb` | `57c10ede19bd471c910449cda1a2afc9e2bd1a2dc3838d1a6f24fdc3cf16291f` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.04-Feature-Engineering.ipynb` | `92131841553e91d293954ad6c5faf8c25826c325617fbb30d2467be9556030bb` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.05-Naive-Bayes.ipynb` | `432266aa9d4fe95f4bc0acea3251bdac2cd277a1f5cdab51b2b0e1d6b316deaa` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.06-Linear-Regression.ipynb` | `a726ef7aee1252f3389b60fd6da4f7d5114a572353c50dd35380aecae54d95c8` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.07-Support-Vector-Machines.ipynb` | `8f01bffbe7f86c160fcbe89f4549b1650d262adc0e76b354719c41eec15af0a6` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.08-Random-Forests.ipynb` | `cc2c5c63686602c8af079e69d02fd37bc6da7202be94bb11a40a4133b88525f8` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.09-Principal-Component-Analysis.ipynb` | `fa00993593486ca2d2445bf4781eba2ea79bb07f3360fa9456d67f573b9da9f2` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.10-Manifold-Learning.ipynb` | `f7408c08b14aab1df8901e1cd741aba965ad866a3e2978837c775ac28bbc18bd` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.11-K-Means.ipynb` | `fe13a8aa33b3bc1ce52da2c8d72747d8f1bbd320bcc18598f5338b9d07592ee3` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.12-Gaussian-Mixtures.ipynb` | `9438d483e156738ba8d581e54f150590061ff6fbe6147cb38ab56ae0449c07e6` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.13-Kernel-Density-Estimation.ipynb` | `b02006c0cc403a0effa4b8824e3dc60e607d2c7390729099806dc7437199055b` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.14-Image-Features.ipynb` | `07ff8f8b63bca77399596a3bd86a2f9f830d08717fa123b098d4d513a83aed14` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/05.15-Learning-More.ipynb` | `9262221390e9857a7c5a5846aa9a745b68e3e144ff6d7fef1f237036d45e1c43` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/06.00-Figure-Code.ipynb` | `24f02d5c1cec9f243eade9be59ee73f41772f1749761f8854f77bf0dc5d2a489` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/Untitled.ipynb` | `4a62b68a633d79c53a6fd8893e8ea42dcf2b9a8a3e907b1b9861661f04f21517` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/data/births.csv` | `2b3d632fcae2dbfd60df24fda0b5488584722dc62f7f8919767c5a6ed5ebfc9c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/data/president_heights.csv` | `9a7561cac88432cbe3d88c2ba5cfa0acee9a609329330f5a8a18a4689cf31790` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/data/state-abbrevs.csv` | `884b3a1974f45f941822b19b6b37552947e9a35ee149d8ce7f37bddf72cd8724` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/data/state-areas.csv` | `f571aeafd4e45c8788e5e90f1ba71716d5fbe2a53d6a97c8e50d4056160bd650` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/data/state-population.csv` | `24f24c2b36cafc1836b309534f92dd44389977373544dc880c5f7b8cb369180a` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/02.05-broadcasting.png` | `bc319a05efccc83365a6fbba879b8f96f0daa4f91948049ef88d0ace9dce4996` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/03.08-split-apply-combine.png` | `f97b835e5aef90d33ab0beaccde1e19597002c6f02b53530d256286263192ae4` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-classification-1.png` | `80157757255fba6549bcb9e6c658a219509785668c2389e7cfb0635c2d0fe5cd` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-classification-2.png` | `9949c2312b99a5aadb94b902610cc535a5486e18d7f9990ee63244d6b29bb280` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-classification-3.png` | `9cfa5485b59faff9fc2b94a9a93b0d57eaa02966ef03e814f43a73b863fa90eb` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-clustering-1.png` | `2b571a814ce0600c8b27dce3a3e82b398f7e6ef010eba6183477225840aba0af` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-clustering-2.png` | `6f63f2b12b945f1d765503082b16a3e424026d942bf585eb1fe2b1538d0dd456` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-dimesionality-1.png` | `ffe2fd09868299053b3fa3a59d8d572ceaa1ab83e906265912f3155eb3468f5d` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-dimesionality-2.png` | `d702baf900d373d82a4e78b2fcda08ab4c1a82d1dab4ebf010fe7eafc861d1af` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-regression-1.png` | `5a6c0eb674fa4d9f1f3d0ffb4c2af3cb2ba59508a6230874a86b06e1e23e1fe4` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-regression-2.png` | `1f4dc7f3c68d545416afaa48979b0fa720928391e1169d0de8689d0111cfd6c0` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-regression-3.png` | `a619da5b7cde46c38adfe45dd5e5891f52725056d9a2650d9ce8c3caca5732aa` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.01-regression-4.png` | `8044af87f46c66b73de51e253ac295faa4024e48379d7fbd997584241ca282bb` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.02-samples-features.png` | `1495eb8e751852895752393022b8351c886ae03d31dc775b411b7ab5e79df252` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-2-fold-CV.png` | `60780a3d2d4ef1b5379a168fe123a64552ed1fda474872ae300de1f8c386504c` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-5-fold-CV.png` | `b82aac00cec1b58a78df2c51cc9fdcfe5815cf791c0cf51044f5d54777b21bbe` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-bias-variance-2.png` | `32623c141d08fa033a15473cdf51e958e72a56524744193b27408a827bd2e65e` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-bias-variance.png` | `df7e1d486cf8c77e475874e1c3ce4bb08e7085e6715f046d6448381e0399f0db` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-learning-curve.png` | `75864dc92ee1b83a23281b81f80e16134cb5243b9fef0e56128d4d0013b1c33e` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.03-validation-curve.png` | `21313e1791c428fcca7a868b695131070f9db6f4d75bfcc39043e5247fcd47fb` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.05-gaussian-NB.png` | `d50c605f6af6f852a7393afbf2a31b193295227295696bb37aa6c8e6ac356e84` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.06-gaussian-basis.png` | `9af45deead6f3b3e3b73da1158f733e4ca52402c9afc57a2db5884eb23d76fc5` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.08-decision-tree-levels.png` | `721e029ff68a36a41c379c60bb804a938114e37f4357893f5fa81ee6b4e2b311` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.08-decision-tree-overfitting.png` | `4a56e98aa633f1fe022f18fe3c173d5d3723d6f333a1e2c2942b5fb5546077ac` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.08-decision-tree.png` | `5f95be6fc136c57292cfffac1ab2239e75a40b2c2675ab61b558e1adb8e882ed` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.09-PCA-rotation.png` | `f3ef65e6c2adc29869cbbf51f4cc7e844daa1d7eda669f5d3d2221782e9c98e7` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.09-digits-pca-components.png` | `958095b63e56048b75dc27dfb86cf1b8c52acee3eb9ded5861130a9633065165` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.09-digits-pixel-components.png` | `4acc90b29b21efc0abbbc268edd2a688d4a1ae9405eaaa668a1ecaa765564601` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.10-LLE-vs-MDS.png` | `bd60db63c5f09ccc89066c6c166e0b55224586f2264ba5f63c9607be2ed6c0f0` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.11-expectation-maximization.png` | `1822bdcae4fd07105888951e64cbbf227ddc49d0c8d8345db063d807c1b17516` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/05.12-covariance-type.png` | `1e1f676f674f3296e3ee59c56f76621a23cf2bab292543452ebbe0016ab947b3` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/Data_Science_VD.png` | `876d9aa65637c2fb49618af6dedb882f244a528beaec98f77e46882fba223dac` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/PDSH-cover-small.png` | `d055132265433e7174ef2e3ec3bf107a20895e90d0014568a15c766566dcd227` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/PDSH-cover.png` | `d31eb8e09dfe68b26c6beb84136f1ec815dbc97f26cfb96a571aef6820204bbc` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/array_vs_list.png` | `95bfd2e56bfba17d3c58248a364443dc3ac7724e455e0950c526845ea73a6577` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/figures/cint_vs_pyint.png` | `05f771f136daa33df982ad2f5a852e5cba8326233dd719e7b6f46b542e79be88` | reference-only; no new placement |
| `software/python/pydata-handbook/PythonDataScienceHandbook/notebooks/helpers_05_08.py` | `e558f5f0369694a011b178c215a1de041db0e1b14c9c10607cdde280670d718f` | reference-only; no new placement |
| `software/python/python-cheatsheets/Graphic-Design_cheatsheet.pdf` | `145a30f02e0bf933ef5d1488acbc1c58e8815261659d21b25d9b3014d4280b91` | out-of-scope candidate |
| `software/python/python-cheatsheets/Keras_cheatsheet.pdf` | `2c5d523fd23ff51992eb270494c46dc340531d45ea352b06c00002a4140ecb18` | out-of-scope candidate |
| `software/python/python-cheatsheets/NumPy_cheatsheet.pdf` | `d14c9ef90c8348224599a640da1b0f58b9c587042fad000c56913491892df78b` | out-of-scope candidate |
| `software/python/python-cheatsheets/Pandas_cheatsheet.pdf` | `590d02ed248727c0e56f6e5a72419aae88d405a68afd9a7e3652f42fd131755b` | out-of-scope candidate |
| `software/python/python-cheatsheets/Scikit-Learn_cheatsheet.pdf` | `a05394df2819fc17bfe9c13b884ed27f61d873adbf51bb610b508e670b270aff` | out-of-scope candidate |
| `software/python/python-depth-drills/README.md` | `bbcae45b4d8740cb8f2ea72143bdc3b8ee67da197a1b728d4cdedc81da412797` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/SHELF.md` | `9ec0dae0ec7283389afbd6ef1fce9c97d6a2b7bed6871c1fca053425dd1dced5` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/_build/README.md` | `a69eded6692e0c897a758ac249d1d5e8c59e3851231a0acbaada07615e1b26b6` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/_build/dump.py` | `e0e1af2136e080e372a31d80bf1bbe34d31ca2959420390068b37bd3a1064526` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/_build/verify.py` | `fdc6743c51ee0a50007dc6e5ff5f30f44dfdbecafc1f641599f192a18f7df751` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/capstone.ipynb` | `2a7a920b30a1ccf82603726405b8ce0cea9aa8a97b16d1b412503f5b0baad0ac` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-0-names-and-identity.ipynb` | `c788ffc079a116840e71d4e3be5c9c159a4d58ca188dd710dcfe6b10075f30f4` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-0-names-and-identity.md` | `596fe57e1f64455e25b408010dd4ae0e9524e04c3ab7fd6c0f99d92345a9bbbc` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-1-functions-as-objects.ipynb` | `77b9b6b2bdf9f118c0eb20d3e9c395864417654bd427a80d288b52d56c067283` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-1-functions-as-objects.md` | `b7d0945982846ac8591a5160693cbb8045d78e4f9605209a533789e522c669d2` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-2-scope-and-closures.ipynb` | `aabb0d1853b82b5dd1259af1188457ab8cd78f04fe446cfa2a7fb1e9abbe2f4a` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-2-scope-and-closures.md` | `9ce892179e82db73ee17224c8ade3c1dbfffb82695e882ac8099f15edb595446` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-3-decorators.ipynb` | `858c013bd3e6804d3ed05598553fb33636dcb777b6545d0645092e587d5da37e` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-3-decorators.md` | `babab12b86b04c3a3a04c0946aa957653846a1c57e6d25ac25f6cfd09ae5688d` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-4-classes-as-objects.ipynb` | `1b9b9cd6c1fcef5e94b577d9114a246851e3339f9160bf8df1d384b2dce61be5` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-4-classes-as-objects.md` | `acce151d64525018ff43f96e7e89c83e69bfc1c626bd2e118315a3f085a2a398` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-5-imports-and-registration.ipynb` | `6223dd84f71a36de06a9c74b8030b1afddff0a57fb94e10bf8f67f991d3517b6` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-5-imports-and-registration.md` | `7550c4a7d236729a5f7ebffe2ec08230828558cbccae9e4eebd58e31209853ef` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-6-data-model-and-dunders.ipynb` | `b25e8cbeb729b26087c148d2dd510e24a6cc5e315bd4d5a068d16e2e8c77b898` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-6-data-model-and-dunders.md` | `92f40bb7744db6f3a8b0da8c22dd34c55174e109fc9780bca9a1878c58bd0eda` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-7-generators-and-iterators.ipynb` | `97e09e78c5ec6ae0e32ec3d55e39687e3819c7899abb0885842a393c1226b7ec` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-7-generators-and-iterators.md` | `ca5b8b57cd5a0369adb0d4e635fac9ba354d66345439fc992401e5b769be92a6` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-8-interfaces-and-dispatch.ipynb` | `87c330a6ed48dba0d0f0fc83915d1bd67e8af6948ef00a832f6eb8bb92418c36` | deferred; metadata only, no exercise/key review |
| `software/python/python-depth-drills/stage-8-interfaces-and-dispatch.md` | `57bab30e98bb50866117d4f5d6c7ee4853f1bf8d0ad56dbc35805b205bf4be9c` | deferred; metadata only, no exercise/key review |
| `software/python/slatkin-effective-python/effective-python-3e-toc-sample.pdf` | `ca46b3ec455b0d28bfa292a20d8e60783701138f94c84c736ebe20d1b186cacc` | optional 2e full text; 3e sample reference-only |
| `software/python/slatkin-effective-python/effective-python.pdf` | `c6049c8b5985ef7449740fb4bc30f7a157dff1baef8feca2b7ad414734467de6` | optional 2e full text; 3e sample reference-only |
