# Haiox Genesis — Autonomous Software Engineer & Cyber-Sandbox

> **Engine Classification:** Autonomous Agentic Software Foundry & Self-Healing Execution Sandbox  
> **Status:** v1.0.0 Production Release  
> **Test Suite:** 27/27 Tests Passing (100% Green, 44.77s)  
> **Architect:** AIrash (Staff Systems Engineer) | **Product Architect:** Hatef Ghanei (haiox)  

---

## 1. Overview & Vision
`Haiox Genesis` is the third sovereign pillar of the Haiox Ecosystem. It transforms the ecosystem from an observational and analytical system into an autonomous builder.

```text
[ 1. Haiox Smart Miner v2.0 ]  ──► (THE EYES: Zero-Token AST Web Extraction & WAF Bypass)
               │
               ▼
[ 2. Haiox Deep Research v1.0 ] ──► (THE AUDIT BRAIN: Multi-Agent Due-Diligence & Zero-Hallucination)
               │
               ▼
[ 3. Haiox Genesis v1.0.0 ] ──────► (THE BUILDER: Autonomous Multi-File Coder, Sandbox & Self-Healer)
```

---

## 2. Core Architecture & Capabilities

### Phase 1: Core Sandbox & Test Harness
1. **Isolated Execution Sandbox (`core/sandbox.py`):** Process-isolated execution with strict timeouts and resource guarding.
2. **Virtual Multi-File Workspace (`core/workspace.py`):** AST pre-flight syntax verification and multi-file tracking.
3. **Autonomous Test Harness (`core/harness.py`):** Diagnostic forensic error parsing and test execution tracking.

### Phase 2: System Architect & Scaffold Generator
4. **System Architect Agent (`agents/architect_agent.py`):** Specification and multi-file topology generator.
5. **Multi-File Scaffold Generator (`engines/scaffold_generator.py`):** Skeletal class and pytest scaffolding.
6. **Smart Dependency Resolver (`engines/dependency_resolver.py`):** Automated stdlib filtering and pinned requirements.txt.

### Phase 3: Autonomous Multi-File Coder Agent
7. **Autonomous Coder Agent (`agents/coder_agent.py`):** Functional multi-file Python synthesis with type hints and clean docstrings.
8. **Automated Test Synthesizer (`engines/test_synthesizer.py`):** Synthesizes full pytest test suites with happy-path and edge-case assertions.
9. **Cross-Module Import Resolver (`core/import_resolver.py`):** AST symbol analyzer and auto-linker for cross-module dependencies.

### Phase 4: Closed-Loop Self-Healing Engine
10. **Surgical Code Healer Agent (`agents/healer_agent.py`):** AST-verified targeted repair of syntax, attributes, zero-division, type mismatches, and logic assertions.
11. **Closed-Loop Healing Engine (`engines/healing_loop.py`):** Autonomous test-diagnose-patch-retest cycles (up to 3 retries) with zero human intervention.
12. **Unified Diff & Mutation Auditor (`core/diff_tracker.py`):** Historical record of unified code diffs and audit trail per iteration.

### Phase 5: Production Docker Packager & Provenance
13. **Hardened Docker Container Builder (`packager/docker_builder.py`):** Non-root security policies, layer-cached Dockerfile, .dockerignore, and docker-compose.
14. **Production Documentation Generator (`packager/doc_generator.py`):** Executive README synthesis with project topology and quick-start instructions.
15. **Artifact Exporter & Provenance Engine (`packager/artifact_exporter.py`):** Clean zip release packaging with cryptographic SHA-256 integrity audits.

### Phase 6: Streamlit Glass Cockpit & Master Pipeline
16. **Streamlit Glass Cockpit UI (`app.py`):** Interactive cyber-glass dashboard with multi-mode telemetry and one-click packaging.
17. **Master Orchestrator Pipeline (`engines/pipeline.py`):** Unified single-command pipeline running prompt-to-container workflows.

---

## 3. Test Verification (27/27 Tests Passing)
```bash
pytest -v
```
* `test_dependency_resolver_filters_stdlib`: PASSED
* `test_architect_spec_generation_scraper`: PASSED
* `test_architect_spec_generation_api`: PASSED
* `test_scaffold_generator_workspace_population`: PASSED
* `test_scaffold_end_to_end_in_sandbox`: PASSED
* `test_import_resolver_cross_module_resolution`: PASSED
* `test_test_synthesizer_generates_valid_pytest`: PASSED
* `test_coder_agent_synthesizes_functional_project`: PASSED
* `test_coder_agent_e2e_sandbox_execution_and_all_tests_pass`: PASSED
* `test_harness_passing_test_suite`: PASSED
* `test_harness_failing_test_diagnostic_extraction`: PASSED
* `test_diff_tracker_records_unified_diff`: PASSED
* `test_self_healing_agent_patches_syntax_error`: PASSED
* `test_self_healing_agent_patches_attribute_error`: PASSED
* `test_healing_loop_autonomous_repair_in_sandbox`: PASSED
* `test_healing_loop_max_retries_termination`: PASSED
* `test_docker_builder_generates_valid_dockerfile_and_compose`: PASSED
* `test_docker_builder_with_fastapi_entrypoint_detection`: PASSED
* `test_doc_generator_produces_production_readme`: PASSED
* `test_artifact_exporter_creates_zip_and_sha256_provenance`: PASSED
* `test_artifact_exporter_clean_archive_without_cache_files`: PASSED
* `test_sandbox_successful_python_execution`: PASSED
* `test_sandbox_failure_exit_code`: PASSED
* `test_sandbox_strict_timeout_interruption`: PASSED
* `test_workspace_valid_file_ast`: PASSED
* `test_workspace_syntax_error_trapping`: PASSED
* `test_workspace_persistence_and_loading`: PASSED

---

## 4. Quickstart

### Local Installation
```bash
git clone https://github.com/haiox/Haiox_Genesis.git
cd Haiox_Genesis
pip install -r requirements.txt
```

### Launch Glass Cockpit
```bash
streamlit run app.py
```

### Run Full Test Suite
```bash
pytest -v
```
