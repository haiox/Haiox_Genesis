"""
Haiox Genesis - Phase 4 Integration Tests: Self-Healing Agent & Closed-Loop Engine
Module: tests/test_healer_agent.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import pytest
import os
import shutil
import tempfile

from core.schemas import DiagnosticTrace
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness
from core.diff_tracker import DiffTracker
from agents.healer_agent import SelfHealingAgent
from engines.healing_loop import HealingLoop


@pytest.fixture
def temp_workspace_dir():
    temp_dir = tempfile.mkdtemp(prefix="haiox_genesis_heal_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sandbox():
    return SandboxEngine()


def test_diff_tracker_records_unified_diff():
    tracker = DiffTracker()
    old_code = "def calc(a, b):\n    return a - b\n"
    new_code = "def calc(a, b):\n    return a + b\n"

    diff = tracker.record_diff(
        iteration=1,
        file_path="math_mod.py",
        old_content=old_code,
        new_content=new_code
    )

    assert diff is not None
    assert diff.file_path == "math_mod.py"
    assert diff.iteration == 1
    assert "--- a/math_mod.py" in diff.diff_text
    assert "+++ b/math_mod.py" in diff.diff_text
    assert "-    return a - b" in diff.diff_text
    assert "+    return a + b" in diff.diff_text

    summary = tracker.get_summary()
    assert summary["total_mutations"] == 1
    assert summary["files_touched_count"] == 1
    assert "math_mod.py" in summary["files_touched"]

    # Identical code should not register a diff
    noop_diff = tracker.record_diff(
        iteration=2,
        file_path="math_mod.py",
        old_content=new_code,
        new_content=new_code
    )
    assert noop_diff is None
    assert tracker.get_summary()["total_mutations"] == 1


def test_self_healing_agent_patches_syntax_error(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    broken_code = "def calculate(a, b)\n    return a + b\n"
    workspace.add_file("calc.py", broken_code)

    assert workspace.files["calc.py"].ast_valid is False

    diag = DiagnosticTrace(
        error_type="SyntaxError",
        error_message="expected ':'",
        failing_file="calc.py",
        failing_line=1,
        traceback_raw="SyntaxError: expected ':' at line 1"
    )

    healer = SelfHealingAgent()
    patch = healer.heal(workspace, diag)

    assert patch is not None
    assert patch.applied_successfully is True
    assert workspace.files["calc.py"].ast_valid is True
    assert "def calculate(a, b):" in workspace.files["calc.py"].content


def test_self_healing_agent_patches_attribute_error(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    service_code = (
        "class OrderService:\n"
        "    def __init__(self):\n"
        "        self.orders = []\n"
    )
    workspace.add_file("order_service.py", service_code)

    diag = DiagnosticTrace(
        error_type="AttributeError",
        error_message="'OrderService' object has no attribute 'get_active_orders'",
        failing_file="order_service.py",
        traceback_raw="AttributeError: 'OrderService' object has no attribute 'get_active_orders'"
    )

    healer = SelfHealingAgent()
    patch = healer.heal(workspace, diag)

    assert patch is not None
    assert patch.applied_successfully is True
    assert "def get_active_orders" in workspace.files["order_service.py"].content
    assert workspace.files["order_service.py"].ast_valid is True


@pytest.mark.asyncio
async def test_healing_loop_autonomous_repair_in_sandbox(temp_workspace_dir, sandbox):
    workspace = VirtualWorkspace(temp_workspace_dir)

    # Inverted logic: add function subtracts instead of adds!
    buggy_math = (
        "def add(a: int, b: int) -> int:\n"
        "    \"\"\"Adds two numbers.\"\"\"\n"
        "    return a - b\n\n"
        "def multiply(a: int, b: int) -> int:\n"
        "    \"\"\"Multiplies two numbers.\"\"\"\n"
        "    return a * b\n"
    )
    workspace.add_file("core_math.py", buggy_math)

    test_math = (
        "import pytest\n"
        "from core_math import add, multiply\n\n"
        "def test_addition():\n"
        "    assert add(10, 5) == 15\n\n"
        "def test_multiplication():\n"
        "    assert multiply(3, 4) == 12\n"
    )
    workspace.add_file("tests/test_math.py", test_math, is_test=True)
    workspace.add_file("pytest.ini", "[pytest]\npythonpath = .\n")

    harness = TestHarness(sandbox)
    diff_tracker = DiffTracker()
    healer = SelfHealingAgent()
    loop = HealingLoop(sandbox, harness, healer, diff_tracker)

    # Execute autonomous healing loop
    report = await loop.run(workspace, max_retries=3, timeout_per_test=20.0)

    # Assertions on healing loop results
    assert report.initial_passed is False, "Initial run should fail due to intentional logic bug"
    assert report.final_passed is True, "Autonomous healing loop must resolve the defect to 100% green"
    assert report.iterations_count >= 1
    assert len(report.diff_history) >= 1
    assert "core_math.py" in [p.file_path for p in report.patches_applied]

    # Verify that the logic in core_math was corrected
    repaired_content = workspace.files["core_math.py"].content
    assert "return a + b" in repaired_content


@pytest.mark.asyncio
async def test_healing_loop_max_retries_termination(temp_workspace_dir, sandbox):
    workspace = VirtualWorkspace(temp_workspace_dir)

    # Unfixable assertion with empty non-python file
    unfixable_code = (
        "def impossible_fn():\n"
        "    # Intentionally impossible condition\n"
        "    return 42\n"
    )
    workspace.add_file("impossible.py", unfixable_code)

    test_code = (
        "from impossible import impossible_fn\n"
        "def test_unreachable():\n"
        "    assert impossible_fn() == 999999\n"
    )
    workspace.add_file("tests/test_impossible.py", test_code, is_test=True)
    workspace.add_file("pytest.ini", "[pytest]\npythonpath = .\n")

    harness = TestHarness(sandbox)
    diff_tracker = DiffTracker()
    healer = SelfHealingAgent()
    loop = HealingLoop(sandbox, harness, healer, diff_tracker)

    # Set strict max_retries to 2
    report = await loop.run(workspace, max_retries=2, timeout_per_test=15.0)

    # Must terminate without hanging
    assert report.final_passed in [True, False]
    assert report.iterations_count <= 2
