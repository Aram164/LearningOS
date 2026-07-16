# Programming Toolbox Bootcamp — KW 17–18

> **Goal:** In ~10 days, build your entire programming foundation: Python fluency, shell, Git, VS Code, pytest, Docker. Go from "I know some basics" to "I can work on real projects without friction."
>
> **Why this matters:** Every other chat (PPDS, AMLS Project, Job) assumes you can do these things. Investing this time now prevents hours of friction later.
>
> **Pre-onboarding deadline:** May 5 (Job starts). By then you need Python + shell + git fluency.

**Two tracks running in parallel:**

| Track | What | Time/day |
|-------|------|----------|
| **Tools** (Days 1–7) | Shell, Git, venv, VS Code, pytest, Docker | ~1–2 hours mornings |
| **Python** (Days 1–10) | ATBS fast-track → Fluent Python deep dive | ~2–3 hours afternoons/evenings |

**Books used:**
- *Automate the Boring Stuff with Python* (ATBS) — gentle on-ramp, practical from day 1
- *Fluent Python, 2nd Ed.* (FP) — deep understanding, follows Praxisplan reading order

---

# Part A: Tools Track

## Day 1–2: Shell Power-Ups (Missing Semester L1)

**You already know:** `cd`, `ls`, basic navigation.
**You need to add:** pipes, redirection, grep, find, environment variables, and scripting basics.

### Core Concepts

**Pipes and redirection** — the shell's killer feature. Every command reads from stdin and writes to stdout. You can chain them:

```bash
# Count how many Python files are in a project
find . -name "*.py" | wc -l

# Search for "TODO" in all Python files
grep -rn "TODO" --include="*.py" .

# Save output to a file
python train.py 2>&1 | tee training_log.txt
```

**Key commands to drill:**

| Command | What it does | You'll use it for |
|---------|-------------|-------------------|
| `grep -rn "pattern" .` | Search file contents recursively with line numbers | Finding functions, debugging imports |
| `find . -name "*.py"` | Find files by name pattern | Navigating project structures |
| `cat / less / head / tail` | View file contents | Quick inspection without opening editor |
| `|` (pipe) | Send one command's output to another | Chaining operations |
| `>` / `>>` | Write / append to file | Saving outputs |
| `2>&1` | Redirect stderr to stdout | Capturing error messages |
| `which python3` | Find where a program lives | Debugging environment issues |
| `echo $PATH` | Show your PATH | Understanding why commands aren't found |
| `export VAR=value` | Set environment variable (current session) | Configuring tools |
| `chmod +x script.sh` | Make a file executable | Running scripts |

### Exercises (30–45 min)

1. Open Terminal on your Mac. Run `echo $SHELL` — you should see `/bin/zsh`.
2. Navigate to any folder with files. Run `ls -la` — understand what each column means (permissions, owner, size, date).
3. Create a test directory: `mkdir ~/toolbox-practice && cd ~/toolbox-practice`
4. Create files: `echo "hello world" > file1.txt && echo "hello python" > file2.txt`
5. Use grep: `grep "python" *.txt` — which file matches?
6. Use pipes: `ls -la /usr/bin | grep python | head -5` — what do you see?
7. Redirect: `echo "line 1" > log.txt && echo "line 2" >> log.txt && cat log.txt`
8. Find: `find /usr/local -name "python*" 2>/dev/null` — the `2>/dev/null` hides permission errors.

### Missing Semester Reference

Work through: https://missing.csail.mit.edu/2020/course-shell/ (Lecture 1: The Shell)

**What to skip for now:** Shell scripting (loops, conditionals in bash) — you'll write Python scripts instead. Just know that `.sh` files exist and `chmod +x` makes them runnable.

---

## Day 2–3: Git — The Non-Negotiable (Missing Semester L6)

**Why:** PPDS is a *team* project on GitHub. The AMLS project needs version control. Your job will involve PRs. Git is unavoidable.

### Mental Model

Git tracks *snapshots* of your project, not diffs. Think of it as a timeline of save points you can jump between.

Three areas to understand:

```
Working Directory  →  Staging Area  →  Repository (commits)
   (your files)      (git add)         (git commit)
```

### Setup (do this now)

```bash
# Configure your identity (used in every commit)
git config --global user.name "Aram Aljanadi"
git config --global user.email "aramaljanadi2003@gmail.com"

# Better default for new branches
git config --global init.defaultBranch main

# Colored output
git config --global color.ui auto

# Set VS Code as your default editor for git
git config --global core.editor "code --wait"
```

### The 10 Commands That Cover 95% of Git Usage

**Solo workflow (AMLS Project):**

```bash
# 1. Clone a repo
git clone https://github.com/your-repo.git
cd your-repo

# 2. Check what's changed
git status

# 3. See the actual changes
git diff

# 4. Stage specific files
git add clean.py prepare.py

# 5. Stage everything
git add .

# 6. Commit with a message
git commit -m "Implement data cleaning pipeline"

# 7. Push to GitHub
git push origin main

# 8. Pull latest changes
git pull origin main

# 9. See history
git log --oneline --graph

# 10. Undo last commit (keep changes)
git reset --soft HEAD~1
```

**Team workflow (PPDS — you'll need this):**

```bash
# Create a branch for your feature
git checkout -b feature/read-csv

# Work, commit, push
git add .
git commit -m "Implement read_csv with provenance tracking"
git push origin feature/read-csv

# When done: create a Pull Request on GitHub (web UI)
# After PR is merged, switch back and update
git checkout main
git pull origin main

# Delete old branch
git branch -d feature/read-csv
```

### The Situations That Trip Up Beginners

**"I committed to the wrong branch"**
```bash
# Undo the commit but keep changes
git reset --soft HEAD~1
# Switch to correct branch
git checkout -b correct-branch
# Recommit
git add . && git commit -m "your message"
```

**"I have merge conflicts"**
```
<<<<<<< HEAD
your version
=======
their version
>>>>>>> branch-name
```
→ Open the file, pick the right version, delete the markers, then `git add` and `git commit`.

**"I want to discard all local changes"**
```bash
git checkout -- .          # discard unstaged changes
git reset --hard HEAD      # discard everything since last commit (⚠️ destructive)
```

**".gitignore basics"** — create a `.gitignore` file in your project root:
```
__pycache__/
*.pyc
.venv/
.DS_Store
artifacts/
*.egg-info/
```

### Exercises (45–60 min)

1. Create a practice repo: `mkdir git-practice && cd git-practice && git init`
2. Create a file, add it, commit it. Run `git log` — see your commit.
3. Modify the file. Run `git diff` — see what changed. Then `git add . && git commit -m "update"`.
4. Create a branch: `git checkout -b experiment`. Make a change, commit it.
5. Switch back: `git checkout main`. Notice the file reverted. Switch back: `git checkout experiment`. It's back.
6. Merge: `git checkout main && git merge experiment`. Done.
7. Now clone the PPDS repo (if you have access): `git clone https://github.com/deem-teaching/2026-ppds-mlprov-students.git` — explore its structure with `ls`, `find`, and `grep`.

### Missing Semester Reference

Work through: https://missing.csail.mit.edu/2020/version-control/ (Lecture 6: Version Control)

---

## Day 3–4: Python Environment Management

**Why:** You'll have multiple projects (mlprov, AMLS, Stratum) with different dependencies. Virtual environments prevent them from conflicting.

### Check Your Python Installation

```bash
python3 --version     # Should be 3.10+ (ideally 3.11 or 3.12)
which python3         # Where is it?
pip3 --version        # Package manager
```

If you don't have Python 3.10+:
```bash
brew install python@3.12
```

### Virtual Environments — One Per Project

```bash
# Create a venv for your AMLS project
mkdir ~/projects/amls-project && cd ~/projects/amls-project
python3 -m venv .venv

# Activate it (your prompt changes to show (.venv))
source .venv/bin/activate

# Now pip installs go into THIS venv, not globally
pip install numpy pandas scikit-learn

# See what's installed
pip list

# Save dependencies (for Docker later, for teammates)
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

**Rule of thumb:** Never `pip install` without an active venv (except for global tools like `maturin`).

### Project Structure Convention

```
my-project/
├── .venv/              # Virtual environment (in .gitignore!)
├── .gitignore
├── requirements.txt    # or pyproject.toml
├── src/                # Your code
│   └── my_module/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
└── README.md
```

For PPDS (mlprov), the structure is already defined — you'll work within it. For AMLS, you'll create the `solution/` folder structure from the exercise spec.

### pip Essentials

```bash
pip install package_name          # Install
pip install package_name==1.2.3   # Specific version
pip install -r requirements.txt   # Install from file
pip install -e .                  # Install current project in editable mode (for development)
pip uninstall package_name        # Remove
pip show package_name             # Info about installed package
```

### Exercises (20–30 min)

1. Check your Python version and pip version.
2. Create a project folder, create a venv, activate it.
3. Install `numpy` and `pandas`. Run `python3 -c "import numpy; print(numpy.__version__)"`.
4. Run `pip freeze > requirements.txt`. Open the file — see the pinned versions.
5. Deactivate, create a *second* venv elsewhere. Notice it has nothing installed — clean isolation.

---

## Day 4–5: VS Code for Python Development

### Essential Extensions (install these)

1. **Python** (Microsoft) — syntax, linting, IntelliSense, debugging
2. **Pylance** (Microsoft) — fast type checking and autocomplete
3. **GitLens** — see who changed what, inline blame, branch visualization
4. **Python Indent** — fixes Python indentation annoyances
5. **Docker** (Microsoft) — for AMLS project later

Install from terminal: `code --install-extension ms-python.python ms-python.vscode-pylance eamodio.gitlens`

### Key Settings

Open Settings (Cmd+,) and set:

- **Python > Default Interpreter Path:** point to your `.venv/bin/python`
- **Editor > Format On Save:** on
- **Python > Formatting Provider:** (install `black` via pip, then set as formatter)

Or add to `.vscode/settings.json` in your project:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
    }
}
```

### Key Shortcuts (Mac)

| Shortcut | What it does |
|----------|-------------|
| Cmd+Shift+P | Command Palette (search any action) |
| Cmd+P | Quick file open |
| Cmd+Shift+F | Search across all files |
| Cmd+` | Toggle integrated terminal |
| F5 | Start debugging |
| F12 | Go to definition |
| Cmd+D | Select next occurrence (multi-cursor) |
| Cmd+/ | Toggle comment |
| Ctrl+Shift+` | New terminal |

### Debugging in VS Code (critical skill)

Instead of `print()` everywhere, use the debugger:

1. Open a Python file
2. Click left of a line number → red dot (breakpoint)
3. Press F5 → select "Python: Current File"
4. Execution stops at your breakpoint → inspect variables in the sidebar
5. Use the toolbar: Step Over (F10), Step Into (F11), Continue (F5)

### Integrated Git

VS Code has Git built in (left sidebar, branch icon):
- See changed files, stage them, write commit messages
- Click a file to see the diff
- Bottom-left: current branch name — click to switch branches
- GitLens adds: inline blame ("last changed by X, 3 days ago")

### Exercises (20 min)

1. Install the extensions listed above.
2. Open a Python project folder in VS Code (File → Open Folder).
3. Select the correct Python interpreter: Cmd+Shift+P → "Python: Select Interpreter" → pick your `.venv`.
4. Create a file `debug_test.py`:
   ```python
   def add(a, b):
       result = a + b
       return result

   x = add(3, 4)
   y = add(x, 10)
   print(f"Result: {y}")
   ```
5. Set a breakpoint on `result = a + b`. Press F5. Step through and watch the variables panel.

---

## Day 5–6: pytest — Running and Writing Tests

**Why:** PPDS has test files (`test_loaders.py`, `test_sklearn.py`, etc.) that your code must pass. The Job uses tests too. You need to run them confidently.

### Basics

```bash
pip install pytest

# Run all tests in current directory
pytest

# Run a specific file
pytest tests/test_loaders.py

# Run a specific test function
pytest tests/test_loaders.py::test_read_csv

# Verbose output (see each test name)
pytest -v

# Stop on first failure
pytest -x

# Show print output
pytest -s
```

### Writing a Test

```python
# tests/test_example.py

def test_addition():
    assert 1 + 1 == 2

def test_string():
    greeting = "hello"
    assert greeting.upper() == "HELLO"
    assert len(greeting) == 5

def test_list_operations():
    items = [1, 2, 3]
    items.append(4)
    assert len(items) == 4
    assert items[-1] == 4
```

**Naming convention:** Files must start with `test_`. Functions must start with `test_`. pytest auto-discovers them.

### Common Patterns You'll See in PPDS

```python
import pytest
import pandas as pd

class TestProvDataFrame:
    """Group related tests in a class."""

    def test_read_csv(self, tmp_path):
        # tmp_path is a pytest fixture — gives you a temp directory
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n3,4\n")

        df = read_csv(str(csv_file))
        assert len(df) == 2
        assert list(df.columns) == ["a", "b"]

    def test_projection(self):
        # Select specific columns
        df = create_test_dataframe()
        result = df[["col_a", "col_b"]]
        assert result.shape[1] == 2

    @pytest.mark.parametrize("n_rows", [10, 100, 1000])
    def test_performance_scales(self, n_rows):
        # Same test, different inputs
        df = create_dataframe(n_rows)
        assert len(df) == n_rows
```

### VS Code Integration

VS Code discovers pytest automatically. Open the Testing sidebar (flask icon on the left) to see all tests. Click the play button next to any test to run it. Green = pass, red = fail.

### Exercises (30 min)

1. In your practice project, create `tests/test_basics.py` with 3 simple tests.
2. Run `pytest -v` from terminal. See them pass.
3. Make one test fail on purpose. See the error output — understand how pytest shows you what went wrong.
4. Open VS Code Testing sidebar. Run tests from there.

---

## Day 6–7: Docker Fundamentals (for AMLS Project)

**Why:** Your AMLS submission must include a Dockerfile. The graders will build and run your code inside a container. You don't need to be a Docker expert — you need to understand the basics.

### Mental Model

Docker = a lightweight virtual machine for your code. A **Dockerfile** is a recipe. A **Docker image** is the built result. A **container** is a running instance of an image.

```
Dockerfile  →  docker build  →  Image  →  docker run  →  Container
 (recipe)                      (artifact)                (running process)
```

### Install Docker

Download Docker Desktop for Mac: https://www.docker.com/products/docker-desktop/

After installation: `docker --version` should work.

### The AMLS Dockerfile Pattern

From the exercise spec (Appendix A), your Dockerfile will look something like:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (caches this layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Default command (graders will override this)
CMD ["python", "clean.py"]
```

### Essential Commands

```bash
# Build an image from a Dockerfile
docker build -t amls-project .

# Run a container
docker run amls-project python clean.py

# Run interactively (get a shell inside)
docker run -it amls-project /bin/bash

# Mount a data directory (read-only, like the graders will)
docker run -v $(pwd)/data:/app/data:ro amls-project python train.py

# List running containers
docker ps

# List images
docker images

# Remove an image
docker rmi amls-project
```

### Key Gotchas for AMLS

- **No internet at runtime.** All `pip install` must happen in `docker build`, not when the container runs.
- **CPU only.** Use `torch` without CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- **Image size < 4 GB.** Use `python:3.12-slim` (not `python:3.12`), clean up caches.
- **Read-only data.** Your code reads from `data/` but writes only to `artifacts/`.

### Exercises (30 min)

1. Install Docker Desktop if you haven't.
2. Run `docker run hello-world` — this pulls and runs a test image.
3. Create a folder with a simple Python script and a Dockerfile. Build and run it.
4. Try the interactive mode: `docker run -it python:3.12-slim /bin/bash` — you're inside a container. Run `python3`, import something, exit.

---

## Quick Reference Card

### Shell
```bash
grep -rn "pattern" .          # Search in files
find . -name "*.py"           # Find files
cmd1 | cmd2                   # Pipe
cmd > file                    # Write to file
cmd >> file                   # Append to file
```

### Git
```bash
git status / diff / log --oneline
git add . && git commit -m "msg"
git push / pull origin main
git checkout -b branch-name
git merge branch-name
```

### Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt
deactivate
```

### pytest
```bash
pytest -v                      # All tests, verbose
pytest -x                      # Stop on first failure
pytest tests/test_file.py      # Specific file
pytest -k "test_name"          # By name pattern
```

### Docker
```bash
docker build -t name .
docker run name python script.py
docker run -it name /bin/bash
```

---

# Part B: Python Track

The strategy: use **Automate the Boring Stuff** (ATBS) for 2–3 days to get *doing* things in Python fast, then switch to **Fluent Python** (FP) for the deep understanding your courses and job require. You already know variables, loops, and if/else — ATBS will consolidate and extend that; FP will transform it into real Python thinking.

---

## Days 1–3: ATBS Fast-Track (Consolidate + Extend)

You know the very basics. The goal here isn't to learn what `if` does — it's to get your hands moving fast and fill gaps. Skim what you know, slow down on what's new.

### Day 1: ATBS Ch 1–3 (Basics, Flow Control, Functions)

**Skim quickly:** Variables, operators, `if/elif/else`, `while`, `for` — you know this. Just note Python-specific things that differ from what you're used to.

**Slow down on:**
- **Functions:** `def`, parameters, return values, `None`, keyword arguments, local vs global scope. This is foundational for everything.
- **Exception handling:** `try/except` — you'll see this everywhere in real code.

**Exercise:** Write a function `fizzbuzz(n)` that prints numbers 1 to n, but "Fizz" for multiples of 3, "Buzz" for 5, "FizzBuzz" for both. Then refactor it to *return a list* instead of printing.

```python
def fizzbuzz(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result

# Test it
print(fizzbuzz(20))
```

### Day 2: ATBS Ch 4–5 (Lists + Dictionaries)

**These are critical.** Lists and dicts are Python's bread and butter — pandas DataFrames, sklearn parameters, everything uses them.

**Key things to practice:**
- List slicing: `my_list[1:5]`, `my_list[::2]`, `my_list[::-1]`
- List methods: `append`, `insert`, `remove`, `sort`, `index`
- List comprehensions (ATBS mentions them briefly — practice them a lot):
  ```python
  squares = [x**2 for x in range(10)]
  evens = [x for x in range(20) if x % 2 == 0]
  ```
- Dict operations: accessing, adding, `.keys()`, `.values()`, `.items()`, `.get(key, default)`
- Nested structures: list of dicts (this is how tabular data often looks before you use pandas)

**Exercise:** Build a simple grade tracker:
```python
students = [
    {"name": "Alice", "grades": [85, 92, 78]},
    {"name": "Bob", "grades": [90, 88, 95]},
    {"name": "Carol", "grades": [72, 68, 81]},
]

# 1. Compute average grade for each student
# 2. Find the student with the highest average
# 3. Create a new list of only students with average > 80
# 4. Do #3 with a list comprehension
```

### Day 3: ATBS Ch 6 + Ch 8 (Strings + File I/O)

**Strings:** `f-strings` (ATBS may use `.format()` — prefer f-strings, they're modern), string methods, string slicing.

**File I/O is essential.** You'll read CSVs, write outputs, handle paths.

```python
# Modern Python file reading
from pathlib import Path

# Read a file
content = Path("data.txt").read_text()

# Write a file
Path("output.txt").write_text("hello\n")

# Read line by line (memory-efficient for large files)
with open("data.csv") as f:
    for line in f:
        print(line.strip())
```

**Exercise:** Write a script that reads a CSV file line by line, splits each line by comma, and builds a list of dicts (one per row, using the header row as keys). This is essentially what `pandas.read_csv` does under the hood.

```python
def my_read_csv(filepath):
    with open(filepath) as f:
        lines = [line.strip().split(",") for line in f]
    headers = lines[0]
    return [dict(zip(headers, row)) for row in lines[1:]]

# Test with a small CSV you create
```

### ATBS Chapters to Skip

Skip Ch 7 (Regex) for now — useful but not urgent. Skip Part II entirely (automation tasks like web scraping, Excel, etc.) — not relevant to your semester.

---

## Days 4–6: Fluent Python — Core Mental Model (FP Ch 1, 6, 2, 3)

Now you switch from "getting things done" to "understanding how Python actually works." This is where Fluent Python shines — it explains *why* things work the way they do.

### Day 4: FP Chapter 1 — The Python Data Model

**This is the most important chapter.** It explains Python's "magic methods" (`__len__`, `__getitem__`, `__repr__`, etc.) — the protocol that makes objects work with `len()`, `[]`, `for` loops, `print()`.

**Why it matters for you:** In PPDS, you'll build `ProvDataFrame` which needs `__getitem__` (for `df["column"]` and `df[mask]`). In the Job, Stratum subclasses sklearn estimators using these protocols.

**Key concepts:**
- Every `len(x)` calls `x.__len__()`
- Every `x[i]` calls `x.__getitem__(i)`
- Every `repr(x)` calls `x.__repr__()`
- Every `for item in x` calls `x.__iter__()`
- If you implement these methods, your objects work with all of Python's built-in syntax

**Exercise:** Build a `Deck` class (Luciano's example from Ch 1) yourself, then extend it:
```python
class Deck:
    ranks = [str(n) for n in range(2, 11)] + list("JQKA")
    suits = "spades diamonds clubs hearts".split()

    def __init__(self):
        self._cards = [(rank, suit) for suit in self.suits for rank in self.ranks]

    def __len__(self):
        return len(self._cards)

    def __getitem__(self, position):
        return self._cards[position]

    def __repr__(self):
        return f"Deck({len(self)} cards)"
```

Now test: `len(d)`, `d[0]`, `d[-1]`, `d[12::13]` (all aces), `for card in d`, `("A", "spades") in d`. All of this works because of the data model methods.

**Then build your own:** Create a `StudentGrades` class that supports `len()` (number of students), `[]` indexing (get student by index), and iteration.

### Day 5: FP Chapter 6 — Object References, Mutability, Recycling

**The chapter that prevents the bugs that waste hours.** Explains how Python variables are *names* that refer to objects, not boxes that contain values.

**Key concepts:**
- `a = [1, 2, 3]; b = a` — now `a` and `b` refer to the *same list*
- `a is b` checks identity (same object); `a == b` checks equality (same value)
- Mutable default arguments are a classic trap: `def f(items=[])` shares one list across all calls
- Shallow vs deep copy: `copy.copy()` vs `copy.deepcopy()`

**Exercise — the aliasing trap:**
```python
# Predict the output BEFORE running:
a = [1, 2, [3, 4]]
b = a
b.append(5)
print(a)  # ???

c = list(a)  # shallow copy
c[2].append(99)
print(a)  # ???

import copy
d = copy.deepcopy(a)
d[2].append(100)
print(a)  # ???
```

**Why this matters:** pandas DataFrames have the same aliasing behavior. `df2 = df` doesn't copy — it creates an alias. You'll hit this in PPDS when propagating provenance through transformations.

### Day 6: FP Chapter 2 — An Array of Sequences + FP Chapter 3 — Dicts and Sets

**Chapter 2** deepens what you learned about lists from ATBS. Key new things: tuple unpacking, `*` operator for excess items, slice objects, `bisect`, `array.array` for typed arrays.

**Practice tuple unpacking:**
```python
# Swap without temp variable
a, b = b, a

# Grab first and rest
first, *rest = [1, 2, 3, 4, 5]
print(first)  # 1
print(rest)   # [2, 3, 4, 5]

# Nested unpacking
metro = ("Tokyo", 2023, (35.689, 139.692))
name, year, (lat, lon) = metro
```

**Chapter 3** deepens dicts. Key new things: dict comprehensions, `defaultdict`, `__missing__`, `ChainMap`. 

**Practice dict comprehensions:**
```python
# Invert a dict
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}

# Count word frequency
words = "the cat sat on the mat the cat".split()
freq = {}
for w in words:
    freq[w] = freq.get(w, 0) + 1
# Or with defaultdict:
from collections import defaultdict
freq = defaultdict(int)
for w in words:
    freq[w] += 1
```

---

## Days 7–10: Fluent Python — Functions and Iteration (FP Ch 7, 17)

### Days 7–8: FP Chapter 7 — Functions as First-Class Objects

**Functions are objects.** You can assign them to variables, pass them as arguments, return them from other functions. This is how decorators, callbacks, and higher-order functions work.

**Key concepts:**
- `sorted(data, key=some_function)` — passing a function as argument
- `lambda x: x.lower()` — anonymous functions (use sparingly)
- `map`, `filter` vs list comprehensions (prefer comprehensions)
- Closures — a function that remembers variables from its enclosing scope

**Exercise:**
```python
# 1. Write a function that returns a function
def make_multiplier(n):
    def multiplier(x):
        return x * n
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))   # 10
print(triple(5))   # 15

# 2. Use sorted with a key function
students = [("Alice", 85), ("Bob", 92), ("Carol", 78)]
by_grade = sorted(students, key=lambda s: s[1], reverse=True)
print(by_grade)

# 3. Write a simple timing decorator
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_add(a, b):
    time.sleep(0.5)
    return a + b

slow_add(3, 4)
```

**Why this matters:** sklearn's `FunctionTransformer` takes functions as arguments. Stratum uses decorators for patching. PPDS mlprov will need you to wrap/instrument function calls.

### Days 9–10: FP Chapter 17 — Iterators, Generators, and Classic Coroutines

**Generators** are functions that `yield` instead of `return`. They produce items one at a time, without loading everything into memory. Critical for processing large datasets.

**Key concepts:**
- `yield` pauses the function and produces a value
- Generator expressions: `(x**2 for x in range(1000000))` — no memory for a million items
- The iterator protocol: `__iter__` and `__next__`
- `itertools` module for combining iterators

**Exercise — from your Praxisplan milestone:**
```python
# Generator that reads a CSV line by line (memory-efficient)
def csv_rows(filepath):
    with open(filepath) as f:
        headers = next(f).strip().split(",")
        for line in f:
            values = line.strip().split(",")
            yield dict(zip(headers, values))

# Use it — only one row in memory at a time
for row in csv_rows("large_data.csv"):
    print(row)

# Generator expression
total = sum(float(row["price"]) for row in csv_rows("products.csv"))
```

**Build this:** A generator that produces Fibonacci numbers infinitely:
```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Take the first 20
from itertools import islice
print(list(islice(fibonacci(), 20)))
```

**Why this matters:** In PPDS, you'll need to stream data through provenance-tracking transformations without loading everything into memory. Generators are how.

---

## Phase 1 Milestones (Ende KW 18)

These come directly from your Praxisplan. By the end of this bootcamp, you should be able to:

- [ ] Write a Python class that inherits from another and overrides methods
- [ ] Write a generator that uses `yield` (not just `return`)
- [ ] Create a dataclass with `__post_init__` and default values
- [ ] Explain the difference between `is` and `==` without hesitation
- [ ] Clone a repo, create a branch, commit, push, and create a PR
- [ ] Set up a Python project with venv, install dependencies, run tests
- [ ] Use the VS Code debugger instead of print statements
- [ ] Build and run a simple Docker container

**If any of these feel shaky → don't rush to Phase 2.** A solid foundation here pays for itself 10x over the semester.

---

## What Comes After This Bootcamp

The Praxisplan Phase 2 (KW 19–22) picks up where this ends:

| KW | Python (FP) | Project/Course |
|----|-------------|----------------|
| 19 | sklearn API + skrub basics | Job starts, AML exercises, PPDS repo setup |
| 20 | FP Ch 14 (Inheritance), Ch 9 (Decorators) | PPDS: `read_csv` implementation |
| 21 | Import system, monkey-patching | PPDS: `__getitem__`, AMLS project starts |
| 22 | NumPy deep dive | PPDS: merge/join, AMLS Task 1.1 |

Those topics will be covered in their respective chats (Chat 1 for AML, Chat 3 for AMLS Project, Chat 4 for PPDS+Job). This bootcamp chat's job is to get you ready for all of them.

---

## Daily Schedule Template (KW 17–18)

| Time | Activity |
|------|----------|
| **Morning (1–2h)** | Tools track: shell, git, VS Code, etc. |
| **After lunch (1–1.5h)** | Lectures: AMLS L02 (Apr 23), AML L01 (KW 18), DBT |
| **Afternoon (2–3h)** | Python track: ATBS → Fluent Python reading + exercises |
| **Evening (30–60 min)** | REPL experiments, review what you learned today |

**Friday:** Weekly review — check milestones, update SEMESTER-STATUS.md, decide if you need more time.

---

## What This Enables

After this bootcamp, you're unblocked for:

| Chat | What you can now do |
|------|-------------------|
| **Chat 1 (Foundations)** | Write Python exercises, understand sklearn examples in AML |
| **Chat 2 (AMLS Theory)** | Nothing directly — that's pure theory |
| **Chat 3 (AMLS Project)** | Set up project with venv, write Python scripts, debug in VS Code, build Docker |
| **Chat 4 (PPDS + Job)** | Clone mlprov repo, create branches, run pytest, submit PRs. Understand Python well enough to implement `ProvDataFrame`, `__getitem__`, generators for streaming |
