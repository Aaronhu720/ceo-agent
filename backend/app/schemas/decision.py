from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field


class DecisionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    problem_statement: str | None = None
    context: str | None = None
    known_facts: str | None = None
    assumptions: str | None = None
    options_json: dict | None = None
    project_id: UUID | None = None
    risk_level: str = "medium"
    reversibility: str = "reversible"


class DecisionUpdate(BaseModel):
    title: str | None = None
    selected_option: str | None = None
    rationale: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    decision_status: str | None = None
    review_date: date | None = None


class DecisionResponse(BaseModel):
    id: UUID
    title: str
    problem_statement: str | None
    context: str | None
    known_facts: str | None
    assumptions: str | None
    options_json: dict | None
    selected_option: str | None
    rationale: str | None
    expected_result: str | None
    actual_result: str | None
    decision_status: str
    decided_at: datetime | None
    review_date: date | None
    reversibility: str
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}
