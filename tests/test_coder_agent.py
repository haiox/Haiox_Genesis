"""
Unit and Integration Test Suite for Haiox Genesis Phase 3.
Verifies CoderAgent, TestSynthesizer, and ImportResolver.
"""

import ast
import pytest
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness
from core.import_resolver import ImportResolver
from core.schemas import PlannedFile
from agents.architect_agent import ArchitectAgent
from agents.coder_agent import CoderAgent
from engines.test_synthesizer import TestSynthesizer
from engines.scaffold_generator import ScaffoldGenerator


def test_import_resolver_cross_module_resolution(tmp_path):
    """Verify ImportResolver detects exported symbols and connects consumers."""
    workspace = VirtualWorkspace(root_dir=tmp_path)

    # File 1: Exports Class A
    workspace.add_or_update_file(
        "service.py",
        "class OrderService:\n    pass\n"
    )

    # File 2: Uses OrderService without importing it
    workspace.add_or_update_file(
        "consumer.py",
        "def process():\n    s = OrderService()\n    return s\n"
    )

    resolved = ImportResolver.resolve_workspace_imports(workspace)

    assert "consumer.py" in resolved
    assert any("from service import OrderService" in stmt for stmt in resolved["consumer.py"])


def test_test_synthesizer_generates_valid_pytest():
    """Verify TestSynthesizer generates syntactically valid pytest modules."""
    pfile = PlannedFile(
        path="math_ops.py",
        purpose="Mathematical operations",
        expected_classes=["Calculator"],
        expected_functions=["calculate_sum"]
    )

    test_content = TestSynthesizer.synthesize_test_file(pfile, "math_ops")

    # AST verification
    tree = ast.parse(test_content)
    assert tree is not None
    assert "def test_calculator_initialization" in test_content
    assert "def test_calculate_sum_happy_path" in test_content


@pytest.mark.asyncio
async def test_coder_agent_synthesizes_functional_project(tmp_path):
    """Verify CoderAgent creates working code and test suites with 100% valid AST."""
    architect = ArchitectAgent()
    spec = await architect.create_specification(
        "Build a high-performance token bucket rate limiter with metrics",
        "rate_limiter"
    )

    workspace = VirtualWorkspace(root_dir=tmp_path)
    # Generate scaffold first
    ScaffoldGenerator.generate_scaffold(spec, workspace)

    # Run CoderAgent
    coder = CoderAgent()
    count, paths = await coder.synthesize_project_code(spec, workspace)

    assert count >= 4
    assert workspace.has_syntax_errors() is False
    assert len(workspace.get_test_files()) >= 1
    assert len(workspace.get_source_files()) >= 2


@pytest.mark.asyncio
async def test_coder_agent_e2e_sandbox_execution_and_all_tests_pass(tmp_path):
    """
    End-to-end integration test:
    Spec -> Architect -> Scaffold -> Coder -> Sandbox -> Pytest -> 100% Green!
    """
    architect = ArchitectAgent()
    spec = await architect.create_specification(
        "Build an asynchronous telemetry collector with structured logging",
        "telemetry_collector"
    )

    workspace = VirtualWorkspace(root_dir=tmp_path / "workspace")
    ScaffoldGenerator.generate_scaffold(spec, workspace)

    coder = CoderAgent()
    await coder.synthesize_project_code(spec, workspace)

    sandbox = SandboxEngine(base_dir=tmp_path / "sandbox", default_timeout=20.0)
    harness = TestHarness(sandbox=sandbox)

    # Run tests on the synthesized code
    summary = await harness.run_tests(workspace)

    assert summary.all_passed is True
    assert summary.passed_tests >= 2
    assert summary.failed_tests == 0
    assert len(summary.diagnostics) == 0
