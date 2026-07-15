from dataclasses import dataclass


@dataclass
class MemoryEvaluation:
    should_store: bool
    memory_type: str
    proposed_title: str
    proposed_content: str
    importance_score: float
    confidence_score: float
    sensitivity_level: str
    valid_until: str | None
    requires_confirmation: bool
    related_entities: list[dict]


MEMORY_EVAL_PROMPT = """Analyze the following conversation and determine if any long-term memories should be extracted.

Evaluate each potential memory on these criteria:
1. Long-term value (will this matter in 30+ days?)
2. Importance to business decisions
3. Whether it's a stable fact vs. temporary context
4. Whether it relates to a business entity (product, employee, supplier, etc.)
5. Whether it represents a preference or lesson learned
6. Sensitivity level (normal, confidential, highly_confidential)
7. Whether it might expire
8. Whether it needs user confirmation

Memory types:
- founder_profile: Personal preferences, work style, decision-making patterns
- preference: Business preferences (suppliers, tools, processes)
- company_fact: Company info, legal, structural facts
- employee_fact: Employee info, skills, roles
- product_fact: Product details, specifications, performance
- supplier_fact: Supplier info, reliability, pricing
- project_fact: Project context, goals, constraints
- decision: Important business decisions and their rationale
- lesson: Lessons learned from successes and failures
- risk: Identified business risks
- strategy: Strategic direction and goals
- process: Business processes and procedures
- relationship: Business relationships
- temporary_context: Short-term context that will expire

For each memory worth storing, output a JSON object with:
{
  "should_store": true,
  "memory_type": "...",
  "proposed_title": "...",
  "proposed_content": "...",
  "importance_score": 0.0-1.0,
  "confidence_score": 0.0-1.0,
  "sensitivity_level": "normal|confidential|highly_confidential",
  "valid_until": null or "YYYY-MM-DD",
  "requires_confirmation": true/false,
  "related_entities": [{"type": "...", "name": "..."}]
}

Rules:
- Do NOT store casual conversation or greetings
- Do NOT store information that is obviously temporary
- Low-risk company facts can be auto-stored (requires_confirmation: false)
- Employee evaluations, financial data, sensitive info MUST require confirmation
- importance_score > 0.7 = high importance
- confidence_score reflects how certain you are about the extracted fact

Conversation:
{conversation}

User's latest message:
{message}

Output as a JSON array of memories to extract (empty array if none):
"""


async def evaluate_memories(
    conversation_history: str,
    latest_message: str,
    model_provider=None,
) -> list[MemoryEvaluation]:
    if model_provider is None:
        from app.services.model_gateway import get_model_provider, ChatMessage
        model_provider = get_model_provider()

    from app.services.model_gateway import ChatMessage

    prompt = MEMORY_EVAL_PROMPT.format(
        conversation=conversation_history,
        message=latest_message,
    )

    response = await model_provider.chat(
        [ChatMessage(role="user", content=prompt)],
        temperature=0.3,
    )

    import json
    try:
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        memories_data = json.loads(text)
        if not isinstance(memories_data, list):
            memories_data = [memories_data]

        return [
            MemoryEvaluation(**m)
            for m in memories_data
            if m.get("should_store", False)
        ]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []
