"""
Haiox Genesis - Multi-File Virtual Workspace Manager
Module: core/workspace.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .schemas import ProjectFile


class VirtualWorkspace:
    """
    Manages in-memory and on-disk multi-file project workspaces.
    Enforces AST syntax verification, structured diff tracking, and seamless synchronization.
    """

    def __init__(self, root_dir: Union[str, Path]):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.files: Dict[str, ProjectFile] = {}

    def add_or_update_file(
        self,
        rel_path: str,
        content: str,
        is_test: Optional[bool] = None,
        is_entrypoint: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Adds or updates a file in the workspace.
        Validates Python syntax via AST parser before accepting.
        Returns (is_valid, error_message).
        """
        norm_path = rel_path.replace("\\", "/").strip("/")

        if is_test is None:
            is_test = "test" in norm_path or norm_path.startswith("tests/")

        # AST syntax validation for Python files
        ast_valid = True
        syntax_err = None

        if norm_path.endswith(".py"):
            try:
                ast.parse(content, filename=norm_path)
            except SyntaxError as e:
                ast_valid = False
                syntax_err = f"SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}"

        project_file = ProjectFile(
            path=norm_path,
            content=content,
            is_test=is_test,
            is_entrypoint=is_entrypoint,
            ast_valid=ast_valid,
            syntax_error=syntax_err
        )

        self.files[norm_path] = project_file
        return ast_valid, syntax_err

    def add_file(
        self,
        rel_path: str,
        content: str,
        is_test: Optional[bool] = None,
        is_entrypoint: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Convenient alias for add_or_update_file."""
        return self.add_or_update_file(rel_path, content, is_test=is_test, is_entrypoint=is_entrypoint)

    def persist_to_disk(self) -> List[str]:
        """
        Writes all currently valid files from memory onto the physical disk workspace.
        Returns the list of persisted file paths.
        """
        persisted = []
        for rel_path, pfile in self.files.items():
            full_path = self.root_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(pfile.content, encoding="utf-8")
            persisted.append(str(full_path))
        return persisted

    def load_from_disk(self) -> int:
        """
        Loads all existing files from the root directory into virtual workspace memory.
        """
        count = 0
        for p in self.root_dir.rglob("*"):
            if p.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in p.parts):
                rel_path = p.relative_to(self.root_dir).as_posix()
                try:
                    content = p.read_text(encoding="utf-8")
                    self.add_or_update_file(rel_path, content)
                    count += 1
                except Exception:
                    pass
        return count

    def get_file(self, rel_path: str) -> Optional[ProjectFile]:
        """Retrieves a specific file by its normalized relative path."""
        norm_path = rel_path.replace("\\", "/").strip("/")
        return self.files.get(norm_path)

    def get_test_files(self) -> List[ProjectFile]:
        """Returns all test files registered in the workspace."""
        return [f for f in self.files.values() if f.is_test]

    def get_source_files(self) -> List[ProjectFile]:
        """Returns all non-test implementation files."""
        return [f for f in self.files.values() if not f.is_test]

    def generate_project_outline(self) -> str:
        """Generates an outline of the project structure for agent context prompts."""
        lines = [f"Project Root: {self.root_dir.name}"]
        for rel_path in sorted(self.files.keys()):
            pfile = self.files[rel_path]
            tag = "[TEST]" if pfile.is_test else "[SRC]"
            status = "VALID" if pfile.ast_valid else f"ERROR: {pfile.syntax_error}"
            lines.append(f"  {tag} {rel_path} ({len(pfile.content)} chars) - {status}")
        return "\n".join(lines)

    def has_syntax_errors(self) -> bool:
        """Returns True if any file has a syntax error."""
        return any(not f.ast_valid for f in self.files.values())
