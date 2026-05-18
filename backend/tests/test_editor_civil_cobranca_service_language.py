from types import SimpleNamespace

from app.api.v1.routes.editable_documents import _build_assisted_sections


class FakeDB:
    def query(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return None


def test_civil_cobranca_reforma_does_not_reuse_electrical_service_language():
    case = SimpleNamespace(
        id=147,
        tenant_id=77,
        case_number="QA-CIVEL-COBRANCA-1778010837",
        title="QA profissional — cobrança de contrato de reforma inadimplido",
        legal_area="civel",
        action_type="Ação de Cobrança",
        status="draft",
        description=(
            "A empresa Alfa Reformas Ltda. foi contratada pela empresa Beta Comércio de Móveis Ltda. "
            "para executar reforma interna em loja comercial situada em Itapoá/SC. "
            "O contrato foi assinado em 15/03/2026, no valor total de R$ 32.000,00, "
            "com pagamento em quatro parcelas de R$ 8.000,00. "
            "A contratada executou integralmente os serviços entre 16/03/2026 e 10/04/2026, "
            "incluindo troca de piso, pintura, adequação elétrica leve e acabamento interno. "
            "A contratante pagou apenas as duas primeiras parcelas, totalizando R$ 16.000,00. "
            "As parcelas vencidas em 02/04/2026 e 12/04/2026 não foram quitadas, restando "
            "saldo principal inadimplido de R$ 16.000,00. "
            "Há contrato assinado, comprovantes dos dois pagamentos realizados, relatório de entrega da obra, "
            "fotografias do serviço concluído, e-mails de aprovação da entrega, mensagens de WhatsApp "
            "em que a devedora reconhece a dívida e notificação extrajudicial recebida sem pagamento."
        ),
    )

    analysis_record = SimpleNamespace(
        analysis={
            "technical": {
                "summary": "Cobrança cível de contrato de reforma interna inadimplido.",
                "issues": ["saldo contratual inadimplido", "multa", "juros", "correção monetária"],
                "next_steps": ["Conferir contrato, comprovantes, notificação e planilha."],
            },
            "strategic": {
                "recommended_strategy": "Propor ação de cobrança contratual.",
                "critical_points": ["Comprovar execução integral e inadimplemento."],
            },
        },
        executive_data={},
    )

    sections = _build_assisted_sections(
        FakeDB(),
        case,
        analysis_record,
        tenant_id=77,
        document_metadata={},
    )

    by_key = {section["key"]: section["content"] for section in sections}
    combined_text = "\n".join(by_key.values()).lower()

    assert "alfa reformas ltda" in combined_text
    assert "beta comércio de móveis ltda" in combined_text
    assert "reforma interna" in combined_text
    assert "r$ 16.000,00" in combined_text
    assert "ação de cobrança" in combined_text
    assert "vara cível da comarca de itapoá/sc" in combined_text
    assert "execução dos serviços contratados descritos na narrativa fática" in combined_text

    assert "manutenção elétrica preventiva e corretiva" not in combined_text
    assert "dlp manutenção" not in combined_text
    assert "restaurante mar azul" not in combined_text
    assert "título executivo extrajudicial probatório" not in combined_text
    assert "estratégia jurídica sugerida" not in combined_text
    assert "lacunas probatórias" not in combined_text
    assert "viabilidade moderada" not in combined_text
    assert "fgts" not in combined_text
    assert "clt" not in combined_text
