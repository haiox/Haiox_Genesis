"""
Unit tests for Haiox Genesis TestHarness.
Verifies test execution, result parsing, and diagnostic trace extraction.
"""

import pytest
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness


@pytest.fixture
def harness_env(tmp_path):
    sandbox = SandboxEngine(base_dir=tmp_path / "sandbox", default_timeout=15.0)
    workspace = VirtualWorkspace(root_dir=tmp_path / "workspace")
    harness = TestHarness(sandbox=sandbox)
    return harness, workspace


@pytest.mark.asyncio
async def test_harness_passing_test_suite(harness_env):
    """Verify clean green test execution and summary."""
    harness, workspace = harness_env

    # Implementation file
    impl_code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    workspace.add_or_update_file("calc.py", impl_code)

    # Test file
    test_code = """
from calc import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(10, 0) == 10
"""
    workspace.add_or_update_file("test_calc.py", test_code)

    summary = await harness.run_tests(workspace)

    assert summary.all_passed is True
    assert summary.passed_tests == 2
    assert summary.failed_tests == 0
    assert len(summary.diagnostics) == 0


@pytest.mark.asyncio
async def test_harness_failing_test_diagnostic_extraction(harness_env):
    """Verify failing tests generate structured diagnostic traces with line numbers."""
    harness, workspace = harness_env

    impl_code = """
def multiply(a: int, b: int) -> int:
    return a + b  # Bug intentionally injected
"""
    workspace.add_or_update_file("math_mod.py", impl_code)

    test_code = """
from math_mod import multiply

def test_multiply_correctness():
    assert multiply(3, 4) == 12
"""
    workspace.add_or_update_file("test_math.py", test_code)

    summary = await harness.run_tests(workspace)

    assert summary.all_passed is False
    assert summary.failed_tests == 1
    assert len(summary.diagnostics) >= 1

    diag = summary.diagnostics[0]
    assert diag.failed_test_name == "test_multiply_correctness"
    assert "AssertionError" in diag.error_type or "assert" in diag.error_message
