from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.modules.jobs.contracts import JobRequest, JobStatus


class JobService:
    def enqueue(self, request: JobRequest) -> JobStatus:
        now = datetime.now(timezone.utc)
        return JobStatus(
            job_id=str(uuid4()),
            job_type=request.job_type,
            status="queued",
            created_at=now,
            updated_at=now,
            result={
                "area": request.area,
                "case_id": request.case_id,
                "scaffold": True,
            },
        )
