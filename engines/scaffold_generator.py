"""
Haiox Genesis - Multi-File Project Scaffold Generator
Module: engines/scaffold_generator.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from typing import Dict, List, Tuple

from core.schemas import GenesisSpecification, PlannedFile
from core.workspace import VirtualWorkspace
from engines.dependency_resolver import DependencyResolver


class ScaffoldGenerator:
    """
    Generates initial multi-file skeletal architectures into the VirtualWorkspace.
    Guarantees clean imports, standard type signatures, and 100% valid AST syntax.
    """

    @classmethod
    def generate_scaffold(
        cls,
        spec: GenesisSpecification,
        workspace: VirtualWorkspace
    ) -> Tuple[int, List[str]]:
        """
        Populates the VirtualWorkspace with skeletal code, test scaffolding,
        requirements.txt, and README.md.
        Returns (file_count, list_of_paths).
        """
        generated_paths = []

        # 1. Generate skeletal source and test files
        for pfile in spec.planned_files:
            content = cls._render_file_scaffold(pfile, spec)
            valid, err = workspace.add_or_update_file(
                rel_path=pfile.path,
                content=content,
                is_test=pfile.is_test
            )
            if not valid:
                raise SyntaxError(f"Scaffold generator created invalid AST syntax in {pfile.path}: {err}")
            generated_paths.append(pfile.path)

        # 2. Generate requirements.txt
        reqs_content = DependencyResolver.generate_requirements_txt(spec.dependencies)
        workspace.add_or_update_file("requirements.txt", reqs_content, is_test=False)
        generated_paths.append("requirements.txt")

        # 3. Generate README.md
        readme_content = cls._render_readme(spec)
        workspace.add_or_update_file("README.md", readme_content, is_test=False)
        generated_paths.append("README.md")

        # 4. Generate pytest.ini for seamless root imports
        pytest_ini_content = "[pytest]\npythonpath = .\n"
        workspace.add_or_update_file("pytest.ini", pytest_ini_content, is_test=False)
        generated_paths.append("pytest.ini")

        return len(generated_paths), generated_paths

    @classmethod
    def _render_file_scaffold(cls, pfile: PlannedFile, spec: GenesisSpecification) -> str:
        """
        Generates skeletal Python code with valid type hints and docstrings.
        """
        lines = [
            f'"""',
            f'Project: {spec.project_name}',
            f'Module: {pfile.path}',
            f'Purpose: {pfile.purpose}',
            f'"""',
            "",
            "from typing import Any, Dict, List, Optional",
            ""
        ]

        # Test file scaffold
        if pfile.is_test:
            lines.append("import pytest")
            lines.append("")
            if pfile.expected_functions:
                for func_name in pfile.expected_functions:
                    lines.extend([
                        f"def {func_name}():",
                        f'    """Test placeholder for {func_name}."""',
                        f"    assert True",
                        ""
                    ])
            else:
                lines.extend([
                    "def test_scaffold_initialization():",
                    '    """Verify basic scaffold initialization."""',
                    "    assert True",
                    ""
                ])
            return "\n".join(lines)

        # Implementation file scaffold
        if pfile.expected_classes:
            for cls_name in pfile.expected_classes:
                lines.extend([
                    f"class {cls_name}:",
                    f'    """{cls_name} - {pfile.purpose}"""',
                    "",
                    "    def __init__(self, **kwargs):",
                    "        self.settings = kwargs",
                    ""
                ])

        if pfile.expected_functions:
            for func_name in pfile.expected_functions:
                lines.extend([
                    f"def {func_name}(*args, **kwargs) -> Any:",
                    f'    """{func_name} placeholder."""',
                    "    return None",
                    ""
                ])

        # If neither class nor function specified
        if not pfile.expected_classes and not pfile.expected_functions:
            lines.extend([
                "# Core module configuration and initialization",
                "MODULE_NAME = __name__",
                ""
            ])

        return "\n".join(lines)

    @classmethod
    def _render_readme(cls, spec: GenesisSpecification) -> str:
        """Generates project documentation."""
        lines = [
            f"# {spec.project_name}",
            "",
            f"> **Objective:** {spec.objective}",
            "",
            "## Architecture Overview",
            f"{spec.architecture_summary}",
            "",
            "## Planned Modules",
        ]
        for f in spec.planned_files:
            tag = "[Test]" if f.is_test else "[Source]"
            lines.append(f"- `{f.path}` {tag}: {f.purpose}")

        lines.extend([
            "",
            "## Installation & Verification",
            "```bash",
            "pip install -r requirements.txt",
            "pytest -v",
            "```"
        ])
        return "\n".join(lines)
