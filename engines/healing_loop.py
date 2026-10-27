"""
Haiox Genesis - Closed-Loop Self-Healing Engine
Module: engines/healing_loop.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import logging
from typing import Optional, List

from core.schemas import HealingReport, TestRunSummary, DiagnosticTrace, CodePatch
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness
from core.diff_tracker import DiffTracker
from agents.healer_agent import SelfHealingAgent

logger = logging.getLogger("haiox.genesis.healing_loop")


class HealingLoop:
    """
    Orchestrates the closed-loop autonomous repair cycle:
    1. Executes pytest test suite in isolated sandbox.
    2. Diagnoses forensic failure tracebacks.
    3. Invokes SelfHealingAgent to apply AST-verified patches.
    4. Audits unified diffs via DiffTracker.
    5. Re-executes tests until 100% green or maximum retry ceiling reached.
    """

    def __init__(
        self,
        sandbox: SandboxEngine,
        harness: TestHarness,
        healer: Optional[SelfHealingAgent] = None,
        diff_tracker: Optional[DiffTracker] = None
    ):
        self.sandbox = sandbox
        self.harness = harness
        self.healer = healer or SelfHealingAgent()
        self.diff_tracker = diff_tracker or DiffTracker()

    async def run(
        self,
        workspace: VirtualWorkspace,
        max_retries: int = 3,
        timeout_per_test: float = 30.0
    ) -> HealingReport:
        """
        Executes the autonomous healing cycle on the provided workspace.
        Guarantees zero infinite loops with strict retry limits.
        """
        # Step 1: Initial baseline test run
        initial_summary = await self.harness.run_tests(workspace, timeout=timeout_per_test)

        if initial_summary.all_passed:
            return HealingReport(
                initial_passed=True,
                final_passed=True,
                iterations_count=0,
                max_retries=max_retries,
                diff_history=[],
                patches_applied=[],
                resolved_errors=[],
                unresolved_errors=[],
                final_summary=initial_summary
            )

        current_summary = initial_summary
        applied_patches: List[CodePatch] = []
        resolved_errors: List[str] = []

        # Step 2: Autonomous iterative healing
        for iteration in range(1, max_retries + 1):
            diagnostics = current_summary.diagnostics

            # If no parsed diagnostics but suite failed, synthesize trace from raw output
            if not diagnostics:
                diagnostics = [
                    DiagnosticTrace(
                        error_type="ExecutionError",
                        error_message="Test runner failed with non-zero exit code.",
                        traceback_raw=current_summary.raw_output[:1000]
                    )
                ]

            iteration_had_patch = False

            for diag in diagnostics:
                target_file_path = self.healer._locate_target_file(workspace, diag)
                if not target_file_path or target_file_path not in workspace.files:
                    continue

                old_file_content = workspace.files[target_file_path].content

                patch = self.healer.heal(workspace, diag, iteration=iteration)
                if patch and patch.applied_successfully:
                    applied_patches.append(patch)
                    iteration_had_patch = True

                    # Record diff in audit tracker
                    new_file_content = workspace.files[target_file_path].content
                    self.diff_tracker.record_diff(
                        iteration=iteration,
                        file_path=target_file_path,
                        old_content=old_file_content,
                        new_content=new_file_content
                    )

            if not iteration_had_patch:
                # No patches could be formulated; break to prevent idle looping
                break

            # Persist patched workspace to disk
            workspace.persist_to_disk()

            # Re-execute test suite in sandbox
            current_summary = await self.harness.run_tests(workspace, timeout=timeout_per_test)

            if current_summary.all_passed:
                # Self-healing succeeded!
                for d in initial_summary.diagnostics:
                    resolved_errors.append(f"[{d.error_type}] {d.error_message}")

                return HealingReport(
                    initial_passed=False,
                    final_passed=True,
                    iterations_count=iteration,
                    max_retries=max_retries,
                    diff_history=self.diff_tracker.history,
                    patches_applied=applied_patches,
                    resolved_errors=resolved_errors,
                    unresolved_errors=[],
                    final_summary=current_summary
                )

        # Reached max retries or dead end without full resolution
        unresolved = [f"[{d.error_type}] {d.error_message}" for d in current_summary.diagnostics]
        return HealingReport(
            initial_passed=False,
            final_passed=current_summary.all_passed,
            iterations_count=min(iteration, max_retries),
            max_retries=max_retries,
            diff_history=self.diff_tracker.history,
            patches_applied=applied_patches,
            resolved_errors=resolved_errors,
            unresolved_errors=unresolved,
            final_summary=current_summary
        )
