import os
import json
import copy
import re
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

from dotenv import load_dotenv

from config.defaults import DEFAULT_CONFIG, DEFAULT_PROMPT_TEMPLATE, REQUIRED_PROMPT_PLACEHOLDERS

# Load .env once, here, so the legacy layer is available regardless of which
# entry point (CLI commit run or web server) imported us first.
load_dotenv()


def _home_dir() -> Path:
    """
    Resolve the directory that holds config.json and history.jsonl.

    We deliberately default to ~/.lazzycommit rather than the repo directory:
    the tool is installed once and run from *many* git repos, so per-user state
    must live outside any single repo (and well away from anything that could be
    staged and committed). LAZZYCOMMIT_HOME overrides this for tests / portable
    installs.
    """
    override = os.getenv("LAZZYCOMMIT_HOME")
    base = Path(override) if override else Path.home() / ".lazzycommit"
    base.mkdir(parents=True, exist_ok=True)
    return base


# The legacy `.env` files store booleans as the strings "true"/"false".
def _as_bool(value: str) -> bool:
    return str(value).lower() == "true"


# Maps a dotted config path to the legacy environment variable that seeds it.
# Only these keys participate in the .env backward-compat layer; everything else
# comes from defaults or config.json. Values are (env_name, caster).
_ENV_BINDINGS: Dict[str, Tuple[str, Callable[[str], Any]]] = {
    "ai.model": ("GEMINI_MODEL", str),
    "validation.max_subject_length": ("MAX_SUBJECT_LENGTH", int),
    "validation.check_api_keys": ("CHECK_API_KEYS", _as_bool),
    "validation.check_sensitive_data": ("CHECK_SENSITIVE_DATA", _as_bool),
    "validation.enforce_conventional_commits": ("ENFORCE_CONVENTIONAL_COMMITS", _as_bool),
    "validation.enforce_length_limit": ("ENFORCE_LENGTH_LIMIT", _as_bool),
    "validation.allow_override": ("ALLOW_OVERRIDE", _as_bool),
}


class ConfigManager:
    """Loads, merges, validates and persists the configuration tree."""

    def __init__(self, home: Path | None = None):
        self.home = home or _home_dir()
        self.config_path = self.home / "config.json"
        self.history_path = self.home / "history.jsonl"
        # A lock guards read-modify-write cycles so a commit run and the web UI
        # saving simultaneously can't corrupt config.json.
        self._lock = threading.RLock()
        self._config = self._build()

    # ----- loading / merging -------------------------------------------------

    def _build(self) -> Dict[str, Any]:
        """Compose the effective config from the three precedence layers."""
        merged = copy.deepcopy(DEFAULT_CONFIG)
        self._apply_env_layer(merged)
        self._apply_file_layer(merged)
        return merged

    def _apply_env_layer(self, cfg: Dict[str, Any]) -> None:
        """Overlay legacy .env values where they are actually present."""
        for dotted, (env_name, cast) in _ENV_BINDINGS.items():
            raw = os.getenv(env_name)
            if raw is None:
                continue
            try:
                _set_dotted(cfg, dotted, cast(raw))
            except (ValueError, TypeError):
                # A malformed env var should never crash startup; defaults stand.
                pass

    def _apply_file_layer(self, cfg: Dict[str, Any]) -> None:
        """Deep-merge the UI-managed config.json on top, if it exists."""
        if not self.config_path.exists():
            return
        try:
            stored = json.loads(self.config_path.read_text(encoding="utf-8"))
            _deep_merge(cfg, stored)
        except (json.JSONDecodeError, OSError):
            # Corrupt config.json shouldn't brick the CLI; fall back to lower layers.
            pass

    def reload(self) -> None:
        """Rebuild from disk — used by the server after a save in another process."""
        with self._lock:
            self._config = self._build()

    # ----- accessors ---------------------------------------------------------

    def all(self) -> Dict[str, Any]:
        """Return a deep copy so callers can't mutate internal state by accident."""
        with self._lock:
            return copy.deepcopy(self._config)

    def get(self, dotted: str, default: Any = None) -> Any:
        with self._lock:
            return _get_dotted(self._config, dotted, default)

    def resolve_api_key(self) -> str:
        """
        Decide which API key to actually use.

        Precedence: a key the user typed into the UI (stored in config.json)
        wins; otherwise we fall back to the legacy GEMINI_API_KEY env var. This
        means existing `.env`-only users need no migration, while UI users never
        have to touch a dotfile.
        """
        stored = self.get("ai.api_key", "") or ""
        return stored.strip() or (os.getenv("GEMINI_API_KEY") or "").strip()

    def api_key_source(self) -> str:
        """Tell the UI where the active key comes from, without revealing it."""
        if (self.get("ai.api_key", "") or "").strip():
            return "config"
        if (os.getenv("GEMINI_API_KEY") or "").strip():
            return "env"
        return "none"

    # ----- mutation / persistence -------------------------------------------

    def update(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and persist a partial config update from the UI.

        Only the keys present in `patch` are touched (deep-merged), so the UI can
        send just the section the user edited. Raises ValueError with a
        human-readable message on invalid input so the API can return a 400.
        """
        with self._lock:
            candidate = copy.deepcopy(self._config)
            _deep_merge(candidate, patch)
            self._validate(candidate)

            # Persist everything *except* secrets we'd rather not write to disk
            # unless the user explicitly provided one through the UI.
            self._write_file(candidate)
            self._config = candidate
            return copy.deepcopy(self._config)

    def reset_prompt(self) -> Dict[str, Any]:
        """Restore the factory prompt template (one-click button in the UI)."""
        return self.update({"ai": {"prompt_template": DEFAULT_PROMPT_TEMPLATE}})

    def _write_file(self, cfg: Dict[str, Any]) -> None:
        """
        Write config.json atomically.

        A temp-file + replace avoids a half-written file if the process dies
        mid-write — config.json is read on every CLI run, so a truncated file
        would break commits, not just the UI.
        """
        tmp = self.config_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.config_path)

    # ----- validation --------------------------------------------------------

    def _validate(self, cfg: Dict[str, Any]) -> None:
        """Reject structurally-valid-but-nonsensical configs before they persist."""
        v = cfg.get("validation", {})

        max_len = v.get("max_subject_length")
        if not isinstance(max_len, int) or not (10 <= max_len <= 200):
            raise ValueError("max_subject_length must be an integer between 10 and 200")

        min_len = v.get("min_message_length")
        if not isinstance(min_len, int) or not (1 <= min_len <= max_len):
            raise ValueError("min_message_length must be an integer between 1 and max_subject_length")

        if not isinstance(v.get("allowed_types"), list) or not v["allowed_types"]:
            raise ValueError("allowed_types must be a non-empty list")
        for t in v["allowed_types"]:
            # Types become part of a regex alternation; restrict to safe tokens.
            if not isinstance(t, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", t):
                raise ValueError(f"invalid commit type '{t}' (use lowercase letters/digits/hyphen)")

        for entry in v.get("custom_secret_patterns", []):
            if not isinstance(entry, dict) or "pattern" not in entry or "name" not in entry:
                raise ValueError("each custom secret pattern needs a 'name' and 'pattern'")
            try:
                re.compile(entry["pattern"])
            except re.error as exc:
                raise ValueError(f"invalid regex in pattern '{entry.get('name')}': {exc}")

        self.validate_prompt_template(cfg.get("ai", {}).get("prompt_template", ""))

        port = cfg.get("ui", {}).get("port")
        if not isinstance(port, int) or not (1024 <= port <= 65535):
            raise ValueError("ui.port must be an integer between 1024 and 65535")

    @staticmethod
    def validate_prompt_template(template: str) -> None:
        """A custom prompt is useless if it drops the placeholders the engine fills."""
        if not isinstance(template, str) or not template.strip():
            raise ValueError("prompt template cannot be empty")
        missing = [p for p in REQUIRED_PROMPT_PLACEHOLDERS if p not in template]
        if missing:
            raise ValueError(
                f"prompt template is missing required placeholder(s): {', '.join(missing)}"
            )


# ----- small dotted-path helpers (kept module-level so they're trivially testable) -----

def _get_dotted(d: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _set_dotted(d: Dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = d
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> None:
    """
    Recursively merge `overlay` into `base` in place.

    Dicts merge key-by-key; everything else (including lists like allowed_types)
    replaces wholesale — a user clearing a list in the UI must actually clear it,
    not merge against the default.
    """
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
