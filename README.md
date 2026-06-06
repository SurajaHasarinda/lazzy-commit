# Lazzy Commit 😪💤 — Enhanced

AI-powered git commit message generator with **built-in security validation**,
**conventional-commit enforcement**, and a **beautiful local settings UI**.

This is the enhanced edition of Lazzy Commit. It keeps everything the original
did — Gemini-generated messages, secret scanning, an interactive review prompt —
and adds a configurable settings dashboard, customizable AI prompt, custom
validation rules, and a local commit-history analytics view.

---

## ✨ What's new in the enhanced edition

| Feature | Description |
|--------|-------------|
| 🎛️ **Settings UI** | A clean, responsive web dashboard (`lazzycommit config`) for every setting — no more hand-editing `.env`. Light/dark/auto themes. |
| ✨ **Customizable AI prompt** | Edit the exact instructions sent to the model from the UI, with placeholder helpers and one-click reset. |
| 🧩 **Custom validation rules** | Add your own forbidden words, allowed commit types, and **regex secret patterns** — all from the UI. |
| 📊 **History & stats** | Local, private log of generated commits with acceptance rate, type distribution, and recent activity. |
| 🔑 **Live key testing** | Verify your Gemini key works with one click before saving. |
| ♻️ **Backward compatible** | Existing `.env` files and CLI flags (`-p`, `-f`) work unchanged. |

### Carried over from the original
🤖 AI-generated messages · 🔒 secret & sensitive-data scanning · 📝 conventional
commits · ✏️ interactive edit/override · 🚀 optional auto-push.

---

## 📋 Requirements

- Python 3.10+
- Git
- A Google Gemini API key — [get one here](https://aistudio.google.com/app/apikey)

---

## 🚀 Quick start

```powershell
# 1. From the enhanced/ folder, install dependencies
pip install -r requirements.txt

# 2. Open the settings UI and add your API key (recommended)
python main.py config

# 3. Stage changes in any repo and generate a commit
python main.py
```

### Install as a global `lazzycommit` command (Windows)

```powershell
# Run the setup script (creates a venv + .env, installs deps)
.\setup-path.bat

# Add this folder to your PATH so `lazzycommit` works from any repo
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";D:\path\to\enhanced", "User")
# Restart your terminal afterwards.
```

Then from any git repository:

```powershell
lazzycommit            # generate a commit message
lazzycommit -p         # generate, commit, and push
lazzycommit config     # open the settings UI
```

---

## 🎛️ The settings UI

Run `lazzycommit config` (or `python main.py config`) and your browser opens to a
local dashboard at `http://127.0.0.1:8420`. It binds to loopback only — nothing
is exposed to your network.

**Tabs**

- **AI & Model** — API key (with live test), model, and max diff size sent to the AI.
- **Security** — toggle credential/sensitive-data scanning; add custom regex patterns.
- **Format Rules** — conventional-commit toggle, subject/min length, allowed types,
  forbidden words, and whether overrides are permitted.
- **AI Prompt** — edit the generation prompt directly, insert the `{files_summary}`
  and `{diffs}` placeholders, or reset to the factory default.
- **History & Stats** — acceptance rate, commit-type distribution, recent activity.

Settings are saved to `~/.lazzycommit/config.json`. Your API key is stored there
only if you enter it in the UI; otherwise the legacy `.env` key is used.

> Prefer `--no-browser` (`python main.py config --no-browser`) to run the server
> headless, e.g. over SSH with a forwarded port.

---

## 📖 CLI usage

Stage your changes, then:

```bash
lazzycommit
```

The tool will:
1. 🔍 Analyze staged changes (and scan diffs for secrets)
2. 🤖 Generate a conventional-commit message
3. 📝 Show it for review
4. ✅ Let you confirm `(y)`, cancel `(n)`, or edit `(e)`

**Flags**

| Flag | Effect |
|------|--------|
| `-p`, `--push` | Push after a successful commit |
| `-f`, `--force` | Skip validation prompts, use the generated message as-is |

**Overrides** — when a security or format check blocks a commit, you'll be asked
whether to continue anyway (unless overrides are disabled in settings). `--force`
bypasses these prompts entirely.

---

## ⚙️ Configuration & precedence

Configuration resolves through three layers, each overriding the one before:

```
code defaults  <  legacy .env  <  config.json (settings UI)
```

- **Defaults** live in `config/defaults.py`.
- **`.env`** is still read for backward compatibility (ideal for the API key).
- **`config.json`** (`~/.lazzycommit/`) holds everything saved from the UI and wins.

Set `LAZZYCOMMIT_HOME` to relocate `config.json` and `history.jsonl` (handy for
portable installs or tests).

### Validation rules at a glance

- **Security:** blocks API keys/tokens (AWS, GitHub, Google, Stripe, …), private
  keys, JWTs, credit cards, SSNs, plus any **custom regex** patterns you add.
- **Format:** enforces `type(scope): description`, configurable subject length,
  and your configurable list of allowed types.
- **Content:** rejects placeholder commits (`wip`, `todo`, `fixme`, …) and
  too-short messages. Forbidden words are word-boundary matched, so `template`
  no longer trips the `temp` rule.

---

## 🏗️ Architecture

A layered design with clear responsibilities and dependency injection:

```
main.py ─ bootstrap.py ─┬─ config/      configuration (defaults, JSON store, env shim)
                        ├─ core/        adapters: git CLI, Gemini API
                        ├─ validators/  rules: security, format, content, custom
                        ├─ services/    commit orchestration, validation chain, history
                        ├─ cli/         interactive terminal workflow
                        └─ ui/         FastAPI settings server + responsive front-end
```

`bootstrap.py` is the single composition root: it reads the live config and wires
the validators and services that both the CLI and the web server use, so the two
never disagree about what a setting means.

---

## 🔧 Development

```bash
pip install -r requirements.txt
python main.py            # commit workflow
python main.py config     # settings UI
```

Contributions follow [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) — branch
naming, conventional commits, PR/review checklist, and secret-handling rules.

---

## 🤝 Contributing

Issues and PRs welcome. Please read [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md)
first and keep PRs small and focused.

## 📄 License

MIT — see [LICENSE](LICENSE).

---

**Made with ❤️ and a bit of laziness** 😪💤
