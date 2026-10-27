"""
Haiox Genesis - Diff Tracker & Code Mutation Audit Engine
Module: core/diff_tracker.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any
from .schemas import DiffEntry


class DiffTracker:
    """
    Maintains a cryptographically verifiable audit trail of all code modifications,
    generating unified diffs across self-healing iterations.
    """

    def __init__(self):
        self.history: List[DiffEntry] = []

    def record_diff(
        self,
        iteration: int,
        file_path: str,
        old_content: str,
        new_content: str
    ) -> Optional[DiffEntry]:
        """
        Calculates unified diff between old and new code versions.
        If identical, returns None. Otherwise logs entry and returns DiffEntry.
        """
        if old_content == new_content:
            return None

        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        diff_text = "\n".join(diff).strip()
        if not diff_text:
            return None

        entry = DiffEntry(
            file_path=file_path,
            iteration=iteration,
            diff_text=diff_text,
            timestamp_iso=datetime.utcnow().isoformat() + "Z"
        )
        self.history.append(entry)
        return entry

    def get_diffs_for_file(self, file_path: str) -> List[DiffEntry]:
        """Returns all historical diff entries for a given file path."""
        return [d for d in self.history if d.file_path == file_path]

    def get_diffs_for_iteration(self, iteration: int) -> List[DiffEntry]:
        """Returns all historical diff entries generated in a specific retry iteration."""
        return [d for d in self.history if d.iteration == iteration]

    def get_summary(self) -> Dict[str, Any]:
        """Provides an aggregated summary of all applied mutations."""
        touched_files = sorted(list({d.file_path for d in self.history}))
        return {
            "total_mutations": len(self.history),
            "files_touched_count": len(touched_files),
            "files_touched": touched_files,
            "has_mutations": len(self.history) > 0
        }
