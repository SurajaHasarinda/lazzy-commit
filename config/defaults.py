# The prompt is kept as a module-level constant (not buried inside AIInterface)
# specifically so the settings UI can show it, let the user edit it, and offer a
# one-click "restore original" without reaching into application code.
#
# {files_summary} and {diffs} are the two placeholders the engine fills in. They
# are documented to the user in the UI; removing them would break generation, so
# the config manager validates their presence before saving a custom template.
DEFAULT_PROMPT_TEMPLATE = """\
Analyze the following git changes and generate ONE professional commit message \
following the Conventional Commits format.

Conventional Commits format: <type>: <description>

Types: feat, fix, docs, style, refactor, test, build, ci, modify
Description: imperative mood, lowercase, no period at end

IMPORTANT: Keep the first line under 72 characters.

Choose the MOST SIGNIFICANT change as the primary type.

Files changed:
{files_summary}

Git diffs:
{diffs}

Provide ONLY the commit message, nothing else. No explanation, no markdown, no quotes.
Example: feat: add JWT authentication system
"""

# Placeholders that MUST survive any user edit, otherwise generation silently
# produces garbage. Referenced by config_manager.validate_prompt_template().
REQUIRED_PROMPT_PLACEHOLDERS = ("{files_summary}", "{diffs}")

# The conventional-commit types recognised out of the box. Exposed as data (not a
# hard-coded regex) so users can add project-specific types (e.g. "deps", "wip")
# from the UI without touching the validator code.
DEFAULT_ALLOWED_TYPES = [
    "feat", "fix", "docs", "style", "refactor",
    "test", "build", "ci", "perf", "chore", "modify", "revert",
]

# Words that usually signal an unfinished commit. User-extensible from the UI.
DEFAULT_FORBIDDEN_WORDS = ["wip", "todo", "fixme", "xxx", "temp"]

# The complete default configuration tree. The config manager deep-merges this
# with the user's config.json so newly-added keys in future versions get safe
# defaults automatically (forward compatibility for existing installs).
DEFAULT_CONFIG = {
    "ai": {
        # Stored here only if the user types it into the UI. Left empty by default
        # so the legacy `.env` GEMINI_API_KEY keeps working untouched.
        "api_key": "",
        "model": "gemini-2.0-flash",
        # Diffs larger than this are truncated before hitting the API. Lower = cheaper
        # / faster; higher = more context. Surfaced as a slider in the UI.
        "max_diff_chars": 30000,
        "prompt_template": DEFAULT_PROMPT_TEMPLATE,
    },
    "validation": {
        "max_subject_length": 72,
        "min_message_length": 10,
        "check_api_keys": True,
        "check_sensitive_data": True,
        "enforce_conventional_commits": True,
        "enforce_length_limit": True,
        "allow_override": True,
        "allowed_types": DEFAULT_ALLOWED_TYPES,
        "forbidden_words": DEFAULT_FORBIDDEN_WORDS,
        # User-defined secret patterns, each {"name": str, "pattern": str}. These are
        # compiled at runtime; invalid regex is rejected at save time by the UI/API so
        # a bad pattern can never crash a commit run.
        "custom_secret_patterns": [],
    },
    "history": {
        # When true, every generated message (and whether it was accepted/edited) is
        # appended to history.jsonl for the stats dashboard. Purely local.
        "enabled": True,
    },
    "ui": {
        # Loopback-only by default; the settings server never binds to a public
        # interface unless the user deliberately changes this.
        "host": "127.0.0.1",
        "port": 8420,
        "theme": "auto",  # auto | light | dark
    },
}
