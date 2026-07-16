---
id: note-git-github-reference
type: note
title: "Git & GitHub — Reference by Working Space"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-git]
sources: []
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Programming/Git/Git-GitHub-Reference-by-Block.md` (legacy tree).

# Git & GitHub — Reference by Working Space

A map of Git commands grouped by **which of the four areas they act on**, with a one-line purpose and good sources under each.

> **The four areas (your blocks):**
> **A** My Working Space → **B** Staging Area → **C** My Commit Graph (local repo) → **D** The Shared Commit Graph (GitHub).
> Almost every command either **moves** a snapshot between two of these, or **compares / inspects** them.

> **About the sources:** `Pro Git §x.y` refers to *Pro Git* (Chacon & Straub) — it's the `GIT.pdf` in this folder, and each link opens the same section online. `man` links are the official command reference. Friendly tutorials (Atlassian, Learn Git Branching, etc.) are added where they help most.

---

## Start here — the mental model

Read these *before* memorizing commands. They explain Git's data model (commits = snapshots in a DAG; branches/HEAD/tags = movable pointers), which makes every command below make sense instead of needing to be memorized.

- **MIT Missing Semester — Version Control (Git):** bottom-up, data-model-first. The single best 1-hour read. <https://missing.csail.mit.edu/2020/version-control/>
- **Learn Git Branching:** interactive, visual game for branches/merge/rebase. Do this in a browser. <https://learngitbranching.js.org/>
- **Pro Git §3.1 — Branches in a Nutshell:** what a branch and HEAD actually are. <https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell>
- **Git for Computer Scientists:** the object model with diagrams. <https://eagain.net/articles/git-for-computer-scientists/>

---

## Setup (before the four blocks)

### `git config` — set your identity and preferences
`git config --global user.name "..."` / `user.email "..."` — stamped on every commit.

- Pro Git §1.6 First-Time Git Setup — <https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup>
- Pro Git §8.1 Git Configuration (every option) — <https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration>
- GitHub Docs — Set up Git — <https://docs.github.com/en/get-started/git-basics/set-up-git>

### `git init` — turn the current folder into a new repo
Creates the hidden `.git` directory (your whole repo). You'll rarely use this when contributing — you'll `clone` instead.

- Pro Git §2.1 Getting a Git Repository — <https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository>
- man: git-init — <https://git-scm.com/docs/git-init>

### `git clone <url>` — copy a remote repo (with full history) to your machine
Downloads everything, sets the source as remote `origin`, checks out the files. **For forking: clone _your fork_, then add the original as `upstream`.**

- Pro Git §2.1 Getting a Git Repository — <https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository>
- man: git-clone — <https://git-scm.com/docs/git-clone>

---

## Block A — My Working Space
*The files you edit. Changes here are "modified" or "untracked" until you stage them.*

### `git status` — what changed and where
Your dashboard: modified, staged, untracked files + branch/ahead-behind info. Run it constantly.

- Pro Git §2.2 Recording Changes — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- man: git-status — <https://git-scm.com/docs/git-status>

### `git diff` — see unstaged changes (Working Space vs Staging)
Add `HEAD` to compare against the last commit instead. (The other diffs live in Block B and Block C.)

- Pro Git §2.2 Recording Changes (Viewing Your Staged and Unstaged Changes) — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- Atlassian — git diff — <https://www.atlassian.com/git/tutorials/saving-changes/git-diff>

### `git restore <file>` — discard edits in the working file ⚠
Replaces the file with the staged/committed version. **Destroys uncommitted edits — no undo.** (Old Git: `git checkout -- <file>`.)

- Pro Git §2.4 Undoing Things — <https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things>
- man: git-restore — <https://git-scm.com/docs/git-restore>
- Rescue recipe — <https://dangitgit.com/#undo-a-file>

### `git rm` / `git mv` — delete or rename a tracked file (and stage it)
`git rm --cached <file>` stops tracking a file but keeps it on disk (the fix after committing something that should be in `.gitignore`).

- Pro Git §2.2 Recording Changes (Removing / Moving Files) — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- man: git-rm — <https://git-scm.com/docs/git-rm>

### `git clean` — delete untracked files from the working space
`git clean -n` (dry run — always do this first), then `git clean -fd`. ⚠ Removes files Git never tracked; no undo.

- Pro Git §7.3 Stashing and Cleaning — <https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning>
- man: git-clean — <https://git-scm.com/docs/git-clean>

### `.gitignore` — tell Git which files to never track
Patterns like `*.log`, `build/`, `.env`. Generate one for your stack at gitignore.io.

- Pro Git §2.2 Recording Changes (Ignoring Files) — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- GitHub Docs — Ignoring files — <https://docs.github.com/en/get-started/git-basics/ignoring-files>
- Generator + templates — <https://www.toptal.com/developers/gitignore> · <https://github.com/github/gitignore>

### `git stash` — shelve working + staged changes, get a clean slate
`git stash` then `git stash pop` later. Perfect when you need to switch branches or pull but aren't ready to commit.

- Pro Git §7.3 Stashing and Cleaning — <https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning>
- Atlassian — git stash — <https://www.atlassian.com/git/tutorials/saving-changes/git-stash>

---

## Block B — Staging Area (the index)
*A hand-picked draft of your next commit. Choosing what goes here is Git's key feature.*

### `git add <file>` — stage changes (Working Space → Staging)
`git add .` stages everything; `git add -A` includes deletions. Re-add after each edit to capture the newer version.

- Pro Git §2.2 Recording Changes — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- Atlassian — git add — <https://www.atlassian.com/git/tutorials/saving-changes>

### `git add -p` — interactively stage selected chunks
Walk through each change and pick y/n. Turns messy work into small, reviewable commits — a real contributor skill.

- Pro Git §7.2 Interactive Staging — <https://git-scm.com/book/en/v2/Git-Tools-Interactive-Staging>
- man: git-add — <https://git-scm.com/docs/git-add>

### `git restore --staged <file>` — unstage (Staging → Working Space)
Undoes a `git add` while keeping your working edits. (Old Git: `git reset <file>`.)

- Pro Git §2.4 Undoing Things — <https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things>
- man: git-restore — <https://git-scm.com/docs/git-restore>

### `git diff --staged` — see what your next commit will contain (Staging vs last commit)
The diff people forget exists. (`--cached` is a synonym.)

- Pro Git §2.2 Recording Changes — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- "Where's my diff?" — <https://dangitgit.com/#dude-wheres-my-diff>

---

## Block C — My Commit Graph (local repo)
*The `.git` directory: your full history and branches, all offline. This is where most "graph manipulation" happens.*

### `git commit` — record the staged snapshot into history (Staging → graph)
`-m "msg"` for the message; `--amend` rewrites the **last** commit (only before pushing).

- Pro Git §2.2 Recording Changes — <https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository>
- Writing good commit messages — <https://cbea.ms/git-commit/>
- Amend recipe — <https://dangitgit.com/#change-last-commit>

### `git log` — view the commit history
`git log --oneline --graph --all --decorate` draws the branch graph (alias it as `git graph`).

- Pro Git §2.3 Viewing the Commit History — <https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History>
- man: git-log — <https://git-scm.com/docs/git-log>

### `git show <commit>` — inspect one commit (message + its diff)
Accepts a hash, `HEAD`, `HEAD~2`, a branch, or a tag.

- Pro Git §7.1 Revision Selection — <https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection>
- man: git-show — <https://git-scm.com/docs/git-show>

### `git blame <file>` — who last changed each line, and in which commit
Essential for understanding unfamiliar code; pair with `git show` on the revealed hash.

- man: git-blame — <https://git-scm.com/docs/git-blame>
- Pro Git §7.5 Searching (line history) — <https://git-scm.com/book/en/v2/Git-Tools-Searching>

### `git branch` — list / create / delete branches
A branch is just a movable pointer to a commit. `-d` deletes a merged branch; `--all` shows remote-tracking ones too.

- Pro Git §3.1 Branches in a Nutshell — <https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell>
- Pro Git §3.3 Branch Management — <https://git-scm.com/book/en/v2/Git-Branching-Branch-Management>
- Learn Git Branching (interactive) — <https://learngitbranching.js.org/>

### `git switch` — move HEAD to another branch
`git switch -c <name>` creates and switches (start every feature this way). Modern replacement for `git checkout <branch>`.

- Pro Git §3.1 Branches in a Nutshell — <https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell>
- man: git-switch — <https://git-scm.com/docs/git-switch>

### `git merge <branch>` — combine another branch into your current one
Fast-forwards if possible, else creates a merge commit (two parents). Conflicts → edit, `git add`, `git commit`.

- Pro Git §3.2 Basic Branching and Merging — <https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging>
- Atlassian — merging vs rebasing — <https://www.atlassian.com/git/tutorials/merging-vs-rebasing>
- Advanced/conflicts: Pro Git §7.8 Advanced Merging — <https://git-scm.com/book/en/v2/Git-Tools-Advanced-Merging>

### `git rebase <branch>` — replay your commits on top of another branch
Gives a linear history (no merge commit) but **rewrites commits (new hashes)** — never rebase commits you've already shared. `-i` lets you squash/reorder/edit before a PR.

- Pro Git §3.6 Rebasing — <https://git-scm.com/book/en/v2/Git-Branching-Rebasing>
- Atlassian — merging vs rebasing — <https://www.atlassian.com/git/tutorials/merging-vs-rebasing>
- GitHub Docs — About Git rebase — <https://docs.github.com/en/get-started/using-git/about-git-rebase>
- Rewriting history: Pro Git §7.6 — <https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History>

### `git cherry-pick <commit>` — copy one specific commit onto the current branch
Grab a single fix from another branch without merging everything.

- Pro Git §5.3 Maintaining a Project (Cherry-Picking) — <https://git-scm.com/book/en/v2/Distributed-Git-Maintaining-a-Project>
- man: git-cherry-pick — <https://git-scm.com/docs/git-cherry-pick>

### `git reset [--soft|--mixed|--hard] <commit>` — move the branch pointer back
`--soft` keeps changes staged · `--mixed` (default) keeps them unstaged · `--hard` discards them ⚠. **Rewrites history — don't use on pushed commits.**

- Pro Git §7.7 Reset Demystified (the clearest explanation anywhere) — <https://git-scm.com/book/en/v2/Git-Tools-Reset-Demystified>
- Pro Git §2.4 Undoing Things — <https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things>
- Atlassian — git reset — <https://www.atlassian.com/git/tutorials/undoing-changes/git-reset>

### `git revert <commit>` — undo a commit by adding a new, inverse commit
The **safe** undo for anything already pushed/shared — history is preserved, so teammates don't diverge.

- man: git-revert — <https://git-scm.com/docs/git-revert>
- Atlassian — git revert — <https://www.atlassian.com/git/tutorials/undoing-changes/git-revert>
- Recipe — <https://dangitgit.com/#undo-a-commit>

### `git tag` — pin a permanent label on a commit (usually a release)
`git tag -a v1.0 -m "..."`. Tags aren't pushed automatically: `git push origin v1.0`.

- Pro Git §2.6 Tagging — <https://git-scm.com/book/en/v2/Git-Basics-Tagging>
- man: git-tag — <https://git-scm.com/docs/git-tag>

### `git reflog` — log of everywhere HEAD has been (your safety net)
Recovers "lost" commits after a bad reset/rebase: find the hash, then `git reset --hard HEAD@{n}`.

- Pro Git §10.7 Maintenance and Data Recovery — <https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery>
- "Magic time machine" recipe — <https://dangitgit.com/#magic-time-machine>

### Navigating the graph: `HEAD`, `HEAD~n`, `HEAD^n`
`HEAD` = where you are. `HEAD~2` = two commits back (first parent). `HEAD^2` = the **second** parent (only at a merge). A **detached HEAD** = HEAD on a commit with no branch — escape with `git switch -c <name>` to keep work.

- Pro Git §7.1 Revision Selection — <https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection>
- man: gitrevisions — <https://git-scm.com/docs/gitrevisions>

---

## Block D — The Shared Commit Graph (GitHub)
*Remote repos. For fork-based work: `origin` = your fork (you push here), `upstream` = the original project (you open PRs against it).*

### `git remote` — manage the named URLs you sync with
`git remote -v` lists them; `git remote add upstream <url>` links the original project to your clone.

- Pro Git §2.5 Working with Remotes — <https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes>
- GitHub Docs — Managing remotes — <https://docs.github.com/en/get-started/git-basics/managing-remote-repositories>

### `git fetch [remote]` — download remote commits without merging (GitHub → graph)
Updates `origin/main`, `upstream/main` (read-only "remote-tracking" pointers). Look before you merge. `--prune` drops stale ones.

- Pro Git §3.5 Remote Branches — <https://git-scm.com/book/en/v2/Git-Branching-Remote-Branches>
- man: git-fetch — <https://git-scm.com/docs/git-fetch>

### `git pull` — fetch + merge into your current branch (GitHub → graph → working space)
Fast-forwards if you've made no local commits, else merges (or use `--rebase` to stay linear).

- Pro Git §2.5 Working with Remotes — <https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes>
- GitHub Docs — Getting changes from a remote — <https://docs.github.com/en/get-started/using-git/getting-changes-from-a-remote-repository>

### `git push` — upload your commits (graph → GitHub)
`git push -u origin <branch>` on first push (sets the tracking link); plain `git push` after. Push to **your fork**, never `upstream`. After a rebase use `--force-with-lease`.

- Pro Git §3.5 Remote Branches — <https://git-scm.com/book/en/v2/Git-Branching-Remote-Branches>
- GitHub Docs — Pushing commits to a remote — <https://docs.github.com/en/get-started/using-git/pushing-commits-to-a-remote-repository>
- "non-fast-forward" error explained — <https://docs.github.com/en/get-started/using-git/dealing-with-non-fast-forward-errors>

### Tracking branches & "upstream" (the confusing word)
**Two meanings:** (1) the `upstream` *remote* = the original project; (2) a branch's *upstream* = the remote branch it tracks (e.g. `main` → `origin/main`). `git branch -vv` shows tracking + ahead/behind; `@{u}` is shorthand for "my upstream."

- Pro Git §3.5 Remote Branches — <https://git-scm.com/book/en/v2/Git-Branching-Remote-Branches>
- GitHub Docs — About remote repositories — <https://docs.github.com/en/get-started/git-basics/about-remote-repositories>

### The fork → Pull Request workflow (your job's contribution loop)
Fork on GitHub → clone your fork → `git remote add upstream …` → branch → commit → `git push -u origin <branch>` → open a **Pull Request** (GitHub's name for a Merge Request) → address review → maintainer merges → sync your fork (`git fetch upstream` → `git merge upstream/main` → `git push origin main`).

- **GitHub Docs — Contributing to a project (full fork+PR walkthrough)** — <https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project>
- GitHub Docs — Fork a repo — <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo>
- GitHub Docs — Syncing a fork — <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork>
- Atlassian — Forking Workflow — <https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow>
- Pro Git §6.2 GitHub — Contributing to a Project — <https://git-scm.com/book/en/v2/GitHub-Contributing-to-a-Project>
- Pro Git §5.2 Distributed Git — Contributing to a Project — <https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project>
- **Practice repo (real first PR):** first-contributions — <https://github.com/firstcontributions/first-contributions>

---

## Conflicts (happen during merge / rebase / pull)
When two branches change the same lines: edit the file between the `<<<<<<<` / `=======` / `>>>>>>>` markers, delete the markers, then `git add` + `git commit` (merge) or `git rebase --continue`. `git merge --abort` / `git rebase --abort` backs out.

- Pro Git §3.2 Basic Branching and Merging (Basic Merge Conflicts) — <https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging>
- GitHub Docs — Resolving conflicts after a rebase — <https://docs.github.com/en/get-started/using-git/resolving-merge-conflicts-after-a-git-rebase>

---

## Best general places to learn (bookmark these)

| Resource | Best for | Link |
|---|---|---|
| **Pro Git book** (= your `GIT.pdf`) | The definitive reference; chapters 1–5 cover ~everything you need | <https://git-scm.com/book/en/v2> |
| **Official Git docs** | Authoritative per-command reference | <https://git-scm.com/docs> |
| **Git cheat sheet** | One-page printable | <https://git-scm.com/cheat-sheet> |
| **MIT Missing Semester** | Understanding the data model (do first) | <https://missing.csail.mit.edu/2020/version-control/> |
| **Learn Git Branching** | Interactive practice for branches/merge/rebase | <https://learngitbranching.js.org/> |
| **Atlassian Git tutorials** | Clear explanations with diagrams | <https://www.atlassian.com/git/tutorials> |
| **GitHub Docs — Get started** | GitHub-specific: forks, PRs, auth | <https://docs.github.com/en/get-started> |
| **Oh Shit, Git!?! / Dangit, Git** | Recovering from mistakes, in plain English | <https://ohshitgit.com/> · <https://dangitgit.com/> |
| **first-contributions** | A safe repo to make your first real PR | <https://github.com/firstcontributions/first-contributions> |

---

*Note: your HU intro PDF teaches GitLab — the Git commands above are identical on GitHub; only platform terms differ (GitLab "Merge Request" = GitHub "Pull Request").*
