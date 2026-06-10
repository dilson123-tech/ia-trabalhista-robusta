from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CaseOperationalAssistantRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=6000)
    mode: str = "orientation"


class CaseOperationalAssistantSuggestion(BaseModel):
    destination: str
    label: str
    suggested_text: str
    reason: str
    priority: str = "normal"


class CaseOperationalAssistantResponse(BaseModel):
    case_id: int
    assistant_mode: str = "orientation_only"
    summary: str
    rewritten_input: str
    suggested_actions: list[CaseOperationalAssistantSuggestion] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str
    metadata: dict[str, Any] = Field(default_factory=dict)
