from config.config_manager import ConfigManager

_cfg = ConfigManager()

# --- Legacy constant surface (kept identical to the original settings.py) -----
GEMINI_API_KEY = _cfg.resolve_api_key()
GEMINI_MODEL = _cfg.get("ai.model")
MAX_SUBJECT_LENGTH = _cfg.get("validation.max_subject_length")
CHECK_API_KEYS = _cfg.get("validation.check_api_keys")
CHECK_SENSITIVE_DATA = _cfg.get("validation.check_sensitive_data")
ENFORCE_CONVENTIONAL_COMMITS = _cfg.get("validation.enforce_conventional_commits")
ENFORCE_LENGTH_LIMIT = _cfg.get("validation.enforce_length_limit")
ALLOW_OVERRIDE = _cfg.get("validation.allow_override")
