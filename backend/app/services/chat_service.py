"""CEO Agent Chat Service — implements the full 18-step workflow with streaming."""
import json
import time
from datetime import datetime, timezone
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.agent import AgentRun, AgentStep
from app.services.context_builder import ContextBuilder
from app.services.model_gateway import get_model_provider, ChatMessage
from app.services.memory_evaluator import evaluate_memories
from app.agents.orchestrator import AgentOrchestrator
from app.tools.registry import tool_registry
from app.tools.handlers import execute_tool
from app.services.audit_service import log_action


class ChatService:
    def __init__(self, db: AsyncSession, user: User, conversation: Conversation):
        self.db = db
        self.user = user
        self.conversation = conversation
        self.context_builder = ContextBuilder(db, user.organization_id, user.id)
        self.orchestrator = AgentOrchestrator(db, user.organization_id, user.id)

    async def stream_response(self, user_message: Message) -> AsyncIterator[dict]:
        """Full CEO Agent workflow with streaming response."""
        start_time = time.time()
        step_counter = 0

        # Step 1: Save original message (already done by caller)
        # Step 15: Create Agent Run — use conversation's agent if set, otherwise CEO agent
        if self.conversation.agent_id:
            ceo_agent = await self.orchestrator.get_agent_by_id(self.conversation.agent_id)
            if not ceo_agent:
                ceo_agent = await self.orchestrator.get_or_create_ceo_agent()
        else:
            ceo_agent = await self.orchestrator.get_or_create_ceo_agent()

        image_urls = []
        if user_message.content_json and "image_urls" in user_message.content_json:
            image_urls = user_message.content_json["image_urls"]

        agent_run = AgentRun(
            organization_id=self.user.organization_id,
            agent_id=ceo_agent.id,
            trigger_type="user_message",
            trigger_id=user_message.id,
            input_json={"message": user_message.content_text, "image_urls": image_urls},
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(agent_run)
        await self.db.flush()

        yield {"type": "message_started", "agent_run_id": str(agent_run.id)}

        # Steps 2-7: Context retrieval (intent, entities, memories, tasks, projects, decisions)
        step_counter += 1
        context_step = AgentStep(
            agent_run_id=agent_run.id,
            step_number=step_counter,
            step_type="context_retrieval",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(context_step)
        await self.db.flush()

        messages = await self.context_builder.build_context(
            self.conversation.id,
            user_message.content_text,
            image_urls=image_urls or None,
        )

        # Add tool definitions to system prompt
        tool_schemas = tool_registry.get_schemas_for_llm()
        if tool_schemas:
            tool_instruction = self._build_tool_instruction()
            messages.insert(1, ChatMessage(role="system", content=tool_instruction))

        context_step.status = "completed"
        context_step.completed_at = datetime.now(timezone.utc)
        context_step.output_json = {"context_messages": len(messages)}

        yield {"type": "memory_retrieved", "count": len(messages) - 3}

        # Step 8: Generate response (streaming)
        step_counter += 1
        gen_step = AgentStep(
            agent_run_id=agent_run.id,
            step_number=step_counter,
            step_type="generation",
            tool_name="chat_completion",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(gen_step)
        await self.db.flush()

        provider = get_model_provider(ceo_agent.model_provider)
        full_response = ""

        try:
            async for delta in provider.chat_stream(
                messages,
                model=ceo_agent.model_name,
                temperature=ceo_agent.temperature,
            ):
                full_response += delta.content
                yield {"type": "text_delta", "content": delta.content}
        except Exception as e:
            gen_step.status = "failed"
            gen_step.error_message = str(e)
            gen_step.completed_at = datetime.now(timezone.utc)
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            yield {"type": "error", "error": str(e)}
            return

        gen_step.status = "completed"
        gen_step.completed_at = datetime.now(timezone.utc)

        latency_ms = int((time.time() - start_time) * 1000)

        # Save assistant message
        assistant_msg = Message(
            conversation_id=self.conversation.id,
            sender_type="agent",
            sender_id=ceo_agent.id,
            content_text=full_response,
            message_type="text",
            model_provider=ceo_agent.model_provider,
            model_name=ceo_agent.model_name,
            latency_ms=latency_ms,
            parent_message_id=user_message.id,
        )
        self.db.add(assistant_msg)

        # Steps 9-12: Extract actionables (tasks, decisions, memories, risks)
        step_counter += 1
        extract_step = AgentStep(
            agent_run_id=agent_run.id,
            step_number=step_counter,
            step_type="extraction",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(extract_step)
        await self.db.flush()

        extracted = await self._extract_and_execute_actions(full_response, agent_run.id, step_counter)

        extract_step.status = "completed"
        extract_step.completed_at = datetime.now(timezone.utc)
        extract_step.output_json = extracted

        # Emit extraction results
        if extracted.get("tasks"):
            yield {"type": "task_proposed", "tasks": extracted["tasks"]}
        if extracted.get("memories"):
            yield {"type": "memory_proposed", "memories": extracted["memories"]}
        if extracted.get("decisions"):
            yield {"type": "decision_proposed", "decisions": extracted["decisions"]}
        if extracted.get("risks"):
            yield {"type": "risk_identified", "risks": extracted["risks"]}
        if extracted.get("tool_results"):
            yield {"type": "tool_completed", "results": extracted["tool_results"]}

        # Step 16: Update conversation summary
        self.conversation.last_message_at = datetime.now(timezone.utc)
        if not self.conversation.title or self.conversation.title == "新对话":
            self.conversation.title = user_message.content_text[:50]

        # Step 15: Complete agent run
        agent_run.status = "completed"
        agent_run.completed_at = datetime.now(timezone.utc)
        agent_run.output_json = {
            "response_length": len(full_response),
            "extracted": extracted,
            "latency_ms": latency_ms,
        }

        # Audit log
        await log_action(
            self.db,
            organization_id=self.user.organization_id,
            action="conversation.message",
            resource_type="conversation",
            resource_id=self.conversation.id,
            user_id=self.user.id,
            agent_id=ceo_agent.id,
        )

        await self.db.commit()

        # Step 17: Return completion event
        yield {
            "type": "message_completed",
            "message_id": str(assistant_msg.id),
            "agent_run_id": str(agent_run.id),
            "latency_ms": latency_ms,
        }

        # Step 18: Async memory evaluation (done inline for MVP, should be Celery task)

    async def _extract_and_execute_actions(
        self,
        response: str,
        agent_run_id,
        base_step: int,
    ) -> dict:
        """Extract tasks, decisions, memories, and risks from the response and write to DB."""
        result = {"tasks": [], "memories": [], "decisions": [], "risks": [], "tool_results": []}
        tool_step = base_step

        lines = response.split("\n")
        for line in lines:
            stripped = line.strip()

            if "[TASK]" in stripped:
                task_text = stripped.replace("[TASK]", "").strip(" :-")
                if task_text:
                    tool_step += 1
                    tool_result = await self.orchestrator.execute_tool_call(
                        "create_task",
                        {"title": task_text},
                        agent_run_id,
                        tool_step,
                    )
                    result["tasks"].append({"title": task_text, "result": tool_result})

            elif "[MEMORY]" in stripped:
                memory_text = stripped.replace("[MEMORY]", "").strip(" :-")
                if memory_text:
                    tool_step += 1
                    tool_result = await self.orchestrator.execute_tool_call(
                        "propose_memory",
                        {
                            "memory_type": "company_fact",
                            "title": memory_text[:100],
                            "content": memory_text,
                            "importance_score": 0.6,
                            "requires_confirmation": True,
                        },
                        agent_run_id,
                        tool_step,
                    )
                    result["memories"].append({"content": memory_text, "result": tool_result})

            elif "[DECISION]" in stripped:
                decision_text = stripped.replace("[DECISION]", "").strip(" :-")
                if decision_text:
                    tool_step += 1
                    tool_result = await self.orchestrator.execute_tool_call(
                        "create_decision",
                        {"title": decision_text[:200], "problem_statement": decision_text},
                        agent_run_id,
                        tool_step,
                    )
                    result["decisions"].append({"title": decision_text, "result": tool_result})

            elif "[RISK]" in stripped:
                risk_text = stripped.replace("[RISK]", "").strip(" :-")
                if risk_text:
                    result["risks"].append(risk_text)

        return result

    def _build_tool_instruction(self) -> str:
        return """## Tool Usage Instructions

When you identify actionable items in the conversation, mark them with tags:

- [TASK] followed by the task description — for things that need to be done
- [MEMORY] followed by the fact — for important facts worth remembering long-term
- [DECISION] followed by the decision — for decisions that need to be recorded
- [RISK] followed by the risk — for business risks that should be tracked

Examples:
- [TASK] Contact supplier about Q3 inventory order by next Friday
- [MEMORY] Aaron prefers to use USPS for domestic orders under 2lbs
- [DECISION] Switch from FBA to FBM for low-margin products
- [RISK] Tariff increase may affect product margins by 15%

Only use these tags when genuinely appropriate. Not every message needs them.
Keep the tags on their own line for clear parsing."""
