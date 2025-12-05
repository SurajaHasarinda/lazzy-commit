from abc import ABC, abstractmethod
from typing import Tuple
import re

class CommitValidator(ABC):
    
    @abstractmethod
    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Validate the commit message.

        Args:
            content: The content to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        pass