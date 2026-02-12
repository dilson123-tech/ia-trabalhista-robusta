from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.case_analysis import CaseAnalysis


def list_case_analyses(
    db: Session,
    case_id: int,
    limit: Optional[int] = 20,
) -> List[CaseAnalysis]:
    """
    Retorna o histórico de análises de um caso específico,
    mais recentes primeiro.

    - case_id: ID do caso (Case.id)
    - limit: máximo de registros (None = sem limite)
    """
    query = (
        db.query(CaseAnalysis)
        .filter(CaseAnalysis.case_id == case_id)
        .order_by(CaseAnalysis.created_at.desc())
    )

    if limit:
        query = query.limit(limit)

    return query.all()
