"""
Haiox Genesis - Core Schemas & Type Contracts
Module: core/schemas.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SYNTAX_ERROR = "syntax_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    timed_out: bool = False
    command: Optional[str] = None


@dataclass
class DiagnosticTrace:
    error_type: str
    error_message: str
    failing_file: Optional[str] = None
    failing_line: Optional[int] = None
    traceback_raw: str = ""
    failed_test_name: Optional[str] = None
    suggested_fix_context: str = ""


@dataclass
class ProjectFile:
    path: str
    content: str
    is_test: bool = False
    is_entrypoint: bool = False
    ast_valid: bool = True
    syntax_error: Optional[str] = None


@dataclass
class TestRunSummary:
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    duration_seconds: float
    all_passed: bool
    diagnostics: List[DiagnosticTrace] = field(default_factory=list)
    raw_output: str = ""


@dataclass
class PlannedFile:
    path: str
    purpose: str
    is_test: bool = False
    expected_classes: List[str] = field(default_factory=list)
    expected_functions: List[str] = field(default_factory=list)


@dataclass
class GenesisSpecification:
    project_name: str
    objective: str
    architecture_summary: str = ""
    functional_requirements: List[str] = field(default_factory=list)
    planned_files: List[PlannedFile] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    target_technologies: List[str] = field(default_factory=lambda: ["python", "pytest"])
    constraints: List[str] = field(default_factory=list)
    max_self_healing_attempts: int = 3


@dataclass
class CodePatch:
    file_path: str
    original_snippet: str
    patched_snippet: str
    rationale: str
    line_number: Optional[int] = None
    applied_successfully: bool = True


@dataclass
class DiffEntry:
    file_path: str
    iteration: int
    diff_text: str
    timestamp_iso: str


@dataclass
class HealingReport:
    initial_passed: bool
    final_passed: bool
    iterations_count: int
    max_retries: int
    diff_history: List[DiffEntry] = field(default_factory=list)
    patches_applied: List[CodePatch] = field(default_factory=list)
    resolved_errors: List[str] = field(default_factory=list)
    unresolved_errors: List[str] = field(default_factory=list)
    final_summary: Optional[TestRunSummary] = None


@dataclass
class DockerConfig:
    python_version: str = "3.11-slim"
    entrypoint_file: Optional[str] = None
    exposed_ports: List[int] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    app_user: str = "appuser"


@dataclass
class ExportArtifactResult:
    archive_path: str
    manifest_path: str
    sha256_hash: str
    total_files: int
    total_uncompressed_bytes: int
    archive_bytes: int
    timestamp_iso: str


@dataclass
class GenesisRunResult:
    project_name: str
    specification: GenesisSpecification
    workspace_dir: str
    all_tests_passed: bool
    test_summary: Optional[TestRunSummary] = None
    healing_report: Optional[HealingReport] = None
    export_result: Optional[ExportArtifactResult] = None
    duration_seconds: float = 0.0




