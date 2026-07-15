"""Tool Registry — defines available tools for agents with schema, permissions, and risk levels."""
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    output_schema: dict | None = None
    required_permissions: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    timeout_seconds: int = 30
    retry_count: int = 0
    handler: Callable[..., Awaitable[Any]] | None = None


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self, permission_level: str | None = None) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        if permission_level:
            tools = [t for t in tools if not t.required_permissions or permission_level in t.required_permissions]
        return tools

    def get_schemas_for_llm(self, permission_level: str | None = None) -> list[dict]:
        tools = self.list_tools(permission_level)
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]


tool_registry = ToolRegistry()

# --- Register built-in tools ---

tool_registry.register(ToolDefinition(
    name="create_task",
    description="Create a new task. Use when the user mentions something that needs to be done.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title"},
            "description": {"type": "string", "description": "Task description"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
            "project_id": {"type": "string", "description": "Associated project ID"},
        },
        "required": ["title"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="update_task",
    description="Update an existing task's status, priority, or other fields.",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "title": {"type": "string"},
        },
        "required": ["task_id"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="create_project",
    description="Create a new project.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "objective": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "target_date": {"type": "string"},
        },
        "required": ["name"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="update_project",
    description="Update project status, progress, or details.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
            "status": {"type": "string"},
            "progress_percent": {"type": "integer"},
            "current_summary": {"type": "string"},
            "next_action": {"type": "string"},
            "risk_level": {"type": "string"},
        },
        "required": ["project_id"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="create_decision",
    description="Record a business decision with problem statement, options, and analysis.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "problem_statement": {"type": "string"},
            "context": {"type": "string"},
            "known_facts": {"type": "string"},
            "assumptions": {"type": "string"},
            "options": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "pros": {"type": "string"}, "cons": {"type": "string"}}}},
            "recommendation": {"type": "string"},
            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "reversibility": {"type": "string", "enum": ["reversible", "partially_reversible", "irreversible"]},
        },
        "required": ["title", "problem_statement"],
    },
    risk_level=RiskLevel.MEDIUM,
))

tool_registry.register(ToolDefinition(
    name="propose_memory",
    description="Propose a new long-term memory for the organization's knowledge base.",
    input_schema={
        "type": "object",
        "properties": {
            "memory_type": {"type": "string", "enum": [
                "founder_profile", "preference", "company_fact", "employee_fact",
                "product_fact", "supplier_fact", "project_fact", "decision",
                "lesson", "risk", "strategy", "process", "relationship",
            ]},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "importance_score": {"type": "number", "minimum": 0, "maximum": 1},
            "sensitivity_level": {"type": "string", "enum": ["normal", "confidential", "highly_confidential"]},
            "requires_confirmation": {"type": "boolean"},
        },
        "required": ["memory_type", "title", "content"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="search_memory",
    description="Search the organization's memory/knowledge base.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "memory_types": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="search_entities",
    description="Search business entities (products, employees, suppliers, etc.).",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "entity_type": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
    risk_level=RiskLevel.LOW,
))

tool_registry.register(ToolDefinition(
    name="create_notification",
    description="Create a notification for the user.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
            "action_required": {"type": "boolean"},
        },
        "required": ["title", "content"],
    },
    risk_level=RiskLevel.LOW,
))
