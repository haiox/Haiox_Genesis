"""
Haiox Genesis - System Architect Agent
Module: agents/architect_agent.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
from typing import Dict, List, Optional

from core.schemas import GenesisSpecification, PlannedFile
from engines.dependency_resolver import DependencyResolver


class ArchitectAgent:
    """
    Deconstructs high-level objectives into modular architectural blueprints,
    multi-file topologies, and strict test specifications.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "gemini-2.5-flash"

    async def create_specification(self, raw_objective: str, project_name: Optional[str] = None) -> GenesisSpecification:
        """
        Transforms a raw problem statement or freelance brief into a structured GenesisSpecification.
        """
        # Deterministic architectural rule-based extraction
        return self._rule_based_spec_generator(raw_objective, project_name)

    def _rule_based_spec_generator(self, objective: str, project_name: Optional[str] = None) -> GenesisSpecification:
        """
        High-precision deterministic specification generator.
        Detects domain patterns (scrapers, webhooks, bots, data pipelines, crypto)
        and constructs an AST-safe multi-file layout.
        """
        lower = objective.lower()

        # Deduce project name
        if not project_name:
            words = re.findall(r'[a-zA-Z0-9]+', lower)
            if words:
                project_name = "_".join(words[:3]) + "_app"
            else:
                project_name = "genesis_micro_service"

        # Detect domain and dependencies
        raw_deps = []
        functional_reqs = []
        planned_files = []

        # Domain: Scraping / Miner / Crawler
        if any(k in lower for k in ["scrape", "crawler", "miner", "extract", "html"]):
            raw_deps.extend(["httpx", "beautifulsoup4", "playwright"])
            functional_reqs.extend([
                "Perform resilient HTTP/async requests with retry policy",
                "Parse HTML DOM and extract structured fields",
                "Validate extracted data against Pydantic schema",
                "Ensure zero memory leak during continuous extraction"
            ])
            planned_files.extend([
                PlannedFile(
                    path="config.py",
                    purpose="Configuration and timeout settings",
                    expected_classes=["ScraperConfig"],
                    expected_functions=["get_default_headers"]
                ),
                PlannedFile(
                    path="models.py",
                    purpose="Pydantic models for extracted payloads",
                    expected_classes=["ExtractedRecord", "ScrapeResult"],
                    expected_functions=[]
                ),
                PlannedFile(
                    path="extractor.py",
                    purpose="Core extraction logic and HTML parser",
                    expected_classes=["DataExtractor"],
                    expected_functions=["parse_html_snippet", "extract_table_data"]
                ),
                PlannedFile(
                    path="tests/test_extractor.py",
                    purpose="Pytest suite for extraction logic and edge cases",
                    is_test=True,
                    expected_classes=[],
                    expected_functions=["test_parse_html_snippet", "test_empty_html_handling"]
                )
            ])

        # Domain: API / Webhook / Web Service
        elif any(k in lower for k in ["api", "webhook", "fastapi", "server", "endpoint", "rest"]):
            raw_deps.extend(["fastapi", "uvicorn", "pydantic", "httpx"])
            functional_reqs.extend([
                "Expose health-check and primary data endpoint",
                "Enforce request validation and authentication tokens",
                "Handle async payload transformations with error status codes",
                "Maintain comprehensive unit tests with TestClient"
            ])
            planned_files.extend([
                PlannedFile(
                    path="config.py",
                    purpose="Server host, port and authentication settings",
                    expected_classes=["ServerConfig"],
                    expected_functions=[]
                ),
                PlannedFile(
                    path="models.py",
                    purpose="Request and response schemas",
                    expected_classes=["WebhookPayload", "ApiResponse"],
                    expected_functions=[]
                ),
                PlannedFile(
                    path="service.py",
                    purpose="Business logic and payload processor",
                    expected_classes=["EventService"],
                    expected_functions=["process_incoming_event"]
                ),
                PlannedFile(
                    path="app.py",
                    purpose="FastAPI application router and entrypoint",
                    expected_classes=[],
                    expected_functions=["create_app", "health_check", "handle_webhook"]
                ),
                PlannedFile(
                    path="tests/test_api.py",
                    purpose="Unit and endpoint test suite",
                    is_test=True,
                    expected_classes=[],
                    expected_functions=["test_health_endpoint", "test_valid_webhook_payload"]
                )
            ])

        # Domain: Data Automation / General Logic
        else:
            raw_deps.extend(["pydantic", "httpx"])
            functional_reqs.extend([
                "Execute deterministic data transformations",
                "Ensure strict input type validation and error handling",
                "Provide CLI or module invocation interface",
                "Provide 100% green unit tests for core utilities"
            ])
            planned_files.extend([
                PlannedFile(
                    path="config.py",
                    purpose="Global module settings",
                    expected_classes=["AppConfig"],
                    expected_functions=[]
                ),
                PlannedFile(
                    path="models.py",
                    purpose="Data schemas and domain entities",
                    expected_classes=["DataEntity", "ProcessingSummary"],
                    expected_functions=[]
                ),
                PlannedFile(
                    path="core_engine.py",
                    purpose="Primary operational algorithm and processor",
                    expected_classes=["CoreEngine"],
                    expected_functions=["execute_task", "validate_input"]
                ),
                PlannedFile(
                    path="tests/test_engine.py",
                    purpose="Unit test coverage for core algorithm",
                    is_test=True,
                    expected_classes=[],
                    expected_functions=["test_execute_task_success", "test_invalid_input_rejection"]
                )
            ])

        clean_deps = DependencyResolver.filter_and_normalize(raw_deps)

        arch_summary = (
            f"Multi-file architecture for '{project_name}' implementing {len(planned_files)} modules "
            f"with strict AST syntax validation, decoupled schemas, and comprehensive pytest coverage."
        )

        return GenesisSpecification(
            project_name=project_name,
            objective=objective,
            architecture_summary=arch_summary,
            functional_requirements=functional_reqs,
            planned_files=planned_files,
            dependencies=clean_deps,
            target_technologies=["python", "pytest"]
        )
