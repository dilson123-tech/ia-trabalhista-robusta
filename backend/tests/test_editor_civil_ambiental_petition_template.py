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


def test_civil_ambiental_petition_template_is_clean_for_antonia_case():
    case = SimpleNamespace(
        id=999,
        tenant_id=77,
        case_number="REAL-CIV-AMB-ANTONIA-CENTRAL-LAGES-2026-001",
        title="Antonia Estevão x Central Lages — Poeira, ruído, vibração e risco à saúde",
        legal_area="civil_ambiental",
        action_type="Ação de Obrigação de Fazer c/c Tutela de Urgência e Danos Morais",
        status="draft",
        description=(
            "A autora Antonia Estevão reside em imóvel residencial situado em Itapoá/SC, "
            "ao lado da empresa Central Lages Indústria e Comércio de Tubos Ltda., que explora "
            "atividade industrial com tubos de concreto.\n\n"
            "Segundo relatado, a empresa ré vem causando emissão excessiva de poeira de cimento, "
            "ruído constante no período diurno, vibração diária, obstrução da visibilidade da via "
            "com tubos e veículos estacionados, além de manter ausência de muro, barreira física "
            "ou contenção adequada entre os imóveis.\n\n"
            "A situação afeta diretamente a autora, pessoa idosa de 77 anos, com problemas pulmonares, "
            "agravando riscos à sua saúde, aumentando desconforto respiratório e prejudicando o uso normal "
            "da residência.\n\n"
            "Além disso, moradores da residência trabalham no Porto de Itapoá em regime de turnos, "
            "havendo necessidade de repouso durante o dia, o que vem sendo prejudicado pelo ruído contínuo "
            "e pela atividade industrial próxima.\n\n"
            "Houve tentativa prévia de solução por meio de notificação extrajudicial encaminhada à empresa ré, "
            "mas não houve providência eficaz para reduzir a poeira, o ruído, a vibração ou instalar barreira adequada."
        ),
    )

    analysis_record = SimpleNamespace(
        analysis={
            "technical": {
                "summary": "Caso civil ambiental envolvendo poeira, ruído, vibração e risco à saúde.",
                "issues": [
                    "direito de vizinhança",
                    "tutela de urgência",
                    "obrigação de fazer/não fazer",
                ],
                "next_steps": [
                    "juntar fotos, vídeos, notificação, documentos médicos e testemunhas",
                ],
            },
            "strategic": {
                "recommended_strategy": "Ajuizar ação de obrigação de fazer com tutela de urgência.",
                "critical_points": [
                    "risco à saúde de pessoa idosa",
                    "necessidade de prova técnica",
                ],
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

    assert "antonia estevão" in combined_text
    assert "central lages indústria e comércio de tubos ltda" in combined_text
    assert "itapoá/sc" in combined_text
    assert "ação de obrigação de fazer" in combined_text
    assert "tutela de urgência" in combined_text
    assert "direito de vizinhança" in combined_text
    assert "poeira de cimento" in combined_text
    assert "ruído" in combined_text
    assert "vibração" in combined_text
    assert "pessoa idosa" in combined_text
    assert "problemas pulmonares" in combined_text
    assert "multa diária" in combined_text
    assert "pericial ambiental/acústica" in combined_text
    assert "parte autora" in combined_text
    assert "parte ré" in combined_text

    forbidden_terms = [
        "estratégia jurídica sugerida",
        "lacunas probatórias",
        "viabilidade moderada",
        "ação de cobrança",
        "saldo inadimplido",
        "fgts",
        "clt",
        "reclamante",
        "reclamada",
        "dilstech",
        "mercado costa norte",
        "alfa reformas",
        "beta comércio",
        "dlp manutenção",
        "restaurante mar azul",
    ]

    for term in forbidden_terms:
        assert term not in combined_text, f"Termo indevido encontrado: {term}"
