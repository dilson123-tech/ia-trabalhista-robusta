from __future__ import annotations

from datetime import date

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

        unfavorable_points = [
            {
                "key": point.key,
                "title": point.title,
                "description": point.description,
                "outcome": point.outcome,
                "legal_effect": point.legal_effect,
            }
            for point in decision.unfavorable_points
        ]
        deadlines = [
            {
                "key": deadline.key,
                "title": deadline.title,
                "due_date": deadline.due_date,
                "status": deadline.status,
            }
            for deadline in state.deadlines
        ]
        strategy_items = [
            {
                "key": item.key,
                "title": item.title,
                "description": item.description,
                "priority": item.priority,
                "target_point_keys": item.target_point_keys,
            }
            for item in state.strategy_items
        ]
        appeal_drafts = [
            {
                "document_type": draft.document_type,
                "title": draft.title,
                "status": draft.status,
                "version": draft.version,
            }
            for draft in state.appeal_drafts
        ]

        next_deadline = self._get_next_pending_deadline(state.deadlines)
        days_remaining = self._days_until(next_deadline.due_date if next_deadline else None)
        priority_strategy = self._get_priority_strategy(state.strategy_items)
        urgency_level = self._get_urgency_level(days_remaining, bool(next_deadline))
        appeal_readiness = self._get_appeal_readiness(state)

        deadline_status = {
            "has_pending_deadline": bool(next_deadline),
            "next_deadline_title": next_deadline.title if next_deadline else None,
            "next_deadline_date": next_deadline.due_date if next_deadline else None,
            "days_remaining": days_remaining,
            "status": next_deadline.status if next_deadline else "nao_informado",
        }

        evidence_focus = [
            self._build_evidence_focus_item(point)
            for point in decision.unfavorable_points
        ]

        counts = {
            "unfavorable_points": len(unfavorable_points),
            "deadlines": len(deadlines),
            "strategy_items": len(strategy_items),
            "appeal_drafts": len(appeal_drafts),
        }

        risk_alerts = self._build_risk_alerts(
            state=state,
            days_remaining=days_remaining,
            has_pending_deadline=bool(next_deadline),
            decision=decision,
        )

        executive_headline = self._build_headline(
            decision=decision,
            counts=counts,
            deadline_status=deadline_status,
            priority_strategy=priority_strategy,
        )
        executive_summary = self._build_executive_summary(
            decision=decision,
            counts=counts,
            urgency_level=urgency_level,
            appeal_readiness=appeal_readiness,
            deadline_status=deadline_status,
            priority_strategy=priority_strategy,
        )
        recommendation = self._build_recommendation(
            urgency_level=urgency_level,
            appeal_readiness=appeal_readiness,
            deadline_status=deadline_status,
            priority_strategy=priority_strategy,
            has_draft=bool(state.appeal_drafts),
        )

        return {
            "area": state.area,
            "case_id": state.case_id,
            "tenant_id": state.tenant_id,
            "decision_type": decision.decision_type,
            "decision_title": decision.title,
            "decision_summary": decision.summary,
            "executive_headline": executive_headline,
            "executive_summary": executive_summary,
            "recommendation": recommendation,
            "urgency_level": urgency_level,
            "appeal_readiness": appeal_readiness,
            "deadline_status": deadline_status,
            "priority_strategy": priority_strategy,
            "evidence_focus": evidence_focus,
            "risk_alerts": risk_alerts,
            "counts": counts,
            "unfavorable_points": unfavorable_points,
            "deadlines": deadlines,
            "strategy_items": strategy_items,
            "appeal_drafts": appeal_drafts,
        }

    def _build_evidence_focus_item(self, point) -> dict[str, object]:
        return {
            "point_key": point.key,
            "title": point.title,
            "current_gap": point.description,
            "recommended_focus": self._recommend_evidence(point.title, point.description),
        }

    def _recommend_evidence(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()

        if "jornada" in text or "hora" in text:
            return (
                "Reunir cartões de ponto, espelhos de jornada, mensagens, registros de acesso "
                "e testemunhas capazes de confirmar rotina e extrapolação habitual."
            )
        if "document" in text or "prova" in text:
            return (
                "Consolidar documentos contemporâneos ao fato, comunicações internas, recibos "
                "e qualquer registro que reduza a fragilidade probatória identificada na sentença."
            )
        if "técnic" in text or "períci" in text or "perici" in text:
            return (
                "Avaliar prova técnica complementar, quesitos, assistente técnico e documentos "
                "de suporte que enfrentem diretamente o fundamento utilizado na decisão."
            )
        if "testemunh" in text:
            return (
                "Mapear testemunhas úteis, coerentes e com conhecimento direto dos fatos, "
                "alinhando pontos de depoimento com os fundamentos a serem impugnados."
            )

        return (
            "Organizar prova documental, cronologia dos fatos e elementos de corroboração "
            "diretamente ligados ao ponto desfavorável identificado."
        )

    def _build_risk_alerts(
        self,
        state: AppealReactionState,
        days_remaining: int | None,
        has_pending_deadline: bool,
        decision: JudicialDecision,
    ) -> list[str]:
        alerts: list[str] = []

        if not has_pending_deadline:
            alerts.append(
                "Nenhum prazo recursal foi cadastrado; validar imediatamente a contagem processual antes de qualquer protocolo."
            )
        elif days_remaining is not None and days_remaining < 0:
            alerts.append(
                "Há indicativo de prazo vencido ou potencialmente vencido; conferir publicação, intimação e eventual suspensão processual."
            )
        elif days_remaining is not None and days_remaining <= 3:
            alerts.append(
                "Prazo recursal em janela crítica; priorizar revisão final, assinatura e protocolo sem deslocar foco para tarefas secundárias."
            )
        elif days_remaining is not None and days_remaining <= 7:
            alerts.append(
                "Prazo recursal em janela sensível; acelerar fechamento da tese, documentos e minuta."
            )

        if not state.strategy_items:
            alerts.append(
                "Ainda não há estratégia recursal cadastrada; o recurso corre risco de sair genérico e pouco direcionado."
            )

        if not state.appeal_drafts:
            alerts.append(
                "Não há minuta vinculada ao estado recursal; preparar texto-base para evitar protocolo de última hora."
            )

        if any("prova" in (point.description or "").lower() for point in decision.unfavorable_points):
            alerts.append(
                "A decisão desfavorável está apoiada em fragilidade probatória; o reforço documental e testemunhal deve ser prioridade máxima."
            )

        return alerts

    def _build_headline(
        self,
        decision: JudicialDecision,
        counts: dict[str, int],
        deadline_status: dict[str, object],
        priority_strategy: dict[str, object],
    ) -> str:
        point_count = counts.get("unfavorable_points", 0)
        deadline_date = self._format_date_pt_br(deadline_status.get("next_deadline_date"))
        strategy_title = priority_strategy.get("title")

        point_phrase = self._format_quantity_phrase(
            point_count,
            "ponto desfavorável identificado",
            "pontos desfavoráveis identificados",
        )

        headline = f"Há matéria recursal relevante, com {point_phrase} na decisão."
        if strategy_title:
            headline += f" A frente prioritária, neste momento, é {strategy_title}."
        if deadline_date:
            headline += f" O prazo atualmente monitorado vai até {deadline_date}."

        return headline

    def _build_executive_summary(
        self,
        decision: JudicialDecision,
        counts: dict[str, int],
        urgency_level: str,
        appeal_readiness: str,
        deadline_status: dict[str, object],
        priority_strategy: dict[str, object],
    ) -> str:
        point_count = counts.get("unfavorable_points", 0)
        deadline_date = self._format_date_pt_br(deadline_status.get("next_deadline_date"))
        strategy_title = priority_strategy.get("title") or "revisão dos fundamentos impugnados"
        decision_label = self._normalize_decision_type(decision.decision_type)
        point_phrase = self._format_quantity_phrase(
            point_count,
            "ponto desfavorável identificado",
            "pontos desfavoráveis identificados",
        )
        urgency_label = self._normalize_urgency_label(urgency_level)
        readiness_label = self._normalize_readiness_label(appeal_readiness)

        parts = [
            f"{decision_label} com {point_phrase}.",
            f"O cenário recomenda atuação com urgência {urgency_label} e apresenta prontidão recursal {readiness_label}.",
            f"O eixo estratégico mais promissor, neste momento, é {strategy_title}.",
        ]

        if decision.summary:
            summary_text = str(decision.summary).strip()
            if summary_text and not summary_text.endswith("."):
                summary_text += "."
            parts.append(f"Em síntese, a decisão registra que {summary_text[0].lower() + summary_text[1:] if len(summary_text) > 1 else summary_text.lower()}")

        if deadline_date:
            parts.append(f"O prazo recursal em monitoramento se encerra em {deadline_date}.")
        else:
            parts.append(
                "O prazo recursal ainda não foi validado no sistema e deve ser confirmado com prioridade absoluta."
            )

        return " ".join(parts)

    def _build_recommendation(
        self,
        urgency_level: str,
        appeal_readiness: str,
        deadline_status: dict[str, object],
        priority_strategy: dict[str, object],
        has_draft: bool,
    ) -> str:
        strategy_title = priority_strategy.get("title") or "revisão da tese recursal"
        next_deadline_date = self._format_date_pt_br(deadline_status.get("next_deadline_date"))

        if urgency_level == "critica":
            if next_deadline_date:
                return (
                    f"Prioridade máxima: concluir a minuta, fechar a prova de suporte e confirmar o prazo fatal "
                    f"de {next_deadline_date} antes de qualquer refinamento acessório."
                )
            return (
                "Prioridade máxima: concluir a minuta, fechar a prova de suporte e validar imediatamente o prazo fatal "
                "antes de qualquer refinamento acessório."
            )

        if appeal_readiness == "alta" and has_draft:
            return (
                f"Avançar para revisão final da minuta, reforçar o lastro probatório e depurar os fundamentos "
                f"centrais ligados à estratégia de {strategy_title}, preparando o protocolo com segurança."
            )

        return (
            f"Estruturar imediatamente a minuta recursal, consolidar documentos de suporte e amarrar a tese principal "
            f"em {strategy_title}, com conferência final de prazo e fundamentos antes do protocolo."
        )

    def _format_date_pt_br(self, value: object) -> str | None:
        if not value:
            return None
        try:
            parsed = date.fromisoformat(str(value))
        except ValueError:
            return str(value)
        return parsed.strftime("%d/%m/%Y")

    def _format_quantity_phrase(
        self,
        count: int,
        singular: str,
        plural: str,
    ) -> str:
        if count == 1:
            return f"1 {singular}"
        return f"{count} {plural}"

    def _normalize_decision_type(self, value: str | None) -> str:
        normalized = str(value or "").strip().lower()
        labels = {
            "sentenca": "Sentença",
            "sentença": "Sentença",
            "acordao": "Acórdão",
            "acórdão": "Acórdão",
            "decisao interlocutoria": "Decisão interlocutória",
            "decisão interlocutória": "Decisão interlocutória",
            "despacho": "Despacho",
        }
        if normalized in labels:
            return labels[normalized]

        cleaned = str(value or "").replace("_", " ").strip()
        if not cleaned:
            return "Decisão judicial"
        return cleaned[:1].upper() + cleaned[1:]

    def _normalize_urgency_label(self, value: str | None) -> str:
        labels = {
            "critica": "crítica",
            "alta": "alta",
            "moderada": "moderada",
            "baixa": "baixa",
            "indefinida": "indefinida",
        }
        return labels.get(str(value or "").strip().lower(), str(value or "indefinida"))

    def _normalize_readiness_label(self, value: str | None) -> str:
        labels = {
            "alta": "alta",
            "media": "média",
            "média": "média",
            "baixa": "baixa",
        }
        return labels.get(str(value or "").strip().lower(), str(value or "baixa"))

    def _get_next_pending_deadline(
        self,
        deadlines: list[AppealDeadline],
    ) -> AppealDeadline | None:
        pending = [
            deadline
            for deadline in deadlines
            if str(deadline.status).lower() in {"pending", "pendente", "open", "aberto"}
        ]
        if not pending:
            return None

        def sort_key(deadline: AppealDeadline) -> tuple[int, str]:
            if deadline.due_date:
                return (0, deadline.due_date)
            return (1, "9999-12-31")

        return sorted(pending, key=sort_key)[0]

    def _days_until(self, due_date_str: str | None) -> int | None:
        if not due_date_str:
            return None
        try:
            due_date = date.fromisoformat(due_date_str)
        except ValueError:
            return None
        return (due_date - date.today()).days

    def _get_priority_strategy(
        self,
        strategy_items: list[AppealStrategyItem],
    ) -> dict[str, object]:
        if not strategy_items:
            return {}

        best_item = sorted(
            strategy_items,
            key=lambda item: self._priority_rank(item.priority),
            reverse=True,
        )[0]

        return {
            "key": best_item.key,
            "title": best_item.title,
            "description": best_item.description,
            "priority": best_item.priority,
            "target_point_keys": best_item.target_point_keys,
        }

    def _priority_rank(self, value: str | None) -> int:
        normalized = str(value or "").strip().lower()
        ranks = {
            "altissima": 4,
            "altíssima": 4,
            "alta": 3,
            "high": 3,
            "media": 2,
            "média": 2,
            "normal": 1,
            "baixa": 0,
            "low": 0,
        }
        return ranks.get(normalized, 1)

    def _get_urgency_level(
        self,
        days_remaining: int | None,
        has_pending_deadline: bool,
    ) -> str:
        if not has_pending_deadline:
            return "indefinida"
        if days_remaining is None:
            return "moderada"
        if days_remaining <= 3:
            return "critica"
        if days_remaining <= 7:
            return "alta"
        if days_remaining <= 15:
            return "moderada"
        return "baixa"

    def _get_appeal_readiness(
        self,
        state: AppealReactionState,
    ) -> str:
        score = 0
        if state.deadlines:
            score += 1
        if state.strategy_items:
            score += 1
        if state.appeal_drafts:
            score += 1

        if score == 3:
            return "alta"
        if score == 2:
            return "media"
        return "baixa"

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
