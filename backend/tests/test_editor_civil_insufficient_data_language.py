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


def test_civil_insufficient_data_guardrail_uses_civil_language():
    case = SimpleNamespace(
        id=111,
        tenant_id=77,
        case_number="PAINEL-CIVEL-003",
        title="Caso cível teste guardrail",
        legal_area="civel",
        action_type="Ação de Cobrança",
        status="draft",
        description="Caso cível com dados insuficientes.",
    )

    analysis_record = SimpleNamespace(
        analysis={
            "technical": {
                "summary": "",
                "issues": [],
                "next_steps": [],
            },
            "strategic": {},
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

    assert "dados insuficientes" in combined_text
    assert "fatos cíveis" in combined_text
    assert "tese jurídica cível" in combined_text
    assert "pedidos cíveis" in combined_text
    assert "período/cronologia" in combined_text
    assert "contexto do conflito" in combined_text

    assert "jornada" not in combined_text
    assert "vínculo" not in combined_text
    assert "verbas trabalhistas" not in combined_text
    assert "reclamação trabalhista" not in combined_text
    assert "fgts" not in combined_text
    assert "clt" not in combined_text
