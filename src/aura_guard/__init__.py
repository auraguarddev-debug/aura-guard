"""Aura Guard — Cost governance and loop prevention for AI agents.

Quick start:
    from aura_guard import AgentGuard

    guard = AgentGuard(max_cost_per_run=0.50)
    decision = guard.check_tool("search_kb", args={"query": "refund policy"})
"""

from .config import AuraGuardConfig, CostModel, ToolAccess, ToolPolicy
from .guard import AuraGuard, GuardState
from .middleware import AgentGuard
from .async_middleware import AsyncAgentGuard
from .telemetry import (
    CompositeTelemetry,
    InMemoryTelemetry,
    LoggingTelemetry,
    SlackWebhookTelemetry,
    Telemetry,
    WebhookTelemetry,
)
from .types import CostEvent, PolicyAction, PolicyDecision, ToolCall, ToolCallSig, ToolResult

__version__ = "0.3.1"

__all__ = [
    # High-level API
    "AgentGuard",
    "AsyncAgentGuard",
    # Core engine
    "AuraGuard",
    "AuraGuardConfig",
    "GuardState",
    # Types
    "CostModel",
    "CostEvent",
    "PolicyAction",
    "PolicyDecision",
    "ToolAccess",
    "ToolPolicy",
    "ToolCall",
    "ToolCallSig",
    "ToolResult",
    # Telemetry
    "Telemetry",
    "LoggingTelemetry",
    "InMemoryTelemetry",
    "WebhookTelemetry",
    "SlackWebhookTelemetry",
    "CompositeTelemetry",
]
