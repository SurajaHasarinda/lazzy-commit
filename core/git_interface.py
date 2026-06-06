import subprocess
from typing import List, Optional, Tuple


class GitInterface:
    """Thin, dependency-free wrapper over the git CLI used by the rest of the app."""

    def __init__(self):
        pass

    def get_staged_files(self) -> List[str]:
        """
        Get list of staged files.

        Returns:
            List of staged file paths.
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get staged files: {e.stderr}")

    def get_file_diff(self, file_path: str, max_lines: int = 500) -> str:
        """
        Get diff for a specific file.

        Args:
            file_path: Path to the file.
            max_lines: Maximum number of lines to return.

        Returns:
            The diff text for the file, truncated if necessary.
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--", file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )

            diff_text = result.stdout
            lines = diff_text.split('\n')

            if len(lines) > max_lines:
                truncated = lines[:max_lines]
                truncated.append(f"\n... (truncated {len(lines) - max_lines} lines)")
                diff_text = '\n'.join(truncated)

            return diff_text
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get diff for {file_path}: {e.stderr}")

    def commit(self, message: str) -> bool:
        """
        Execute git commit.

        Args:
            message: Commit message.

        Returns:
            True if commit was successful, False otherwise.
        """
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def push(self) -> Tuple[bool, str]:
        """
        Execute git push.

        Returns:
            A tuple (is_successful, output_message).
        """
        try:
            result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def has_staged_changes(self) -> bool:
        """
        Check if there are staged changes.

        Returns:
            True if there are staged changes, False otherwise.
        """
        try:
            # `--quiet` exits 1 when there *is* a diff; that's the signal we want.
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True
            )
            return result.returncode == 1
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """
        Get the current branch name.

        Added for the history feature so each recorded commit knows which branch
        it happened on (useful when reviewing stats per-branch). Returns None
        rather than raising, because branch context is nice-to-have metadata and
        must never block a commit.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            return branch or None
        except subprocess.CalledProcessError:
            return None

    def get_repo_name(self) -> Optional[str]:
        """
        Best-effort repository name (top-level dir), used to label history entries.
        Returns None outside a git repo.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            top = result.stdout.strip()
            return top.replace("\\", "/").rstrip("/").split("/")[-1] if top else None
        except subprocess.CalledProcessError:
            return None
