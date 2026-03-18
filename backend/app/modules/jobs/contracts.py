from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class JobRequest:
    job_type: str
    area: str | None = None
    case_id: int | None = None
    tenant_id: int | None = None
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobStatus:
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
