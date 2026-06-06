from abc import ABC, abstractmethod
from typing import Tuple


class CommitValidator(ABC):
    """
    Common interface for every validation rule.

    A validator answers one yes/no question about a piece of text and explains a
    "no". Validators that also expose a `PATTERNS` attribute are treated as
    *security* validators and additionally run against raw diffs (see
    ValidationChain.validate_diff) — that attribute is the marker the chain uses
    to decide what is safe to scan against secret-bearing diff content.
    """

    @abstractmethod
    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Validate the given content.

        Args:
            content: The text to validate (a commit message, or a diff).

        Returns:
            (is_valid, reason_if_invalid). `reason_if_invalid` is empty when valid.
        """
        raise NotImplementedError
