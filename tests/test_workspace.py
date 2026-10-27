"""
Unit tests for Haiox Genesis VirtualWorkspace.
Verifies file tracking, AST pre-flight syntax verification, and disk persistence.
"""

import pytest
from core.workspace import VirtualWorkspace


@pytest.fixture
def workspace(tmp_path):
    return VirtualWorkspace(root_dir=tmp_path)


def test_workspace_valid_file_ast(workspace):
    """Verify valid Python files are accepted without syntax errors."""
    valid_code = """
def calculate_yield(amount: float, rate: float) -> float:
    return amount * rate
"""
    valid, err = workspace.add_or_update_file("src/math_utils.py", valid_code)

    assert valid is True
    assert err is None
    assert workspace.has_syntax_errors() is False
    assert len(workspace.get_source_files()) == 1


def test_workspace_syntax_error_trapping(workspace):
    """Verify invalid Python code is caught by AST parser immediately."""
    broken_code = """
def broken_function(
    return 123
"""
    valid, err = workspace.add_or_update_file("src/broken.py", broken_code)

    assert valid is False
    assert err is not None
    assert "SyntaxError" in err
    assert workspace.has_syntax_errors() is True


def test_workspace_persistence_and_loading(workspace, tmp_path):
    """Verify files persist to disk and can be reloaded."""
    code = "VALUE = 42\n"
    workspace.add_or_update_file("config.py", code)
    persisted = workspace.persist_to_disk()

    assert len(persisted) == 1
    assert (tmp_path / "config.py").exists()
    assert (tmp_path / "config.py").read_text(encoding="utf-8") == code

    # Test fresh workspace loading
    fresh_ws = VirtualWorkspace(root_dir=tmp_path)
    count = fresh_ws.load_from_disk()

    assert count == 1
    assert fresh_ws.get_file("config.py") is not None
    assert fresh_ws.get_file("config.py").content == code
