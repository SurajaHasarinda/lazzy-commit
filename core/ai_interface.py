import google.generativeai as genai
from typing import Optional, List, Dict


class AIInterface:

    # Prompt template for commit message generation 
    GENERATION_PROMPT = """
        Analyze the following git changes and generate ONE professional commit message following the Conventional Commits format.

        Conventional Commits format: <type>: <description>

        Types: feat, fix, docs, style, refactor, test, build, ci, modify
        Description: imperative mood, lowercase, no period at end

        IMPORTANT: Keep the first line under 72 characters.

        Choose the MOST SIGNIFICANT change as the primary type.

        Files changed:
        {files_summary}

        Git diffs:
        {diffs}

        Provide ONLY the commit message, nothing else. No explanation, no markdown, no quotes.
        Example: feat: add JWT authentication system
        """
    
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
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
            
            # Truncate if too long
            if len(diffs_text) > 30000:
                diffs_text = diffs_text[:30000] + "\n\n... (truncated)"
            
            prompt = self.GENERATION_PROMPT.format(
                files_summary=files_summary,
                diffs=diffs_text
            )
            
            response = self.model.generate_content(prompt)
            
            if response and hasattr(response, 'text') and response.text:
                message = response.text.strip()
                message = message.strip('`').strip('"').strip("'")
                return message
            
            return None
        except Exception as e:
            print(f"AI error: {e}")
            return None