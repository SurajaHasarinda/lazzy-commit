# Git Workflow & Standards

This document defines how we use Git for **Lazzy Commit**. It exists so every
contributor branches, commits, reviews, and merges the same way — keeping history
readable and releases predictable. (Fittingly, this project *generates* commit
messages that already follow these rules.)

---

## 1. Repository structure

```
enhanced/
├── main.py              # Entry point (commit workflow + `config` subcommand)
├── bootstrap.py         # Composition root — builds services from config
├── config/              # Configuration: defaults, JSON store, legacy .env shim
├── core/                # External-system adapters (git CLI, Gemini API)
├── validators/          # Commit/diff validation rules
├── services/            # Business logic (commit, validation chain, history)
├── cli/                 # Interactive terminal UI
├── ui/                  # Local settings web app (FastAPI server + static front-end)
├── docs/                # Project documentation (this file, etc.)
└── requirements.txt
```

Keep new code in the layer that matches its responsibility. A new external
integration is a `core/` adapter; a new rule is a `validators/` class; new
orchestration is a `services/` method.

---

## 2. Branch naming conventions

Branch off `main`. Use a `type/short-description` slug in kebab-case:

| Prefix      | Use for                                   | Example                          |
|-------------|-------------------------------------------|----------------------------------|
| `feature/`  | New functionality                         | `feature/custom-secret-patterns` |
| `bugfix/`   | Fixing a non-urgent bug                   | `bugfix/range-slider-reset`      |
| `hotfix/`   | Urgent production fix (branch off a tag)  | `hotfix/api-key-leak`            |
| `refactor/` | Internal change, no behavior change       | `refactor/config-manager`        |
| `docs/`     | Documentation only                        | `docs/git-workflow`              |
| `chore/`    | Tooling, deps, CI                         | `chore/bump-fastapi`             |
| `release/`  | Release preparation                       | `release/2.1.0`                  |

Reference an issue when one exists: `feature/142-prompt-editor`.

---

## 3. Commit message format

We follow **[Conventional Commits](https://www.conventionalcommits.org/)** —
the same format this tool enforces.

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`,
`perf`, `chore`, `revert`.

**Rules**
- Subject in the **imperative mood**, lowercase, **no trailing period**, **≤ 72 chars**.
- Use a scope to localize the change: `feat(ui): add dark theme toggle`.
- Append `!` (or a `BREAKING CHANGE:` footer) for breaking changes:
  `feat(config)!: move settings to ~/.lazzycommit`.
- Explain **why** in the body when the change isn't self-evident; wrap at ~72 cols.

**Examples**
```
feat(validators): add user-defined secret patterns
fix(history): skip malformed jsonl lines instead of aborting
docs: document the config precedence chain
refactor(config): extract dotted-path helpers
```

---

## 4. Pull requests

1. Keep PRs **small and focused** — one logical change. Split unrelated work.
2. **Title** uses the Conventional Commits format (it often becomes the squash
   commit subject).
3. **Description** must cover:
   - *What* changed and *why* (link the issue: `Closes #142`).
   - How it was tested (commands run, screenshots for UI changes).
   - Any breaking changes or follow-ups.
4. Ensure the branch is **up to date with `main`** and the app still runs:
   `python main.py` and `python main.py config`.
5. At least **one approving review** is required before merge.

---

## 5. Code review checklist

Reviewers confirm:

- [ ] **Correctness** — does what the PR claims; edge cases handled.
- [ ] **Scope** — no unrelated changes sneaked in.
- [ ] **Security** — no secrets committed; user input (regex, config) is validated;
      the API key is never logged or sent to the browser.
- [ ] **Layering** — code sits in the right layer; `core/` stays free of business logic.
- [ ] **Readability** — names are self-documenting; comments explain *why*, not *what*.
- [ ] **Backward compatibility** — existing `.env` configs and CLI flags still work.
- [ ] **Docs** — README / this file updated if behavior or setup changed.
- [ ] **No dead code** — debug prints, commented-out blocks removed.

---

## 6. Merge vs. rebase

- **Updating your branch:** prefer **rebase** onto `main` to keep a linear history
  (`git fetch origin && git rebase origin/main`). Resolve conflicts locally.
- **Landing a PR:** use **squash and merge** so each PR becomes one tidy,
  conventional commit on `main`.
- **Never rebase or force-push a shared branch** others may have based work on.
  Rebase is for your own in-progress feature branch only.
- `main` is protected: no direct pushes, no force-pushes.

---

## 7. Handling sensitive data & secrets

This is a security tool — we hold ourselves to the standard it enforces.

- **Never commit** API keys, tokens, `.env`, or `config.json`. They are in
  `.gitignore`; keep them there.
- The Gemini key lives in `.env` (gitignored) or in `~/.lazzycommit/config.json`
  (outside any repo). It is **never** written into the project tree.
- If a secret is ever committed: **rotate it immediately**, then scrub history
  (`git filter-repo` / BFG) and force-update with team coordination. Rotation
  comes first — assume anything pushed is already compromised.
- Use placeholders in examples and tests (`your_api_key_here`), never real values.
- Let the tool guard you: run `lazzycommit` (its diff scanner blocks the common
  credential formats before they're committed).

---

## 8. Releases

1. Branch `release/x.y.z` off `main`.
2. Bump the version, update the changelog, final QA of both `commit` and `config`.
3. Merge to `main`, then tag: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push --tags`.
4. `hotfix/` branches for urgent fixes branch off the affected tag and merge back
   to both `main` and any active release branch.

We follow **[Semantic Versioning](https://semver.org/)**: `MAJOR` for breaking
changes, `MINOR` for backward-compatible features, `PATCH` for fixes.
