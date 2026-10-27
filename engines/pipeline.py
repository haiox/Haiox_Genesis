"""
Haiox Genesis - Master Autonomous Orchestration Pipeline
Module: engines/pipeline.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import time
import tempfile
from pathlib import Path
from typing import Optional, Union

from core.schemas import (
    GenesisSpecification,
    GenesisRunResult,
    SniperProject,
    SniperProposalPayload
)
from core.sandbox import SandboxEngine
from core.workspace import VirtualWorkspace
from core.harness import TestHarness
from core.diff_tracker import DiffTracker
from engines.dependency_resolver import DependencyResolver
from engines.scaffold_generator import ScaffoldGenerator
from engines.healing_loop import HealingLoop
from agents.architect_agent import ArchitectAgent
from agents.coder_agent import CoderAgent
from agents.healer_agent import SelfHealingAgent
from packager.docker_builder import DockerBuilder
from packager.doc_generator import DocumentationGenerator
from packager.artifact_exporter import ArtifactExporter

try:
    from integrations.sniper_bridge import SniperBridge
    from integrations.miner_feeder import MinerFeeder
    from integrations.proposal_enricher import ProposalEnricher
    HAS_SNIPER = True
except ImportError:
    SniperBridge = None
    MinerFeeder = None
    ProposalEnricher = None
    HAS_SNIPER = False


class GenesisPipeline:
    """
    Master end-to-end orchestrator for Haiox Genesis.
    Coordinates specification parsing, multi-file synthesis, sandbox execution,
    closed-loop self-healing, containerization, and release packaging.
    """

    def __init__(self, sandbox: Optional[SandboxEngine] = None):
        self.sandbox = sandbox or SandboxEngine()
        self.harness = TestHarness(self.sandbox)
        self.dependency_resolver = DependencyResolver()
        self.architect = ArchitectAgent()
        self.coder = CoderAgent()
        self.healer = SelfHealingAgent()
        self.diff_tracker = DiffTracker()
        self.healing_loop = HealingLoop(self.sandbox, self.harness, self.healer, self.diff_tracker)
        self.docker_builder = DockerBuilder()
        self.doc_generator = DocumentationGenerator()
        self.artifact_exporter = ArtifactExporter()
        if HAS_SNIPER and SniperBridge is not None:
            self.sniper_bridge = SniperBridge()
            self.miner_feeder = MinerFeeder()
            self.proposal_enricher = ProposalEnricher()
        else:
            self.sniper_bridge = None
            self.miner_feeder = None
            self.proposal_enricher = None

    async def execute_from_spec(
        self,
        spec: GenesisSpecification,
        workspace_dir: Optional[Union[str, Path]] = None,
        max_healing_retries: int = 3
    ) -> GenesisRunResult:
        """
        Executes the complete autonomous engineering pipeline from a specification.
        """
        start_time = time.perf_counter()

        # Step 1: Initialize isolated workspace
        target_dir = Path(workspace_dir) if workspace_dir else Path(tempfile.mkdtemp(prefix="haiox_genesis_run_"))
        target_dir.mkdir(parents=True, exist_ok=True)
        workspace = VirtualWorkspace(target_dir)

        # Step 2: Scaffold multi-file structure
        ScaffoldGenerator.generate_scaffold(spec, workspace)

        # Step 3: Implement multi-file code and synthesized tests
        await self.coder.synthesize_project(spec, workspace)

        # Step 4: Inject containerization manifests
        self.docker_builder.populate_workspace(workspace, spec)

        # Step 5: Inject executive documentation
        self.doc_generator.populate_workspace(workspace, spec)

        # Step 6: Closed-Loop Self-Healing Test Execution
        healing_report = await self.healing_loop.run(
            workspace=workspace,
            max_retries=max_healing_retries,
            timeout_per_test=30.0
        )

        # Step 7: Export release artifact with cryptographic provenance
        export_result = self.artifact_exporter.export_project_archive(
            workspace=workspace,
            archive_name=f"{spec.project_name.lower()}_v1.0.0"
        )

        duration = time.perf_counter() - start_time

        return GenesisRunResult(
            project_name=spec.project_name,
            specification=spec,
            workspace_dir=str(target_dir),
            all_tests_passed=healing_report.final_passed,
            test_summary=healing_report.final_summary,
            healing_report=healing_report,
            export_result=export_result,
            proposal_payload=None,
            duration_seconds=round(duration, 2)
        )

    async def execute_sniper_project(
        self,
        project: SniperProject,
        workspace_dir: Optional[Union[str, Path]] = None
    ) -> GenesisRunResult:
        """
        Executes the complete Freelancer Sniper pipeline:
        Policy Guard -> Target Mining -> Specification -> Genesis Synthesis ->
        Pytest Verification -> Painkiller Proposal with PoC Code.
        """
        start_time = time.perf_counter()

        if not HAS_SNIPER or self.sniper_bridge is None:
            return GenesisRunResult(
                project_name=project.title,
                specification=GenesisSpecification(project_name="restricted", objective="private_module"),
                workspace_dir="",
                all_tests_passed=False,
                proposal_payload=SniperProposalPayload(
                    project_id=project.id,
                    three_sentence_proposal="[Haiox Private Core] Freelancer Sniper live bidding and target scraping are restricted to private nodes.",
                    poc_code_snippet="# Proprietary integration bridge active on internal infrastructure.",
                    is_compliant=False,
                    rejection_reason="Private enterprise module"
                ),
                duration_seconds=round(time.perf_counter() - start_time, 2)
            )

        # 1. Policy Evaluation
        approved, reason = self.sniper_bridge.evaluate_project(project)
        if not approved:
            return GenesisRunResult(
                project_name=project.title,
                specification=GenesisSpecification(project_name="rejected", objective="policy_rejection"),
                workspace_dir="",
                all_tests_passed=False,
                proposal_payload=SniperProposalPayload(
                    project_id=project.id,
                    three_sentence_proposal="",
                    poc_code_snippet="",
                    is_compliant=False,
                    rejection_reason=reason
                ),
                duration_seconds=round(time.perf_counter() - start_time, 2)
            )

        # 2. Ground-Truth Target Mining
        evidence = self.miner_feeder.inspect_target(project)

        # 3. Specification Formulation
        spec = self.sniper_bridge.transform_to_specification(project, evidence)

        # 4. Pipeline Execution
        run_result = await self.execute_from_spec(spec, workspace_dir=workspace_dir)

        # 5. Proposal Synthesis & PoC Injection
        # Load virtual workspace from directory
        ws = VirtualWorkspace(run_result.workspace_dir)
        ws.load_from_disk()

        proposal = self.proposal_enricher.enrich_and_synthesize(
            project=project,
            workspace=ws,
            export_result=run_result.export_result,
            mined_evidence=evidence
        )

        run_result.proposal_payload = proposal
        run_result.duration_seconds = round(time.perf_counter() - start_time, 2)
        return run_result
