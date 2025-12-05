import re
from typing import Tuple
from validators.base import CommitValidator

class ConventionalCommitValidator(CommitValidator):
    
    PATTERN = r'^(feat|fix|docs|style|refactor|test|build|ci|modify|revert)(\(.+?\))?!?:\s.+$'
    
    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check if the commit message follows Conventional Commit format.

        Args:
            content: The commit message to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        first_line = content.split('\n')[0].strip()
        if not re.match(self.PATTERN, first_line):
            return False, "Invalid format (use: type(scope): description)"
        return True, ""


class LengthValidator(CommitValidator):
    
    def __init__(self, max_subject_length: int = 100):
        """
        Initialize LengthValidator.

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
    
    FORBIDDEN = ['wip', 'todo', 'fixme', 'xxx', 'temp']
    
    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check for forbidden words and message length in the content.

        Args:
            content: The commit message to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        first_line = content.split('\n')[0].lower()
        
        for word in self.FORBIDDEN:
            if word in first_line:
                return False, f"Contains '{word}' - avoid WIP commits"
        
        if len(first_line) < 10:
            return False, "Message too short"
        
        return True, ""