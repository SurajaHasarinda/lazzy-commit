from typing import List, Dict, Tuple, Optional
from core.git_interface import GitInterface
from core.ai_interface import AIInterface
from services.validation_chain import ValidationChain

class CommitService:

    def __init__(
        self,
        git_interface: GitInterface,
        ai_interface: AIInterface,
        validation_chain: ValidationChain
    ):
        self.git = git_interface
        self.ai = ai_interface
        self.validation_chain = validation_chain

    def collect_changes(self) -> Tuple[bool, List[Dict[str, str]], List[str]]:
        """
        Collect staged changes from the Git repository.

        Args:
            None

        Returns:
            A tuple (is_successful, changes, errors).
        """
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
                        # Security check on diff
                        is_safe, errors = self.validation_chain.validate_diff(diff)
                        if not is_safe:
                            return False, [], errors

                        file_diffs.append({"file": file_path, "diff": diff})
                except Exception as e:
                    return False, [], [f"Failed to read {file_path}: {str(e)}"]

            return True, file_diffs, []

        except Exception as e:
            return False, [], [str(e)]

    def generate_commit_message(self, file_diffs: List[Dict[str, str]]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Generate and validate commit message.
        
        Args:
            file_diffs (List[Dict[str, str]]): List of file diffs.

        Returns:
            A tuple (is_successful, commit_message, errors).
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

        Args:
            message: Commit message.

        Returns:
            A tuple (is_successful, output_message).
        """
        try:
            return (True, "Success") if self.git.commit(message) else (False, "Failed")
        except Exception as e:
            return False, str(e)        

    def execute_push(self) -> Tuple[bool, str]:
        """
        Execute git push.

        Args:
            None
            
        Returns:
            A tuple (is_successful, output_message).
        """
        try:
            return self.git.push()
        except Exception as e:
            return False, str(e)