from types import SimpleNamespace

from app.api.v1.routes.editable_documents import _resolve_editor_export_title


class FakeQuery:
    def __init__(self, case):
        self.case = case

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.case


class FakeDB:
    def __init__(self, case):
        self.case = case

    def query(self, model):
        return FakeQuery(self.case)


def test_resolve_editor_export_title_prefers_document_metadata_display_title():
    document = SimpleNamespace(
        document_metadata={"display_title": "Título definido no documento"},
        case_id=10,
        title="Título antigo do documento",
    )
    db = FakeDB(case=SimpleNamespace(title="Título do caso"))

    assert _resolve_editor_export_title(db, document, tenant_id=77) == "Título definido no documento"


def test_resolve_editor_export_title_falls_back_to_case_title():
    document = SimpleNamespace(
        document_metadata={},
        case_id=10,
        title="trab 005",
    )
    db = FakeDB(case=SimpleNamespace(title="FGTS não recolhido — ausência de depósitos durante o contrato"))

    assert (
        _resolve_editor_export_title(db, document, tenant_id=77)
        == "FGTS não recolhido — ausência de depósitos durante o contrato"
    )


def test_resolve_editor_export_title_falls_back_to_document_title_when_case_missing():
    document = SimpleNamespace(
        document_metadata={},
        case_id=10,
        title="Documento manual",
    )
    db = FakeDB(case=None)

    assert _resolve_editor_export_title(db, document, tenant_id=77) == "Documento manual"
