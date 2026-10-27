"""
Haiox Genesis - Autonomous Test Harness & Traceback Parser
Module: core/harness.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
import time
from typing import List, Optional

from .schemas import DiagnosticTrace, ExecutionStatus, TestRunSummary
from .sandbox import SandboxEngine
from .workspace import VirtualWorkspace


class TestHarness:
    """
    Executes automated test suites inside the isolated sandbox,
    captures runtime diagnostics, and transforms raw failure outputs into actionable healing prompts.
    """
    __test__ = False

    def __init__(self, sandbox: SandboxEngine):
        self.sandbox = sandbox

    async def run_tests(
        self,
        workspace: VirtualWorkspace,
        test_args: Optional[List[str]] = None,
        timeout: float = 30.0
    ) -> TestRunSummary:
        """
        Persists workspace files and executes pytest in the isolated environment.
        Parses test outcomes and forensic failure traces.
        """
        # Ensure latest files are written to disk
        workspace.persist_to_disk()

        # Check for syntax errors before running pytest
        syntax_errors = [f for f in workspace.files.values() if not f.ast_valid]
        if syntax_errors:
            diagnostics = [
                DiagnosticTrace(
                    error_type="SyntaxError",
                    error_message=f.syntax_error or "Unknown syntax error",
                    failing_file=f.path,
                    traceback_raw=f"Pre-flight AST Syntax check failed for file: {f.path}"
                )
                for f in syntax_errors
            ]
            return TestRunSummary(
                total_tests=0,
                passed_tests=0,
                failed_tests=len(syntax_errors),
                error_tests=len(syntax_errors),
                duration_seconds=0.0,
                all_passed=False,
                diagnostics=diagnostics,
                raw_output="Pre-flight AST syntax check discovered syntax errors before test execution."
            )

        # Build pytest command
        default_args = ["-v", "--tb=short"]
        extra = " ".join(test_args) if test_args else " ".join(default_args)
        cmd = f'"{self.sandbox.python_executable}" -m pytest {extra}'

        start_time = time.perf_counter()
        exec_result = await self.sandbox.execute_command(
            command=cmd,
            working_dir=workspace.root_dir,
            timeout=timeout
        )
        duration = time.perf_counter() - start_time

        output = f"{exec_result.stdout}\n{exec_result.stderr}".strip()

        # Parse test results
        return self._parse_pytest_output(output, duration, exec_result.status == ExecutionStatus.SUCCESS)

    def _parse_pytest_output(self, raw_output: str, duration: float, is_success_exit: bool) -> TestRunSummary:
        """
        Extracts passed/failed counts, assertion errors, and forensic traces from pytest output.
        """
        passed = 0
        failed = 0
        errors = 0

        # Match summary line: "X passed, Y failed, Z error in ..."
        passed_match = re.search(r'(\d+)\s+passed', raw_output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r'(\d+)\s+failed', raw_output)
        if failed_match:
            failed = int(failed_match.group(1))

        error_match = re.search(r'(\d+)\s+error', raw_output)
        if error_match:
            errors = int(error_match.group(1))

        total = passed + failed + errors

        # Determine all_passed
        all_passed = is_success_exit and failed == 0 and errors == 0 and total > 0

        # Parse failure traces
        diagnostics = self._extract_failure_diagnostics(raw_output)

        # If pytest crashed or failed to collect
        if total == 0 and not is_success_exit:
            diagnostics.append(
                DiagnosticTrace(
                    error_type="CollectionOrImportError",
                    error_message="Test runner failed during module collection or import phase.",
                    traceback_raw=raw_output[:2000]
                )
            )

        return TestRunSummary(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            duration_seconds=round(duration, 3),
            all_passed=all_passed,
            diagnostics=diagnostics,
            raw_output=raw_output
        )

    def _extract_failure_diagnostics(self, output: str) -> List[DiagnosticTrace]:
        """
        Isolates individual test failure blocks and captures line numbers and error types.
        """
        diagnostics = []
        clean_output = output.replace("\r\n", "\n")

        # Find FAILURES or ERRORS sections
        failure_blocks = re.split(r'={3,}\s*(?:FAILURES|ERRORS)\s*={3,}', clean_output)
        if len(failure_blocks) > 1:
            details_section = failure_blocks[1]
            # Split before short test summary info if present
            if "=== short test summary info ===" in details_section:
                details_section = details_section.split("=== short test summary info ===")[0]

            # Split by individual test headers: "____ test_name ____"
            test_chunks = re.split(r'\n_{3,}\s*(.*?)\s*_{3,}\n', details_section)

            for i in range(1, len(test_chunks), 2):
                test_name = test_chunks[i].strip()
                trace_content = test_chunks[i + 1] if i + 1 < len(test_chunks) else ""

                # Extract error message
                err_type = "AssertionError"
                err_msg = ""
                err_match = re.search(r'(E\s+([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception):\s*(.*))', trace_content)
                if err_match:
                    err_type = err_match.group(2)
                    err_msg = err_match.group(3)
                elif "assert" in trace_content or "E   assert" in trace_content:
                    err_type = "AssertionError"
                    assert_match = re.search(r'E\s+(assert\s+.*)', trace_content)
                    if assert_match:
                        err_msg = assert_match.group(1)

                # Extract failing file and line
                file_match = re.search(r'([A-Za-z0-9_\-\\\/\.]+\.py):(\d+):', trace_content)
                failing_file = file_match.group(1) if file_match else None
                failing_line = int(file_match.group(2)) if file_match else None

                diagnostics.append(
                    DiagnosticTrace(
                        error_type=err_type,
                        error_message=err_msg or "Test failed without explicit exception message.",
                        failing_file=failing_file,
                        failing_line=failing_line,
                        traceback_raw=trace_content.strip()[:1500],
                        failed_test_name=test_name,
                        suggested_fix_context=f"Test '{test_name}' failed at {failing_file}:{failing_line}"
                    )
                )

        return diagnostics
