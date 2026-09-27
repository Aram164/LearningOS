# Native Obsidian pass

Build a fresh synthetic world, then from the real Core checkout run:

```bash
.venv/bin/python tests/eval/tools/prepare_native.py \
  --world /private/tmp/los-eval-world-U \
  --ui-rev UI_FULL_SHA
```

The tool locally clones that UI commit beside the synthetic Core, links the
existing Python virtual environment for the UI gateway, generates views, runs
the UI installer and `install:status`, and prints the product Core
revision, synthetic Core HEAD and UI revision separately. It can reuse the
source checkout's `node_modules` through a local ignored link. If dependencies
are missing, it leaves a clean UI clone; run `npm ci` there and then
`python3 install.py --vault /private/tmp/los-eval-world-U/LearningOS/repository`.
It refuses a
nonempty UI destination and any world inside the real workspace.

Open only `/private/tmp/los-eval-world-U/LearningOS/repository` as a vault in
Obsidian. Check its title/path before the first click. Enable the installed
plugin if Obsidian asks, reload, and open Diagnostics. Record the visible
identity and source fingerprint, then run S23–S25 through the actual controls.
Capture screenshots and JavaScript errors. CLI preparation is allowed; CLI
application does not count for the UI-admitted map import.

After opening Diagnostics in the target vault and **before S23 writes**, run
the installed UI clone's read-only live check with the **synthetic** Core HEAD
printed by the tool:

```bash
cd /private/tmp/los-eval-world-U/LearningOS/obsidian-ui
npm run check:live -- --vault /private/tmp/los-eval-world-U/LearningOS/repository \
  --core-sha SYNTHETIC_CORE_HEAD --ui-sha UI_FULL_SHA \
  --evidence-dir /private/tmp/los-eval-runs/RUN_ID/live
```

The synthetic HEAD is the history commit of Noor's data; `EVAL-WORLD.json`
binds its product code to the candidate Core revision. Report both. A passed
installer or `install:status` is installed-file evidence; only the running
Diagnostics and `check:live` support a live-app claim. If Obsidian or its CLI
is unavailable, mark the native cases NOT_RUN with the exact missing tool.
After a scenario writes canonical state, the synthetic Core is intentionally
dirty, and `check:live`'s clean-pair gate can no longer pass on that same
world. Keep the baseline live report plus post-write screenshots, Diagnostics,
Core receipts and fresh reads. Run S27 on another untouched frozen world.
