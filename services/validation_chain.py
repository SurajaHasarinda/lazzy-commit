from typing import List, Tuple

from validators.base import CommitValidator


class ValidationChain:
    """
    Runs a composed list of validators (Chain of Responsibility).

    Two entry points exist because messages and diffs need different subsets:
    `validate_message` runs everything against the generated subject, while
    `validate_diff` runs *only* security validators (those exposing PATTERNS)
    against raw diff content — we never want format/length rules firing on a diff.
    """

    def __init__(self):
        self.validators: List[CommitValidator] = []

    def add_validator(self, validator: CommitValidator) -> "ValidationChain":
        """
        Add a validator to the chain.

        Returns:
            self, so adds can be chained fluently.
        """
        self.validators.append(validator)
        return self

    def validate_message(self, message: str) -> Tuple[bool, List[str]]:
        """
        Validate the commit message against every validator.

        Returns:
            (is_valid, errors) — all failures are collected, not short-circuited,
            so the user sees every problem at once instead of one-at-a-time.
        """
        errors = []
        for validator in self.validators:
            is_valid, reason = validator.validate(message)
            if not is_valid and reason:
                errors.append(reason)
        return len(errors) == 0, errors

    def validate_diff(self, diff_content: str) -> Tuple[bool, List[str]]:
        """
        Validate diff content with security validators only.

        The `PATTERNS` attribute is the marker for "this validator scans for
        secrets and is safe/meaningful to run on a raw diff". Format and content
        validators are intentionally skipped here.

        Returns:
            (is_valid, errors)
        """
        errors = []
        for validator in self.validators:
            if hasattr(validator, "PATTERNS"):
                is_valid, reason = validator.validate(diff_content)
                if not is_valid and reason:
                    errors.append(reason)
        return len(errors) == 0, errors
