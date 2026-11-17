# M1 worktree setup (PowerShell)

Run from the Git repository root after the initial commit. Worktrees are **sibling directories**, not folders inside the main checkout. The two branches start at the same commit.

```powershell
git status --short
git rev-parse HEAD
git worktree add -b codex/flip-m1-core ../flip-codex HEAD
git worktree add -b opencode/flip-m1-fixtures ../flip-opencode HEAD
git worktree list
```

Open Codex in `../flip-codex`; OpenCode in `../flip-opencode`. Give each the corresponding prompt under `agent-tasks/`. The primary `flip` checkout stays on `main` and receives reviewed commits only.

After both finish: Codex reviews the OpenCode fixture commit, verifies source hashes, and cherry-picks or merges into the integration branch; run required full M1 tests before updating `main`. **Never let the agents work concurrently in the same checkout.**

If `git init -b main` is unsupported in installed Git: `git init`, then `git branch -M main` after first commit.
