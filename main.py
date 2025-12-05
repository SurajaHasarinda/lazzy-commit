import sys
import os
import argparse

from core.git_interface import GitInterface
from core.ai_interface import AIInterface
from validators.api_key_validator import APIKeyValidator, SensitiveDataValidator
from validators.format_validator import ConventionalCommitValidator, LengthValidator, ContentValidator
from services.validation_chain import ValidationChain
from services.commit_service import CommitService
from cli.commit_cli import CommitCLI
from config import settings

def setup_validation_chain() -> ValidationChain:
    """
    Setup validation chain with all validators.
    
    Args:
        None

    Returns:
        An instance of ValidationChain with validators added.
    """
    chain = ValidationChain()

    if settings.CHECK_API_KEYS:
        chain.add_validator(APIKeyValidator())
    
    if settings.CHECK_SENSITIVE_DATA:
        chain.add_validator(SensitiveDataValidator())
    
    if settings.ENFORCE_CONVENTIONAL_COMMITS:
        chain.add_validator(ConventionalCommitValidator())
    
    if settings.ENFORCE_LENGTH_LIMIT:
        chain.add_validator(LengthValidator(max_subject_length=settings.MAX_SUBJECT_LENGTH))
    
    chain.add_validator(ContentValidator())
    return chain


def load_config() -> tuple:
    """
    Load configuration from environment.

    Args:
        None

    Returns:
        A tuple (api_key, model_name).
    """
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL
    
    if not api_key:
        print("✗ GEMINI_API_KEY not found")
        print("\nAdd to .env file:")
        print("  GEMINI_API_KEY=your_key_here")
        return None, model_name
    
    return api_key, model_name


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        None

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="AI Commit Message Generator")
    parser.add_argument('--push', '-p', action='store_true', help='Push after commit')
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Args:
        None
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()
    
    api_key, model_name = load_config()
    if not api_key:
        return 1
    
    # Dependency injection
    git = GitInterface()
    ai = AIInterface(api_key, model_name)
    chain = setup_validation_chain()
    service = CommitService(git, ai, chain)
    cli = CommitCLI(service, should_push=args.push)
    
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())