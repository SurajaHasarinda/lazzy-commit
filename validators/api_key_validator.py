import re
from typing import Tuple

from validators.base import CommitValidator


class APIKeyValidator(CommitValidator):
    """
    Scans content for credentials that must never reach a commit.

    The built-in pattern set covers the most common providers. It is intentionally
    kept here (rather than in config) because these are well-known, security-critical
    signatures we always want on — users extend, never replace, them via the
    separate CustomSecretValidator.
    """

    # Predefined patterns for various API keys and secrets.
    PATTERNS = {
        'AWS Access Key': r'AKIA[0-9A-Z]{16}',
        'AWS Secret Key': r'aws(.{0,20})?["\']?[0-9a-zA-Z/+]{40}["\']?',
        'GitHub Token': r'ghp_[a-zA-Z0-9]{36}',
        'GitHub OAuth': r'gho_[a-zA-Z0-9]{36}',
        'Google API Key': r'AIza[0-9A-Za-z\-_]{35}',
        'Google OAuth': r'ya29\.[0-9A-Za-z\-_]+',
        'Slack Token': r'xox[baprs]-[0-9a-zA-Z]{10,48}',
        'Slack Webhook': r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}',
        'Private Key': r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        'Generic API Key': r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
        'Generic Secret': r'["\']?secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
        'JWT Token': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        'Password in Code': r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\'](?!old-pass|new-pass|different|password|test|example|sample|demo|placeholder|your-password|123456|admin)[^"\']{10,}["\']',
        'Stripe API Key': r'sk_live_[0-9a-zA-Z]{24,}',
        'Twilio API Key': r'SK[a-zA-Z0-9]{32}',
        'Square Access Token': r'sq0atp-[0-9A-Za-z\-_]{22}',
        'PayPal/Braintree': r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
        'Heroku API Key': r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
    }

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check for API keys and secrets in the content.

        Args:
            content: The content to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        detected = []

        for key_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                detected.append(f"{key_type}: {match.group()}")

        if detected:
            keys_list = "\n  ".join(detected)
            return False, f"🔒 BLOCKED:\n  {keys_list}"

        return True, ""


class SensitiveDataValidator(CommitValidator):
    """Catches personal data (cards, SSNs) that should never be committed."""

    # Predefined patterns for sensitive data.
    PATTERNS = {
        'Credit Card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
    }

    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Check for sensitive data like credit cards and SSNs in the content.

        Args:
            content: The content to validate.

        Returns:
            (is_valid, reason_if_invalid)
        """
        detected = []

        for data_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, content):
                detected.append(f"{data_type}: {match.group()}")

        if detected:
            data_list = "\n  ".join(detected)
            return False, f"🔒 BLOCKED:\n  {data_list}"

        return True, ""
