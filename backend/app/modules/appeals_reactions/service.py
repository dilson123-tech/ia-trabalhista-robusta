from __future__ import annotations

from app.modules.appeals_reactions.contracts import (
    AppealDeadline,
    AppealDraftRef,
    AppealReactionState,
    AppealStrategyItem,
    JudicialDecision,
)


class AppealsReactionsService:
    def build_state_from_decision(
        self,
        decision: JudicialDecision,
    ) -> AppealReactionState:
        return AppealReactionState(
            area=decision.area,
            case_id=decision.case_id,
            tenant_id=decision.tenant_id,
            source_decision=decision,
            metadata={
                "source": "appeals_reactions_service",
                "decision_type": decision.decision_type,
                "unfavorable_points_count": len(decision.unfavorable_points),
            },
        )

    def add_deadline(
        self,
        state: AppealReactionState,
        deadline: AppealDeadline,
    ) -> AppealReactionState:
        self._ensure_deadline_key_is_unique(state, deadline.key)
        state.deadlines.append(deadline)
        return state

    def add_strategy_item(
        self,
        state: AppealReactionState,
        strategy_item: AppealStrategyItem,
    ) -> AppealReactionState:
        decision = self._require_source_decision(state)
        point_keys = {point.key for point in decision.unfavorable_points}

        for point_key in strategy_item.target_point_keys:
            if point_key not in point_keys:
                raise ValueError(
                    f"Decision point with key '{point_key}' was not found"
                )

        self._ensure_strategy_key_is_unique(state, strategy_item.key)
        state.strategy_items.append(strategy_item)
        return state

    def add_appeal_draft(
        self,
        state: AppealReactionState,
        draft_ref: AppealDraftRef,
    ) -> AppealReactionState:
        state.appeal_drafts.append(draft_ref)
        return state

    def summarize_reaction(self, state: AppealReactionState) -> dict[str, object]:
        decision = self._require_source_decision(state)

        return {
            "area": state.area,
            "case_id": state.case_id,
            "tenant_id": state.tenant_id,
            "decision_type": decision.decision_type,
            "decision_title": decision.title,
            "unfavorable_points": [
                {
                    "key": point.key,
                    "title": point.title,
                    "outcome": point.outcome,
                }
                for point in decision.unfavorable_points
            ],
            "deadlines": [
                {
                    "key": deadline.key,
                    "title": deadline.title,
                    "due_date": deadline.due_date,
                    "status": deadline.status,
                }
                for deadline in state.deadlines
            ],
            "strategy_items": [
                {
                    "key": item.key,
                    "title": item.title,
                    "priority": item.priority,
                    "target_point_keys": item.target_point_keys,
                }
                for item in state.strategy_items
            ],
            "appeal_drafts": [
                {
                    "document_type": draft.document_type,
                    "title": draft.title,
                    "status": draft.status,
                    "version": draft.version,
                }
                for draft in state.appeal_drafts
            ],
        }

    def _require_source_decision(
        self,
        state: AppealReactionState,
    ) -> JudicialDecision:
        if state.source_decision is None:
            raise ValueError("Appeal reaction state does not have a source decision")
        return state.source_decision

    def _ensure_deadline_key_is_unique(
        self,
        state: AppealReactionState,
        deadline_key: str,
    ) -> None:
        for deadline in state.deadlines:
            if deadline.key == deadline_key:
                raise ValueError(f"Deadline with key '{deadline_key}' already exists")

    def _ensure_strategy_key_is_unique(
        self,
        state: AppealReactionState,
        strategy_key: str,
    ) -> None:
        for item in state.strategy_items:
            if item.key == strategy_key:
                raise ValueError(
                    f"Strategy item with key '{strategy_key}' already exists"
                )
