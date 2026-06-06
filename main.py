import sys
import argparse

from config.config_manager import ConfigManager
from bootstrap import build_commit_service
from cli.commit_cli import CommitCLI


def run_commit(args: argparse.Namespace) -> int:
    """The default workflow: generate, review, and create a commit."""
    cfg = ConfigManager()

    api_key = cfg.resolve_api_key()
    if not api_key:
        print("✗ No Gemini API key found.")
        print("\nFix it either way:")
        print("  • Run:  lazzycommit config   (set it in the UI)")
        print("  • Or add GEMINI_API_KEY to your .env file")
        return 1

    service = build_commit_service(cfg)

    # Override is permitted only when both the setting allows it AND the user
    # didn't pass --force. (Force means "don't prompt me", so overrides are moot.)
    allow_override = cfg.get("validation.allow_override", True) and not args.force
    cli = CommitCLI(service, should_push=args.push, allow_override=allow_override)
    return cli.run()


def run_config(args: argparse.Namespace) -> int:
    """Launch the local settings server (imports web deps lazily)."""
    try:
        from ui.server import serve
    except ImportError as exc:
        # FastAPI/uvicorn are only needed for the settings UI; give a precise hint
        # instead of a raw traceback if the optional deps aren't installed.
        print(f"✗ Settings UI dependencies missing: {exc}")
        print("  Install them with:  pip install -r requirements.txt")
        return 1
    serve(open_browser=not args.no_browser)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lazzycommit",
        description="AI-powered commit message generator with security validation.",
    )
    # Flags live on the top-level parser so the legacy `lazzycommit -p` form keeps
    # working without naming a subcommand.
    parser.add_argument("--push", "-p", action="store_true", help="Push after commit")
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Commit without validation prompts (overrides all blocks)",
    )

    sub = parser.add_subparsers(dest="command")
    config_p = sub.add_parser("config", help="Open the settings UI in your browser")
    config_p.add_argument("--no-browser", action="store_true",
                          help="Start the server without auto-opening a browser")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "config":
        return run_config(args)
    return run_commit(args)


if __name__ == "__main__":
    sys.exit(main())
