from core.types import ItemDiagnostico
from modulos.iso27701.controles import (
    CATEGORIAS,
    CONTROLES,
    CONTROLES_POR_CATEGORIA,
    MODULO_ID,
)


def test_modulo_id() -> None:
    assert MODULO_ID == "iso27701"


def test_categorias_cobrem_anexos_a1_a2_e_a3() -> None:
    """Inclui Controlador (A.1.*), Operador (A.2.*) e Segurança transversal (A.3)."""
    assert set(CATEGORIAS.keys()) == {
        "A.1.2",
        "A.1.3",
        "A.1.4",
        "A.1.5",
        "A.2.2",
        "A.2.3",
        "A.2.4",
        "A.2.5",
        "A.3",
    }


def test_controles_nao_vazios() -> None:
    assert len(CONTROLES) > 0
    assert all(isinstance(c, ItemDiagnostico) for c in CONTROLES)


def test_todos_controles_pertencem_a_categoria_conhecida() -> None:
    cats = set(CATEGORIAS.keys())
    for c in CONTROLES:
        assert c.categoria_id in cats, f"Controle {c.id} em categoria desconhecida {c.categoria_id!r}"


def test_ids_unicos() -> None:
    ids = [c.id for c in CONTROLES]
    assert len(ids) == len(set(ids)), "Há controles com id duplicado"


def test_categoria_id_derivada_corretamente() -> None:
    """A.x.y.z → A.x.y; A.3.z → A.3."""
    for c in CONTROLES:
        if c.id.startswith("A.3"):
            assert c.categoria_id == "A.3"
        else:
            partes = c.id.split(".")
            assert c.categoria_id == ".".join(partes[:3])


def test_modulo_dos_controles() -> None:
    assert all(c.modulo == "iso27701" for c in CONTROLES)


def test_controles_por_categoria_consistente() -> None:
    total = sum(len(v) for v in CONTROLES_POR_CATEGORIA.values())
    assert total == len(CONTROLES)
    for cat in CATEGORIAS:
        for controle in CONTROLES_POR_CATEGORIA[cat]:
            assert controle.categoria_id == cat



def test_anexo_b_operador_presente() -> None:
    """A.2.* (Operador) deve estar presente após este commit."""
    a2_ids = [c.id for c in CONTROLES if c.id.startswith("A.2.")]
    assert len(a2_ids) > 0, "Nenhum controle do Operador (A.2.*) encontrado"
    # Pelo menos uma categoria de cada subgrupo de operador.
    a2_cats = {c.categoria_id for c in CONTROLES if c.id.startswith("A.2.")}
    assert a2_cats == {"A.2.2", "A.2.3", "A.2.4", "A.2.5"}
