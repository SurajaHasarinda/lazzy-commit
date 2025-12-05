from typing import Optional
from services.commit_service import CommitService


class CommitCLI:
    
    def __init__(self, commit_service: CommitService, should_push: bool = False):
        self.commit_service = commit_service
        self.should_push = should_push
    
    def run(self) -> int:
        """
        Run the CLI workflow.

        Args:
            None
            
        Returns:
            Exit code (0 for success, 1 for failure).
        """
        try:
            # Collect changes
            print("🔍 Analyzing...")
            success, file_diffs, errors = self.commit_service.collect_changes()
            
            if not success:
                print(f"✗ {errors[0]}" if errors else "✗ Failed")
                if len(errors) > 1:
                    for error in errors[1:]:
                        print(error)
                return 1
            
            print(f"✓ {len(file_diffs)} file(s)")
            
            # Generate message
            print("🤖 Generating...")
            success, message, errors = self.commit_service.generate_commit_message(file_diffs)

            if not success:
                print("✗ Validation failed:")
                for error in errors:
                    print(error)
                return 1

            # Ensure message is not None at this point
            if not message:
                print("✗ No message generated")
                return 1

            # Display
            print("\n" + "─" * 50)
            print(message)
            print("─" * 50 + "\n")

            # Confirm
            action = self._get_confirmation()

            if action == 'yes':
                return self._execute_commit(message)
            elif action == 'edit':
                edited = self._edit_message(message)
                return self._execute_commit(edited) if edited else 1
            else:
                print("✗ Cancelled")
                return 1
                
        except KeyboardInterrupt:
            print("\n✗ Cancelled")
            return 1
        except Exception as e:
            print(f"✗ Error: {e}")
            return 1
    
    def _get_confirmation(self) -> str:
        """
        Get user confirmation.
        
        Args:
            None

        Returns:
            'yes', 'no', or 'edit'
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
        Allow user to edit the commit message.
        
        Args:
            original (str): The original commit message.

        Returns:
            Optional[str]: The edited commit message or None if no changes were made.
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
    
    def _execute_commit(self, message: str) -> int:
        """
        Execute the commit and optional push.

        Args:
            message (str): The commit message.
            
        Returns:
            int: Exit code (0 for success, 1 for failure).
        """
        print("💾 Committing...")
        success, _ = self.commit_service.execute_commit(message)
        
        if not success:
            print("✗ Commit failed")
            return 1
        
        print("✓ Committed")
        
        if self.should_push:
            print("🚀 Pushing...")
            success, _ = self.commit_service.execute_push()
            print("✓ Pushed" if success else "✗ Push failed")
            return 0 if success else 1
        
        return 0