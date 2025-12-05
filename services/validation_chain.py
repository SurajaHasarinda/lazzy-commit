from typing import List, Tuple
from validators.base import CommitValidator

class ValidationChain:

    def __init__(self):
        self.validators: List[CommitValidator] = []
    
    def add_validator(self, validator: CommitValidator) -> 'ValidationChain':
        """
        Add a validator to the chain.

        Args:
            validator: An instance of CommitValidator to add.

        Returns:
            The ValidationChain instance (for method chaining).
        """
        self.validators.append(validator)
        return self

    def validate_message(self, message: str) -> Tuple[bool, List[str]]:
        """
        Validate the commit message using the chain of validators.

        Args:
            message: The commit message to validate.

        Returns:
            A tuple (is_valid, reason_if_invalid).
        """
        errors = []
        for validator in self.validators:
            is_valid, reason = validator.validate(message)
            if not is_valid and reason:
                errors.append(reason)
        
        return len(errors) == 0, errors

    def validate_diff(self, diff_content: str) -> Tuple[bool, List[str]]:
        """
        Validate diff content (security checks only).

        Args:
            diff: The commit diff to validate.

        Returns:
            A tuple (is_valid, reason_if_invalid).
        """
        errors = []
        for validator in self.validators:
            # Only run security validators on diff
            if hasattr(validator, 'PATTERNS'):
                is_valid, reason = validator.validate(diff_content)
                if not is_valid and reason:
                    errors.append(reason)
        return len(errors) == 0, errors
