from app.services.legal_modules import (
    OFFICIAL_LEGAL_MODULE_IDS,
    get_legal_module_config,
    infer_legal_module,
    list_legal_modules,
    normalize_legal_area,
)


def test_official_modules_are_registered():
    assert OFFICIAL_LEGAL_MODULE_IDS == (
        "trabalhista",
        "civel",
        "consumidor",
        "familia",
        "previdenciario",
        "criminal",
        "civil_ambiental",
    )


def test_normalize_legal_area_aliases():
    assert normalize_legal_area("Trabalhista") == "trabalhista"
    assert normalize_legal_area("Cível") == "civel"
    assert normalize_legal_area("Direito do Consumidor") == "consumidor"
    assert normalize_legal_area("Família") == "familia"
    assert normalize_legal_area("BPC/LOAS") == "previdenciario"
    assert normalize_legal_area("Penal") == "criminal"
    assert normalize_legal_area("Civil Ambiental") == "civil_ambiental"


def test_infer_submodules_from_generic_civel_cases():
    assert infer_legal_module(
        legal_area="civel",
        action_type="Consumidor — vício do produto com pedido de restituição",
    ) == "consumidor"

    assert infer_legal_module(
        legal_area="civel",
        action_type="Família — guarda e regulamentação de convivência",
    ) == "familia"

    assert infer_legal_module(
        legal_area="civel",
        description="Pedido de BPC/LOAS para pessoa idosa em vulnerabilidade social perante o INSS.",
    ) == "previdenciario"

    assert infer_legal_module(
        legal_area="civel",
        description="Caso com poeira, ruído, vibração e ausência de barreira entre imóveis.",
    ) == "civil_ambiental"


def test_explicit_non_civel_area_wins():
    assert infer_legal_module(
        legal_area="trabalhista",
        action_type="Cobrança de FGTS",
    ) == "trabalhista"

    assert infer_legal_module(
        legal_area="criminal",
        action_type="Habeas corpus inicial",
    ) == "criminal"


def test_module_config_and_listing():
    cfg = get_legal_module_config("bpc")
    assert cfg.id == "previdenciario"
    assert "BPC-LOAS" in cfg.label

    modules = list_legal_modules()
    ids = [item["id"] for item in modules]
    assert "criminal" in ids
    assert "civil_ambiental" in ids
