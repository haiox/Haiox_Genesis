"""
Haiox Genesis - Phase 5 Integration Tests: Dockerized Artifact Packager
Module: tests/test_packager.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import json
import os
import shutil
import tempfile
import zipfile
import pytest

from core.schemas import GenesisSpecification, DockerConfig
from core.workspace import VirtualWorkspace
from packager.docker_builder import DockerBuilder
from packager.doc_generator import DocumentationGenerator
from packager.artifact_exporter import ArtifactExporter


@pytest.fixture
def temp_workspace_dir():
    temp_dir = tempfile.mkdtemp(prefix="haiox_genesis_packager_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_docker_builder_generates_valid_dockerfile_and_compose(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    workspace.add_file("main.py", "def run():\n    print('Hello Haiox Genesis')\n")
    workspace.add_file("requirements.txt", "httpx==0.27.0\npydantic>=2.7.0\n")

    builder = DockerBuilder()
    dockerfile = builder.generate_dockerfile(workspace)

    assert "FROM python:3.11-slim" in dockerfile
    assert "RUN useradd -u 10001" in dockerfile
    assert "USER appuser" in dockerfile
    assert "COPY requirements.txt ." in dockerfile
    assert 'CMD ["python", "main.py"]' in dockerfile

    dockerignore = builder.generate_dockerignore()
    assert "__pycache__" in dockerignore
    assert ".pytest_cache" in dockerignore
    assert ".venv" in dockerignore

    compose = builder.generate_docker_compose("genesis_service", workspace)
    assert "version: '3.8'" in compose
    assert "haiox/genesis_service:latest" in compose

    # Test workspace population
    builder.populate_workspace(workspace)
    assert "Dockerfile" in workspace.files
    assert ".dockerignore" in workspace.files
    assert "docker-compose.yml" in workspace.files


def test_docker_builder_with_fastapi_entrypoint_detection(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    fastapi_code = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/')\n"
        "def root(): return {'status': 'active'}\n"
    )
    workspace.add_file("app.py", fastapi_code)

    builder = DockerBuilder()
    dockerfile = builder.generate_dockerfile(workspace)

    # Automatically infers uvicorn entrypoint and exposes port 8000
    assert 'uvicorn' in dockerfile
    assert 'app:app' in dockerfile
    assert 'EXPOSE 8000' in dockerfile


def test_doc_generator_produces_production_readme(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    workspace.add_file("core_engine.py", "def process(): return True\n")
    workspace.add_file("tests/test_engine.py", "def test_p(): pass\n", is_test=True)

    spec = GenesisSpecification(
        project_name="Haiox Cyber Harvester",
        objective="High-velocity zero-token web extraction pipeline",
        functional_requirements=["WAF bypass", "AST cleaning", "Session pooling"],
        dependencies=["httpx", "beautifulsoup4"]
    )

    doc_gen = DocumentationGenerator()
    readme = doc_gen.generate_readme(workspace, spec)

    assert "# Haiox Cyber Harvester" in readme
    assert "High-velocity zero-token web extraction pipeline" in readme
    assert "WAF bypass" in readme
    assert "├── core_engine.py" in readme
    assert "docker run" in readme
    assert "pytest -v" in readme

    doc_gen.populate_workspace(workspace, spec)
    assert "README.md" in workspace.files
    assert "# Haiox Cyber Harvester" in workspace.files["README.md"].content


def test_artifact_exporter_creates_zip_and_sha256_provenance(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    workspace.add_file("service.py", "print('service running')\n")
    workspace.add_file("requirements.txt", "pytest>=8.0.0\n")
    workspace.add_file("README.md", "# Test Service\n")

    exporter = ArtifactExporter()
    dist_dir = os.path.join(temp_workspace_dir, "dist_output")
    result = exporter.export_project_archive(workspace, output_dir=dist_dir, archive_name="haiox_service_v1")

    assert os.path.isfile(result.archive_path)
    assert os.path.isfile(result.manifest_path)
    assert result.total_files == 3
    assert len(result.sha256_hash) == 64  # Valid SHA-256 hex digest
    assert result.archive_bytes > 0

    # Verify that zip file is valid and readable
    with zipfile.ZipFile(result.archive_path, "r") as z:
        namelist = z.namelist()
        assert "service.py" in namelist
        assert "requirements.txt" in namelist
        assert "README.md" in namelist

    # Verify manifest JSON content
    with open(result.manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        assert manifest["sha256_hash"] == result.sha256_hash
        assert manifest["total_files"] == 3
        assert len(manifest["files"]) == 3


def test_artifact_exporter_clean_archive_without_cache_files(temp_workspace_dir):
    workspace = VirtualWorkspace(temp_workspace_dir)
    workspace.add_file("app.py", "def run(): pass\n")
    # Intentionally add cache directories
    workspace.add_file("__pycache__/app.cpython-311.pyc", "binary_bytecode_data")
    workspace.add_file(".pytest_cache/v/cache/nodeids", "cached_nodes")
    workspace.add_file(".git/config", "[core] bare = false")

    exporter = ArtifactExporter()
    result = exporter.export_project_archive(workspace, archive_name="clean_package")

    with zipfile.ZipFile(result.archive_path, "r") as z:
        namelist = z.namelist()
        assert "app.py" in namelist
        # Verify blacklisted artifacts are stripped
        for item in namelist:
            assert "__pycache__" not in item
            assert ".pytest_cache" not in item
            assert ".git" not in item
            assert not item.endswith(".pyc")
