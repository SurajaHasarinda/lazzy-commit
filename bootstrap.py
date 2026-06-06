from typing import Optional

from config.config_manager import ConfigManager
from core.git_interface import GitInterface
from core.ai_interface import AIInterface
from validators.api_key_validator import APIKeyValidator, SensitiveDataValidator
from validators.format_validator import (
    ConventionalCommitValidator,
    LengthValidator,
    ContentValidator,
)
from validators.custom_validator import CustomSecretValidator
from services.validation_chain import ValidationChain
from services.commit_service import CommitService
from services.history_service import HistoryService


def build_validation_chain(cfg: ConfigManager) -> ValidationChain:
    """
    Assemble the validator chain honouring every toggle and custom rule.

    Order matters for the message pass: security first (most important to surface),
    then format, length, and content. Each validator is constructed with the
    user's configured parameters rather than hard-coded defaults.
    """
    v = cfg.get("validation", {})
    chain = ValidationChain()

    if v.get("check_api_keys", True):
        chain.add_validator(APIKeyValidator())

    if v.get("check_sensitive_data", True):
        chain.add_validator(SensitiveDataValidator())

    # Custom secret patterns are a security layer too; only add the validator when
    # the user has actually defined patterns, to avoid an empty no-op in the chain.
    custom_patterns = v.get("custom_secret_patterns", [])
    if custom_patterns:
        chain.add_validator(CustomSecretValidator(custom_patterns))

    if v.get("enforce_conventional_commits", True):
        chain.add_validator(ConventionalCommitValidator(allowed_types=v.get("allowed_types")))

    if v.get("enforce_length_limit", True):
        chain.add_validator(LengthValidator(max_subject_length=v.get("max_subject_length", 72)))

    # Content rules (forbidden words / min length) always run — they're the cheap
    # last line of defence against empty or placeholder messages.
    chain.add_validator(
        ContentValidator(
            forbidden_words=v.get("forbidden_words"),
            min_message_length=v.get("min_message_length", 10),
        )
    )
    return chain


def build_history(cfg: ConfigManager) -> HistoryService:
    """Construct the history service pointed at the per-user JSONL log."""
    return HistoryService(
        history_path=cfg.history_path,
        enabled=cfg.get("history.enabled", True),
    )


def build_ai(cfg: ConfigManager, api_key: Optional[str] = None) -> AIInterface:
    """
    Construct the AI interface from config.

    `api_key` can be passed explicitly (e.g. the UI's "test this key before
    saving" flow); otherwise it's resolved through the normal precedence chain.
    """
    return AIInterface(
        api_key=api_key or cfg.resolve_api_key(),
        model_name=cfg.get("ai.model"),
        prompt_template=cfg.get("ai.prompt_template"),
        max_diff_chars=cfg.get("ai.max_diff_chars", 30000),
    )


def build_commit_service(cfg: ConfigManager) -> CommitService:
    """Wire up the full commit service used by the CLI run."""
    return CommitService(
        git_interface=GitInterface(),
        ai_interface=build_ai(cfg),
        validation_chain=build_validation_chain(cfg),
        history_service=build_history(cfg),
    )
