from app.modules.document_factory import (
    DocumentFactoryService,
    IntakeEmployment,
    IntakeItem,
    IntakeParty,
    PeticaoInicialTrabalhistaIntake,
)
from app.modules.legal_editor import LegalEditorService


def _build_sample_draft():
    intake = PeticaoInicialTrabalhistaIntake(
        reclamante=IntakeParty(
            nome="Ana Pereira",
            documento="123.456.789-00",
            qualificacao="brasileira, auxiliar administrativa",
        ),
        reclamada=IntakeParty(
            nome="Empresa Ômega Ltda.",
            documento="12.345.678/0001-55",
            qualificacao="pessoa jurídica de direito privado",
        ),
        vinculo=IntakeEmployment(
            data_admissao="2021-03-10",
            data_dispensa="2024-02-01",
            funcao="Auxiliar administrativa",
            salario="R$ 2.800,00",
            jornada="Segunda a sexta, das 08h às 17h",
        ),
        fatos=[
            IntakeItem(
                titulo="Horas extras sem pagamento",
                descricao="A reclamante prestava horas extras habituais sem quitação integral.",
            ),
        ],
        pedidos=[
            IntakeItem(
                titulo="Horas extras com reflexos",
                descricao="Condenação ao pagamento das horas extras e reflexos legais.",
                fundamento_legal="CLT, art. 59",
            ),
        ],
        fundamentos=[
            IntakeItem(
                titulo="Violação à jornada legal",
                descricao="Descumprimento das regras de duração do trabalho.",
                fundamento_legal="CLT, art. 58 e 59",
            ),
        ],
        provas=[
            IntakeItem(
                titulo="Cartões de ponto",
                descricao="Apresentação de controles de jornada e prova testemunhal.",
            ),
        ],
        valor_causa="R$ 22.000,00",
    )

    document_factory = DocumentFactoryService()
    return document_factory.build_peticao_inicial_trabalhista_from_intake(
        intake=intake,
        case_id=77,
        tenant_id=9,
        user_id=11,
    )


def test_legal_editor_creates_editable_document_from_draft():
    draft = _build_sample_draft()
    service = LegalEditorService()

    editable = service.create_from_draft(
        draft=draft,
        created_by_user_id=11,
    )

    assert editable.area == "trabalhista"
    assert editable.document_type == "peticao_inicial_trabalhista"
    assert editable.case_id == 77
    assert editable.tenant_id == 9
    assert len(editable.versions) == 1
    assert editable.current_version is not None
    assert editable.current_version.version == 1
    assert editable.current_version.approved is False
    assert editable.current_version.created_by_user_id == 11
    assert len(editable.current_version.sections) >= 1
    assert editable.current_version.sections[0].source == "ai"


def test_legal_editor_updates_single_section_without_destroying_previous_version():
    draft = _build_sample_draft()
    service = LegalEditorService()

    editable = service.create_from_draft(draft=draft, created_by_user_id=11)
    updated = service.update_section(
        document=editable,
        section_key="fatos",
        new_content="Nova narrativa fática ajustada manualmente pelo advogado.",
        edited_by_user_id=22,
        notes="Refino da narrativa",
    )

    assert len(editable.versions) == 1
    assert len(updated.versions) == 2
    assert updated.current_version is not None
    assert updated.current_version.version == 2
    assert updated.current_version.approved is False
    assert updated.current_version.created_by_user_id == 22
    assert updated.current_version.notes == "Refino da narrativa"
    assert updated.current_version.metadata["parent_version"] == 1
    assert updated.current_version.metadata["section_key"] == "fatos"

    old_sections = {section.key: section for section in editable.current_version.sections}
    new_sections = {section.key: section for section in updated.current_version.sections}

    assert old_sections["fatos"].content != new_sections["fatos"].content
    assert new_sections["fatos"].content == "Nova narrativa fática ajustada manualmente pelo advogado."
    assert new_sections["fatos"].source == "manual"
    assert new_sections["fatos"].status == "edited"
    assert new_sections["fatos"].metadata["edited_by_user_id"] == 22
    assert old_sections["pedidos"].content == new_sections["pedidos"].content


def test_legal_editor_approves_current_version():
    draft = _build_sample_draft()
    service = LegalEditorService()

    editable = service.create_from_draft(draft=draft, created_by_user_id=11)
    updated = service.update_section(
        document=editable,
        section_key="pedidos",
        new_content="Pedidos revisados e reforçados.",
        edited_by_user_id=22,
    )
    approved = service.approve_current_version(
        document=updated,
        approved_by_user_id=33,
        notes="Versão aprovada para exportação",
    )

    assert len(approved.versions) == 3
    assert approved.current_version is not None
    assert approved.current_version.version == 3
    assert approved.current_version.approved is True
    assert approved.current_version.created_by_user_id == 33
    assert approved.current_version.notes == "Versão aprovada para exportação"
    assert approved.current_version.metadata["parent_version"] == 2
    assert approved.current_version.metadata["approved_by_user_id"] == 33
    assert all(section.status == "approved" for section in approved.current_version.sections)
