"""
Unit and Integration Test Suite for Haiox Genesis Phase 2.
Verifies ArchitectAgent, DependencyResolver, and ScaffoldGenerator.
"""

import pytest
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness
from agents.architect_agent import ArchitectAgent
from engines.dependency_resolver import DependencyResolver
from engines.scaffold_generator import ScaffoldGenerator


def test_dependency_resolver_filters_stdlib():
    """Verify that Python standard library modules are filtered out from requirements."""
    raw_deps = ["os", "sys", "json", "asyncio", "httpx", "pydantic", "re", "math"]
    clean_deps = DependencyResolver.filter_and_normalize(raw_deps)

    # Standard library should be stripped
    assert "os" not in clean_deps
    assert "sys" not in clean_deps
    assert "json" not in clean_deps
    assert "asyncio" not in clean_deps
    assert "re" not in clean_deps

    # Third-party PyPI packages should remain
    assert any("httpx" in d for d in clean_deps)
    assert any("pydantic" in d for d in clean_deps)
    assert any("pytest" in d for d in clean_deps)


@pytest.mark.asyncio
async def test_architect_spec_generation_scraper():
    """Verify ArchitectAgent builds a scraping-tailored multi-file topology."""
    agent = ArchitectAgent()
    spec = await agent.create_specification(
        raw_objective="Build a resilient web scraper for e-commerce tables with rate limiting",
        project_name="ecom_scraper"
    )

    assert spec.project_name == "ecom_scraper"
    assert len(spec.planned_files) >= 4
    assert any(f.path == "extractor.py" for f in spec.planned_files)
    assert any(f.is_test for f in spec.planned_files)
    assert any("beautifulsoup4" in d for d in spec.dependencies)


@pytest.mark.asyncio
async def test_architect_spec_generation_api():
    """Verify ArchitectAgent builds an API-tailored multi-file topology."""
    agent = ArchitectAgent()
    spec = await agent.create_specification(
        raw_objective="Create an asynchronous webhook receiver REST API with FastAPI",
        project_name="webhook_receiver"
    )

    assert spec.project_name == "webhook_receiver"
    assert any(f.path == "app.py" for f in spec.planned_files)
    assert any("fastapi" in d for d in spec.dependencies)


def test_scaffold_generator_workspace_population(tmp_path):
    """Verify ScaffoldGenerator populates VirtualWorkspace with 100% valid AST files."""
    agent = ArchitectAgent()
    import asyncio
    spec = asyncio.run(agent.create_specification("Build data automation processor", "data_worker"))

    workspace = VirtualWorkspace(root_dir=tmp_path)
    count, paths = ScaffoldGenerator.generate_scaffold(spec, workspace)

    assert count >= 4
    assert "requirements.txt" in paths
    assert "README.md" in paths
    assert workspace.has_syntax_errors() is False

    # Persist and check on disk
    persisted = workspace.persist_to_disk()
    assert len(persisted) == count
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "requirements.txt").exists()


@pytest.mark.asyncio
async def test_scaffold_end_to_end_in_sandbox(tmp_path):
    """Verify scaffolded project runs in isolated SandboxEngine and pytest passes."""
    agent = ArchitectAgent()
    spec = await agent.create_specification("Build simple math calculator engine", "calc_engine")

    workspace = VirtualWorkspace(root_dir=tmp_path / "workspace")
    ScaffoldGenerator.generate_scaffold(spec, workspace)

    sandbox = SandboxEngine(base_dir=tmp_path / "sandbox", default_timeout=15.0)
    harness = TestHarness(sandbox=sandbox)

    # Run tests on the generated scaffold
    summary = await harness.run_tests(workspace)

    assert summary.all_passed is True
    assert summary.passed_tests >= 1
    assert summary.failed_tests == 0
    assert len(summary.diagnostics) == 0
