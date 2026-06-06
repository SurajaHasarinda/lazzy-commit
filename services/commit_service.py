from typing import List, Dict, Tuple, Optional

from core.git_interface import GitInterface
from core.ai_interface import AIInterface
from services.validation_chain import ValidationChain
from services.history_service import HistoryService


class CommitService:
    """
    Orchestrates the commit workflow: collect diffs -> generate -> validate ->
    commit/push, and (new) record each run to history.

    History is injected as an optional dependency so the service still works in
    contexts where we don't want logging (tests), and so the single source of git
    context (repo/branch) lives in one place rather than being re-derived in the CLI.
    """

    def __init__(
        self,
        git_interface: GitInterface,
        ai_interface: AIInterface,
        validation_chain: ValidationChain,
        history_service: Optional[HistoryService] = None,
    ):
        self.git = git_interface
        self.ai = ai_interface
        self.validation_chain = validation_chain
        self.history = history_service

    def collect_changes(self) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """
        Collect staged changes, running the security check on each diff.

        Returns:
            (is_successful, changes, errors). Fails fast on the first diff that
            trips a security validator so a secret is never sent to the AI.
        """
        return self._collect(run_security=True)

    def collect_changes_unsafe(self) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """
        Collect staged changes WITHOUT the security check.

        Only reached after the user has explicitly chosen to override a security
        block in the CLI. Kept as a distinct method (rather than a boolean flag on
        the public call) so the override is always an obvious, deliberate code path.
        """
        return self._collect(run_security=False)

    def _collect(self, run_security: bool) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """Shared collection logic for the safe/unsafe variants."""
        try:
            if not self.git.has_staged_changes():
                return False, [], ["No staged changes found."]

            staged_files = self.git.get_staged_files()
            if not staged_files:
                return False, [], ["No staged files found."]

            file_diffs = []
            for file_path in staged_files:
                try:
                    diff = self.git.get_file_diff(file_path)
                    if diff:
                        if run_security:
                            is_safe, errors = self.validation_chain.validate_diff(diff)
                            if not is_safe:
                                return False, [], errors
                        file_diffs.append({"file": file_path, "diff": diff})
                except Exception as e:
                    return False, [], [f"Failed to read {file_path}: {str(e)}"]

            return True, file_diffs, []
        except Exception as e:
            return False, [], [str(e)]

    def generate_commit_message(
        self, file_diffs: List[Dict[str, str]]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Generate and validate a commit message.

        Returns:
            (is_successful, commit_message, errors). On validation failure the
            message is still returned so the CLI can offer an override.
        """
        try:
            message = self.ai.generate_commit_message(file_diffs)
            if not message:
                return False, None, ["AI generation failed"]

            is_valid, errors = self.validation_chain.validate_message(message)
            if not is_valid:
                return False, message, errors

            return True, message, []
        except Exception as e:
            return False, None, [str(e)]

    def execute_commit(self, message: str) -> Tuple[bool, str]:
        """
        Execute git commit.

        Returns:
            (is_successful, output_message).
        """
        try:
            return (True, "Success") if self.git.commit(message) else (False, "Failed")
        except Exception as e:
            return False, str(e)

    def execute_push(self) -> Tuple[bool, str]:
        """
        Execute git push.

        Returns:
            (is_successful, output_message).
        """
        try:
            return self.git.push()
        except Exception as e:
            return False, str(e)

    def record_history(
        self, message: str, outcome: str, file_count: int = 0, overridden: bool = False
    ) -> None:
        """
        Log a commit event, enriching it with git context.

        Centralised here because this is the one place that owns both the GitInterface
        (for repo/branch) and the HistoryService — keeping the CLI free of that wiring.
        """
        if not self.history:
            return
        self.history.record(
            message=message,
            outcome=outcome,
            repo=self.git.get_repo_name(),
            branch=self.git.get_current_branch(),
            file_count=file_count,
            overridden=overridden,
        )
