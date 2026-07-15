"""Agent Orchestrator — manages agent dispatch, sub-agent calls, and tool execution."""
import json
from datetime import datetime, timezone
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentRun, AgentStep
from app.services.model_gateway import get_model_provider, ChatMessage
from app.tools.registry import tool_registry
from app.tools.handlers import execute_tool


@dataclass
class AgentInput:
    objective: str
    context: dict | None = None
    constraints: list[str] | None = None
    permission_level: str = "full"
    expected_output_schema: dict | None = None
    deadline: str | None = None
    parent_run_id: UUID | None = None


@dataclass
class AgentOutput:
    summary: str
    findings: list[dict] | None = None
    recommendations: list[str] | None = None
    actions: list[dict] | None = None
    risks: list[str] | None = None
    missing_information: list[str] | None = None
    confidence: float = 0.5
    source_references: list[str] | None = None
    requires_approval: bool = False


class AgentOrchestrator:
    def __init__(self, db: AsyncSession, org_id: UUID, user_id: UUID):
        self.db = db
        self.org_id = org_id
        self.user_id = user_id

    async def get_or_create_ceo_agent(self) -> Agent:
        result = await self.db.execute(
            select(Agent).where(
                Agent.organization_id == self.org_id,
                Agent.agent_type == "ceo",
                Agent.status == "active",
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            agent = Agent(
                organization_id=self.org_id,
                name="CEO Agent",
                agent_type="ceo",
                description="Your AI business partner",
                model_provider="openai",
                model_name="gpt-4o",
                temperature=0.7,
                tools_json={"tools": [t.name for t in tool_registry.list_tools()]},
                permissions_json={"level": "full"},
                memory_scope="organization",
            )
            self.db.add(agent)
            await self.db.flush()

        return agent

    async def dispatch_sub_agent(
        self,
        agent_type: str,
        agent_input: AgentInput,
    ) -> AgentOutput:
        """Dispatch a task to a specialized sub-agent."""
        result = await self.db.execute(
            select(Agent).where(
                Agent.organization_id == self.org_id,
                Agent.agent_type == agent_type,
                Agent.status == "active",
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            return AgentOutput(
                summary=f"No {agent_type} agent available",
                confidence=0.0,
            )

        run = AgentRun(
            organization_id=self.org_id,
            agent_id=agent.id,
            trigger_type="parent_agent",
            trigger_id=agent_input.parent_run_id,
            input_json={"objective": agent_input.objective, "context": agent_input.context},
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.flush()

        provider = get_model_provider(agent.model_provider)

        system_prompt = agent.system_instructions or f"You are a specialized {agent_type} agent."
        system_prompt += f"\n\nObjective: {agent_input.objective}"
        if agent_input.constraints:
            system_prompt += f"\nConstraints: {', '.join(agent_input.constraints)}"

        context_msg = ""
        if agent_input.context:
            context_msg = f"\n\nContext provided:\n{json.dumps(agent_input.context, default=str, ensure_ascii=False)}"

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"{agent_input.objective}{context_msg}"),
        ]

        try:
            response = await provider.chat(
                messages,
                model=agent.model_name,
                temperature=agent.temperature,
            )

            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.output_json = {"response": response.content}
            run.token_usage_json = {
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
            }
            await self.db.flush()

            return AgentOutput(
                summary=response.content,
                confidence=0.7,
            )

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()

            return AgentOutput(
                summary=f"Agent execution failed: {str(e)}",
                confidence=0.0,
            )

    async def execute_tool_call(
        self,
        tool_name: str,
        params: dict,
        agent_run_id: UUID,
        step_number: int,
    ) -> dict:
        """Execute a tool call and record the step."""
        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return {"error": f"Unknown tool: {tool_name}"}

        if tool_def.requires_approval:
            from app.models.approval import Approval
            approval = Approval(
                organization_id=self.org_id,
                requested_by_agent_id=None,
                requested_for_user_id=self.user_id,
                action_type=f"tool:{tool_name}",
                action_description=f"Agent wants to execute: {tool_name}",
                payload_json=params,
                risk_level=tool_def.risk_level.value,
                status="pending",
            )
            self.db.add(approval)
            await self.db.flush()
            return {"status": "approval_required", "approval_id": str(approval.id)}

        step = AgentStep(
            agent_run_id=agent_run_id,
            step_number=step_number,
            step_type="tool_call",
            tool_name=tool_name,
            input_json=params,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step)
        await self.db.flush()

        try:
            result = await execute_tool(tool_name, self.db, self.org_id, self.user_id, params)
            step.status = "completed"
            step.output_json = result
            step.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return result

        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return {"error": str(e)}
