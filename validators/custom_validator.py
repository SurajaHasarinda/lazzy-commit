import re
from typing import Dict, List, Tuple

from validators.base import CommitValidator


class CustomSecretValidator(CommitValidator):
    """
    User-defined secret/forbidden patterns from the settings UI.

    This exists as its own validator (rather than mutating APIKeyValidator) for
    two reasons:
      1. It keeps the trusted built-in signatures separate from user input, so a
         user mistake can never weaken or overwrite the defaults.
      2. It exposes a `PATTERNS` attribute, which is the marker ValidationChain
         uses to also run a validator against raw diffs — so a team can block,
         say, an internal hostname or a project-specific token format in diffs,
         exactly like the built-in security checks.

    Patterns are validated (compiled) when saved via the API, but we compile
    defensively here too and skip any bad entry instead of crashing a commit run.
    """

    def __init__(self, patterns: List[Dict[str, str]] | None = None):
        """
        Args:
            patterns: list of {"name": str, "pattern": str} from config.
        """
        # PATTERNS mirrors the {label: regex} shape of the built-in validators so
        # the rest of the system can treat all security validators uniformly.
        self.PATTERNS: Dict[str, str] = {}
        for entry in patterns or []:
            name = (entry.get("name") or "").strip()
            pattern = entry.get("pattern") or ""
            if not name or not pattern:
                continue
            try:
                re.compile(pattern)
            except re.error:
                # A malformed user regex is ignored rather than fatal — the UI
                # already warns on save, so this is just belt-and-braces.
                continue
            self.PATTERNS[name] = pattern

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check content against every user-defined pattern.

        Returns:
            (is_valid, reason_if_invalid)
        """
        if not self.PATTERNS:
            return True, ""

        detected = []
        for name, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                detected.append(f"{name}: {match.group()}")

        if detected:
            hits = "\n  ".join(detected)
            return False, f"🔒 BLOCKED (custom rule):\n  {hits}"

        return True, ""
