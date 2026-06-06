import re
from typing import List, Tuple

from validators.base import CommitValidator
from config.defaults import DEFAULT_ALLOWED_TYPES, DEFAULT_FORBIDDEN_WORDS


class ConventionalCommitValidator(CommitValidator):
    """
    Enforces the Conventional Commits subject format.

    The original hard-coded the allowed types into a regex literal. Here the type
    list is injected, so a team can add project-specific types (e.g. "deps",
    "release") from the settings UI without code changes. The regex is rebuilt
    from that list at construction time.
    """

    def __init__(self, allowed_types: List[str] | None = None):
        types = allowed_types or DEFAULT_ALLOWED_TYPES
        # Escape each type and join into an alternation. Types are validated to be
        # simple tokens upstream, but we escape anyway to stay injection-proof if a
        # caller bypasses that validation.
        alternation = "|".join(re.escape(t) for t in types)
        # Mirrors the original pattern: optional (scope), optional ! for breaking
        # change, then ": " and a non-empty description.
        self._pattern = re.compile(rf'^({alternation})(\(.+?\))?!?:\s.+$')
        self._types = list(types)

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check if the commit message follows Conventional Commit format.

        Args:
            content: The commit message to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        first_line = content.split('\n')[0].strip()
        if not self._pattern.match(first_line):
            allowed = ", ".join(self._types)
            return False, f"Invalid format (use: type(scope): description; types: {allowed})"
        return True, ""


class LengthValidator(CommitValidator):
    """Caps the subject line length so it stays readable in `git log --oneline`."""

    def __init__(self, max_subject_length: int = 72):
        """
        Args:
            max_subject_length: Maximum allowed length for the subject line.
        """
        self.max_subject_length = max_subject_length

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check if the subject line exceeds the maximum length.

        Args:
            content: The commit message to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        first_line = content.split('\n')[0]
        if len(first_line) > self.max_subject_length:
            return False, f"Subject too long ({len(first_line)}/{self.max_subject_length})"
        return True, ""


class ContentValidator(CommitValidator):
    """
    Blocks placeholder/unfinished commits and over-terse messages.

    Both the forbidden-word list and the minimum length are configurable so teams
    can tune strictness from the UI (e.g. allow very short messages, or ban extra
    words like "asdf").
    """

    def __init__(self, forbidden_words: List[str] | None = None, min_message_length: int = 10):
        # Stored lowercase for case-insensitive matching against the subject.
        self.forbidden_words = [w.lower() for w in (forbidden_words or DEFAULT_FORBIDDEN_WORDS)]
        self.min_message_length = min_message_length

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check for forbidden words and minimum length.

        Args:
            content: The commit message to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        first_line = content.split('\n')[0].lower()

        for word in self.forbidden_words:
            # Word-boundary match so "template" doesn't trip the "temp" rule —
            # the original substring check produced false positives like that.
            if re.search(rf'\b{re.escape(word)}\b', first_line):
                return False, f"Contains '{word}' - avoid WIP/placeholder commits"

        if len(first_line) < self.min_message_length:
            return False, f"Message too short (min {self.min_message_length} chars)"

        return True, ""
