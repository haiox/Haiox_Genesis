"""
Unit tests for Haiox Genesis SandboxEngine.
Verifies command execution, timeout handling, and environment isolation.
"""

import asyncio
import sys
import pytest
from core.sandbox import SandboxEngine
from core.schemas import ExecutionStatus


@pytest.fixture
def sandbox(tmp_path):
    return SandboxEngine(base_dir=tmp_path, default_timeout=5.0)


@pytest.mark.asyncio
async def test_sandbox_successful_python_execution(sandbox, tmp_path):
    """Verify standard valid Python execution inside the sandbox."""
    code = """
import sys
print("GENESIS_SANDBOX_ACTIVE")
sys.exit(0)
"""
    result = await sandbox.execute_python_code(code, working_dir=tmp_path)

    assert result.status == ExecutionStatus.SUCCESS
    assert result.exit_code == 0
    assert "GENESIS_SANDBOX_ACTIVE" in result.stdout
    assert result.duration_ms > 0
    assert not result.timed_out


@pytest.mark.asyncio
async def test_sandbox_failure_exit_code(sandbox, tmp_path):
    """Verify execution failure traps non-zero exit codes."""
    code = """
import sys
print("ERROR_TRACE_SIMULATED", file=sys.stderr)
sys.exit(2)
"""
    result = await sandbox.execute_python_code(code, working_dir=tmp_path)

    assert result.status == ExecutionStatus.FAILED
    assert result.exit_code == 2
    assert "ERROR_TRACE_SIMULATED" in result.stderr


@pytest.mark.asyncio
async def test_sandbox_strict_timeout_interruption(sandbox, tmp_path):
    """Verify sandbox forcibly kills long-running processes exceeding timeout."""
    code = """
import time
time.sleep(10)
print("SHOULD_NEVER_REACH")
"""
    # Execute with strict 1.0 second timeout
    result = await sandbox.execute_python_code(code, working_dir=tmp_path, timeout=1.0)

    assert result.status == ExecutionStatus.TIMEOUT
    assert result.timed_out is True
    assert "Exceeded maximum allowed timeout" in result.stderr
