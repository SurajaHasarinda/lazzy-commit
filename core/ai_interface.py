import google.genai as genai
from typing import Optional, List, Dict

from config.defaults import DEFAULT_PROMPT_TEMPLATE


class AIInterface:
    """
    Wraps the Google Gemini client and turns staged diffs into a commit message.

    The prompt template is now injected (was a hard-coded class constant) so users
    can tailor the model's instructions from the settings UI — e.g. enforce a
    different tone, language, or ticket-prefix convention — without editing code.
    The template must contain {files_summary} and {diffs}; that invariant is
    enforced by ConfigManager before a custom template is ever saved.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        prompt_template: Optional[str] = None,
        max_diff_chars: int = 30000,
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        # Fall back to the factory template if a caller passes nothing, so the
        # interface is still usable in isolation (tests, scripts).
        self.prompt_template = prompt_template or DEFAULT_PROMPT_TEMPLATE
        self.max_diff_chars = max_diff_chars

    def generate_commit_message(self, file_diffs: List[Dict[str, str]]) -> Optional[str]:
        """
        Generate commit message from file diffs.

        Args:
            file_diffs: List of dicts with 'file' and 'diff' keys.

        Returns:
            Generated commit message or None if failed.
        """
        try:
            files_summary = "\n".join([f"- {item['file']}" for item in file_diffs])
            diffs_text = "\n\n".join([
                f"=== {item['file']} ===\n{item['diff']}"
                for item in file_diffs
            ])

            # Truncate oversized diffs so we stay within the configured budget
            # (controls both API cost and latency).
            if len(diffs_text) > self.max_diff_chars:
                diffs_text = diffs_text[:self.max_diff_chars] + "\n\n... (truncated)"

            prompt = self.prompt_template.format(
                files_summary=files_summary,
                diffs=diffs_text
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            if response and hasattr(response, 'text') and response.text:
                message = response.text.strip()
                # Models sometimes wrap output in backticks/quotes despite the
                # prompt; strip them so the raw subject line passes validation.
                message = message.strip('`').strip('"').strip("'")
                return message

            return None
        except Exception as e:
            print(f"AI error: {e}")
            return None
