import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class HistoryService:
    def __init__(self, history_path: Path, enabled: bool = True):
        self.history_path = history_path
        self.enabled = enabled

    def record(
        self,
        message: str,
        outcome: str,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        file_count: int = 0,
        overridden: bool = False,
    ) -> None:
        """
        Append one commit event.

        Args:
            message: The final commit message acted upon.
            outcome: "committed", "edited", "cancelled", or "pushed".
            repo / branch: context for per-repo / per-branch stats.
            file_count: number of staged files in this run.
            overridden: whether the user bypassed a validation/security block.

        Failures here are swallowed: history is a convenience, and a logging
        error must never break the actual commit the user came to make.
        """
        if not self.enabled:
            return
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": self._extract_type(message),
            "subject": message.split("\n")[0][:200],
            "outcome": outcome,
            "repo": repo,
            "branch": branch,
            "file_count": file_count,
            "overridden": overridden,
        }
        try:
            with self.history_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def load(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read history newest-first.

        Args:
            limit: cap the number of returned records (the UI paginates).

        Malformed lines are skipped rather than aborting the whole read, so one
        bad write can't hide the entire history.
        """
        if not self.history_path.exists():
            return []
        records: List[Dict[str, Any]] = []
        try:
            with self.history_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []

        records.reverse()  # newest first for display
        return records[:limit] if limit else records

    def stats(self) -> Dict[str, Any]:
        """
        Aggregate history into the numbers the dashboard shows.

        Returns counts by type, by outcome, the acceptance rate, and recent
        activity — computed on read so there's no separate aggregate to keep in
        sync with the raw log.
        """
        records = self.load()
        total = len(records)

        by_type: Dict[str, int] = {}
        by_outcome: Dict[str, int] = {}
        overrides = 0
        for r in records:
            by_type[r.get("type", "other")] = by_type.get(r.get("type", "other"), 0) + 1
            by_outcome[r.get("outcome", "unknown")] = by_outcome.get(r.get("outcome", "unknown"), 0) + 1
            if r.get("overridden"):
                overrides += 1

        # Acceptance = anything that resulted in a real commit (committed/edited/pushed)
        # over the total number of generations.
        accepted = sum(by_outcome.get(o, 0) for o in ("committed", "edited", "pushed"))
        acceptance_rate = round((accepted / total) * 100, 1) if total else 0.0

        return {
            "total": total,
            "by_type": by_type,
            "by_outcome": by_outcome,
            "acceptance_rate": acceptance_rate,
            "overrides": overrides,
            "recent": records[:10],
        }

    def clear(self) -> None:
        """Delete the history file (exposed as a 'Clear history' action in the UI)."""
        try:
            self.history_path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _extract_type(message: str) -> str:
        """
        Pull the conventional-commit type ('feat', 'fix', ...) from the subject.

        Used purely for the type-distribution chart; returns 'other' when the
        subject isn't conventional (e.g. an overridden free-form message).
        """
        first = message.split("\n")[0].strip()
        if ":" in first:
            head = first.split(":", 1)[0]
            # Strip an optional (scope) and a trailing ! breaking-change marker.
            head = head.split("(")[0].rstrip("!").strip().lower()
            if head:
                return head
        return "other"
