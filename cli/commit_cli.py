from typing import Optional

from services.commit_service import CommitService


class CommitCLI:
    """
    Interactive terminal workflow for generating and confirming a commit.

    Compared with the original, this version threads an `overridden` flag through
    the run and records the final outcome (committed / edited / cancelled /
    pushed) to history, so the stats dashboard reflects what actually happened.
    """

    def __init__(self, commit_service: CommitService, should_push: bool = False, allow_override: bool = True):
        self.commit_service = commit_service
        self.should_push = should_push
        self.allow_override = allow_override
        # Tracks whether a security/validation block was bypassed during this run,
        # so the recorded history entry can flag it for the "overrides" stat.
        self._overridden = False

    def run(self) -> int:
        """
        Run the CLI workflow.

        Returns:
            Exit code (0 for success, 1 for failure).
        """
        try:
            # --- 1. Collect staged changes (with security scan) ---
            print("🔍 Analyzing...")
            success, file_diffs, errors = self.commit_service.collect_changes()

            if not success:
                print(f"✗ {errors[0]}" if errors else "✗ Failed")
                for error in errors[1:]:
                    print(error)

                # Only a security BLOCK is overridable; "no staged changes" is not.
                if self.allow_override and errors and "BLOCKED" in str(errors):
                    if self._confirm_override("security check"):
                        print("⚠️  Override accepted - proceeding with caution")
                        self._overridden = True
                        success, file_diffs, errors = self.commit_service.collect_changes_unsafe()
                        if not success:
                            print(f"✗ Failed to collect changes: {errors[0] if errors else 'Unknown error'}")
                            return 1
                    else:
                        return 1
                else:
                    return 1

            print(f"✓ {len(file_diffs)} file(s)")

            # --- 2. Generate the message ---
            print("🤖 Generating...")
            success, message, errors = self.commit_service.generate_commit_message(file_diffs)

            if not success:
                print("✗ Validation failed:")
                for error in errors:
                    print(error)

                if self.allow_override and message:
                    if self._confirm_override("validation"):
                        print("⚠️  Override accepted - using generated message")
                        self._overridden = True
                    else:
                        return 1
                else:
                    return 1

            if not message:
                print("✗ No message generated")
                return 1

            # --- 3. Review ---
            print("\n" + "─" * 50)
            print(message)
            print("─" * 50 + "\n")

            # --- 4. Confirm / edit / cancel ---
            action = self._get_confirmation()
            file_count = len(file_diffs)

            if action == 'yes':
                return self._execute_commit(message, file_count, edited=False)
            elif action == 'edit':
                edited = self._edit_message(message)
                if not edited:
                    print("✗ Cancelled")
                    self.commit_service.record_history(message, "cancelled", file_count, self._overridden)
                    return 1
                return self._execute_commit(edited, file_count, edited=True)
            else:
                print("✗ Cancelled")
                self.commit_service.record_history(message, "cancelled", file_count, self._overridden)
                return 1

        except KeyboardInterrupt:
            print("\n✗ Cancelled")
            return 1
        except Exception as e:
            print(f"✗ Error: {e}")
            return 1

    def _confirm_override(self, validation_type: str) -> bool:
        """
        Ask whether to bypass a failed check.

        Args:
            validation_type: Human label for the check that failed.

        Returns:
            True if the user confirms the override.
        """
        print(f"\n⚠️  WARNING: {validation_type} failed!")
        print("This may include sensitive data or security risks.")
        response = input("Override and continue anyway? (yes/no): ").strip().lower()
        return response in ['yes', 'y']

    def _get_confirmation(self) -> str:
        """
        Prompt until the user gives a valid choice.

        Returns:
            'yes', 'no', or 'edit'.
        """
        while True:
            response = input("(y)es / (n)o / (e)dit: ").strip().lower()
            if response in ['y', 'yes']:
                return 'yes'
            elif response in ['n', 'no']:
                return 'no'
            elif response in ['e', 'edit']:
                return 'edit'

    def _edit_message(self, original: str) -> Optional[str]:
        """
        Let the user retype the message (Enter twice to finish).

        Args:
            original: The generated message, shown for reference.

        Returns:
            The edited message, or None if the user entered nothing.
        """
        print(f"\nCurrent: {original}")
        print("New (Enter twice to finish):\n")

        lines = []
        empty_count = 0

        while empty_count < 2:
            line = input()
            if line == "":
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)

        return '\n'.join(lines).strip() or None

    def _execute_commit(self, message: str, file_count: int, edited: bool) -> int:
        """
        Commit (and optionally push), recording the outcome to history.

        Args:
            message: The final commit message.
            file_count: Number of staged files (for stats).
            edited: Whether the user edited the AI's message before committing.

        Returns:
            Exit code (0 success, 1 failure).
        """
        print("💾 Committing...")
        success, _ = self.commit_service.execute_commit(message)

        if not success:
            print("✗ Commit failed")
            return 1

        print("✓ Committed")

        # Record before pushing so the commit is logged even if the push fails.
        outcome = "edited" if edited else "committed"
        self.commit_service.record_history(message, outcome, file_count, self._overridden)

        if self.should_push:
            print("🚀 Pushing...")
            success, _ = self.commit_service.execute_push()
            if success:
                print("✓ Pushed")
                self.commit_service.record_history(message, "pushed", file_count, self._overridden)
                return 0
            print("✗ Push failed")
            return 1

        return 0
