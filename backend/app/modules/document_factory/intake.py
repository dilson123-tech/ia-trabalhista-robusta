from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class IntakeParty:
    nome: str
    documento: str | None = None
    qualificacao: str | None = None


@dataclass(slots=True)
class IntakeEmployment:
    data_admissao: str | None = None
    data_dispensa: str | None = None
    funcao: str | None = None
    salario: str | None = None
    jornada: str | None = None
    resumo: str | None = None


@dataclass(slots=True)
class IntakeItem:
    titulo: str
    descricao: str
    fundamento_legal: str | None = None


@dataclass(slots=True)
class PeticaoInicialTrabalhistaIntake:
    reclamante: IntakeParty
    reclamada: IntakeParty
    vinculo: IntakeEmployment = field(default_factory=IntakeEmployment)
    fatos: list[IntakeItem] = field(default_factory=list)
    pedidos: list[IntakeItem] = field(default_factory=list)
    fundamentos: list[IntakeItem] = field(default_factory=list)
    provas: list[IntakeItem] = field(default_factory=list)
    valor_causa: str | None = None
    observacoes: str | None = None


def _join_items(items: list[IntakeItem], *, fallback: str) -> str:
    if not items:
        return fallback
    return "\n".join(f"- {item.titulo}: {item.descricao}" for item in items)


def build_peticao_inicial_payload_from_intake(
    intake: PeticaoInicialTrabalhistaIntake,
) -> dict[str, str]:
    contrato_partes = [
        f"Admissão: {intake.vinculo.data_admissao or 'não informada'}",
        f"Dispensa: {intake.vinculo.data_dispensa or 'não informada'}",
        f"Função: {intake.vinculo.funcao or 'não informada'}",
        f"Salário: {intake.vinculo.salario or 'não informado'}",
        f"Jornada: {intake.vinculo.jornada or 'não informada'}",
    ]

    contrato_resumo = intake.vinculo.resumo or "; ".join(contrato_partes)

    return {
        "reclamante_nome": intake.reclamante.nome,
        "reclamada_nome": intake.reclamada.nome,
        "contrato_resumo": contrato_resumo,
        "fatos": _join_items(
            intake.fatos,
            fallback="Descrever os fatos principais do caso trabalhista.",
        ),
        "pedidos": _join_items(
            intake.pedidos,
            fallback="Listar pedidos de forma objetiva, com reflexos e requerimentos finais.",
        ),
        "fundamentos": _join_items(
            intake.fundamentos,
            fallback="Indicar fundamentos jurídicos aplicáveis, verbas postuladas e violações alegadas.",
        ),
        "provas": _join_items(
            intake.provas,
            fallback="Indicar documentos, testemunhas e demais meios de prova pretendidos.",
        ),
        "valor_causa": intake.valor_causa or "Informar valor estimado da causa.",
    }
