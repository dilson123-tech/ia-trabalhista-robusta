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


def test_civil_cobranca_structured_author_defendant_and_open_installments():
    case = SimpleNamespace(
        id=112,
        tenant_id=77,
        case_number="PAINEL-CIVEL-004",
        title="Cobrança contratual com documentos completos",
        legal_area="civel",
        action_type="Ação de Cobrança",
        status="draft",
        description=(
            "Autor: Alfa Soluções Empresariais LTDA.\n"
            "Réu: Beta Comércio de Equipamentos ME.\n\n"
            "Resumo do caso:\n"
            "Em 10/01/2026, as partes firmaram contrato de prestação de serviços de manutenção "
            "e suporte técnico mensal para equipamentos comerciais, no valor total de R$ 18.500,00, "
            "dividido em 3 parcelas.\n\n"
            "Cronologia dos fatos:\n"
            "- Contrato assinado em 10/01/2026.\n"
            "- Serviço executado entre 12/01/2026 e 28/02/2026.\n"
            "- Foram emitidas as notas fiscais nº 101, 102 e 103.\n"
            "- A ré pagou apenas a primeira parcela no valor de R$ 6.000,00 em 20/01/2026.\n"
            "- Permaneceram em aberto as parcelas de R$ 6.250,00 com vencimento em 20/02/2026 "
            "e R$ 6.250,00 com vencimento em 20/03/2026.\n"
            "- Em 25/03/2026, a autora enviou notificação extrajudicial por e-mail e WhatsApp.\n"
            "- Em 02/04/2026, a ré respondeu por WhatsApp reconhecendo que os serviços foram prestados.\n"
            "- Até a presente data, não houve pagamento do saldo."
        ),
    )

    analysis_record = SimpleNamespace(
        analysis={
            "technical": {
                "summary": "Cobrança cível estruturada com autor, réu, cronologia e parcelas em aberto.",
                "issues": ["saldo contratual inadimplido", "multa", "juros", "correção monetária"],
                "next_steps": ["Conferir contrato, notas fiscais, notificação e planilha."],
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

    combined_text = "\n".join(section["content"] for section in sections).lower()

    assert "alfa soluções empresariais ltda" in combined_text
    assert "beta comércio de equipamentos me" in combined_text
    assert "ação de cobrança" in combined_text
    assert "vara cível da comarca competente" in combined_text
    assert "r$ 12.500,00" in combined_text
    assert "[local a definir]" in combined_text

    assert "[nome completo da parte autora]" not in combined_text
    assert "[nome/razão social da parte ré]" not in combined_text
    assert "r$ [valor a ser definido pelo advogado]" not in combined_text
    assert "[comarca a definir pelo advogado]" not in combined_text
    assert "fgts" not in combined_text
    assert "clt" not in combined_text
    assert "reclamação trabalhista" not in combined_text
