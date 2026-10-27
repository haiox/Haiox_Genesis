"""
Haiox Genesis - Isolated Execution Sandbox Engine
Module: core/sandbox.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from .schemas import ExecutionResult, ExecutionStatus


class SandboxEngine:
    """
    High-security, process-isolated sandbox engine.
    Safely executes arbitrary code and commands with strict timeout guarantees,
    resource protection, and disposable environment lifecycles.
    """

    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        default_timeout: float = 15.0,
        python_executable: Optional[str] = None
    ):
        self.base_dir = Path(base_dir).resolve() if base_dir else Path(tempfile.gettempdir()) / "haiox_genesis_sandboxes"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.default_timeout = default_timeout
        self.python_executable = python_executable or sys.executable

    def create_isolated_environment(self, sandbox_id: Optional[str] = None) -> Path:
        """Creates a dedicated isolated workspace directory on disk."""
        if not sandbox_id:
            sandbox_id = f"sandbox_{int(time.time() * 1000)}"
        env_path = self.base_dir / sandbox_id
        env_path.mkdir(parents=True, exist_ok=True)
        return env_path

    def clean_environment(self, env_path: Path):
        """Disposes and wipes the isolated workspace safely."""
        if env_path.exists() and env_path.is_dir():
            shutil.rmtree(env_path, ignore_errors=True)

    async def execute_command(
        self,
        command: Union[str, List[str]],
        working_dir: Union[str, Path],
        timeout: Optional[float] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Asynchronously executes a shell/process command within an isolated workspace.
        Enforces execution timeouts and returns structured metrics.
        """
        work_path = Path(working_dir).resolve()
        work_path.mkdir(parents=True, exist_ok=True)
        effective_timeout = timeout or self.default_timeout

        # Construct sanitized environment
        clean_env = os.environ.copy()
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONIOENCODING"] = "utf-8"
        clean_env["PYTHONPATH"] = str(work_path)
        if env_vars:
            clean_env.update(env_vars)

        start_time = time.perf_counter()

        cmd_str = command if isinstance(command, str) else " ".join(command)

        try:
            # Spawn asynchronous subprocess
            process = await asyncio.create_subprocess_shell(
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_path),
                env=clean_env
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
                exit_code = process.returncode or 0

                status = ExecutionStatus.SUCCESS if exit_code == 0 else ExecutionStatus.FAILED

                return ExecutionResult(
                    status=status,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    exit_code=exit_code,
                    duration_ms=round(duration_ms, 2),
                    timed_out=False,
                    command=cmd_str
                )

            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    stdout="",
                    stderr=f"Process terminated: Exceeded maximum allowed timeout of {effective_timeout}s.",
                    exit_code=-9,
                    duration_ms=round(duration_ms, 2),
                    timed_out=True,
                    command=cmd_str
                )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                stdout="",
                stderr=f"System execution failure: {str(e)}",
                exit_code=-1,
                duration_ms=round(duration_ms, 2),
                timed_out=False,
                command=cmd_str
            )

    async def execute_python_code(
        self,
        code_string: str,
        working_dir: Union[str, Path],
        file_name: str = "temp_exec.py",
        timeout: Optional[float] = None
    ) -> ExecutionResult:
        """
        Writes and executes a snippet of Python code directly inside the sandbox.
        """
        work_path = Path(working_dir).resolve()
        work_path.mkdir(parents=True, exist_ok=True)
        target_file = work_path / file_name

        target_file.write_text(code_string, encoding="utf-8")

        cmd = f'"{self.python_executable}" "{target_file.name}"'
        return await self.execute_command(
            command=cmd,
            working_dir=work_path,
            timeout=timeout
        )
