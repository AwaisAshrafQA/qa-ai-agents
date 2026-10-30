"""The ten agents, in workflow order (requirements to release)."""

from qa_agents.agents.api_contract import ApiContractAgent
from qa_agents.agents.code_review import CodeReviewAgent
from qa_agents.agents.defect_drafting import DefectDraftingAgent
from qa_agents.agents.execution_reporting import ExecutionReportingAgent
from qa_agents.agents.failure_analysis import FailureAnalysisAgent
from qa_agents.agents.flaky_analysis import FlakyAnalysisAgent
from qa_agents.agents.regression_selection import RegressionSelectionAgent
from qa_agents.agents.release_quality import ReleaseQualityAgent
from qa_agents.agents.requirement_review import RequirementReviewAgent
from qa_agents.agents.test_case_generation import TestCaseGenerationAgent
from qa_agents.core.base import Agent

ALL_AGENTS: list[type[Agent]] = [
    RequirementReviewAgent,
    TestCaseGenerationAgent,
    ApiContractAgent,
    CodeReviewAgent,
    FailureAnalysisAgent,
    FlakyAnalysisAgent,
    DefectDraftingAgent,
    RegressionSelectionAgent,
    ExecutionReportingAgent,
    ReleaseQualityAgent,
]

REGISTRY: dict[str, type[Agent]] = {a.name: a for a in ALL_AGENTS}


def get_agent(name: str) -> Agent:
    return REGISTRY[name]()
