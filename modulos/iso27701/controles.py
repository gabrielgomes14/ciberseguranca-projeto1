from core.db import init_db, listar_categorias_iso27701, listar_controles_iso27701
from core.types import ItemDiagnostico

MODULO_ID = "iso27701"


def _carregar() -> tuple[dict[str, str], list[ItemDiagnostico], dict[str, list[ItemDiagnostico]]]:
    """Lê o catálogo ISO/IEC 27701 do banco, garantindo o seed automático.

    Retorna `(CATEGORIAS, CONTROLES, CONTROLES_POR_CATEGORIA)`. Chamado uma única
    vez no import. As descrições já vêm com o sufixo LGPD embutido pelos JSONs
    em `data/`, populados em `init_db()`.
    """
    init_db()
    categorias = listar_categorias_iso27701()
    rows = listar_controles_iso27701()
    controles = [
        ItemDiagnostico(
            id=r.id,
            titulo=r.titulo,
            descricao=r.descricao,
            categoria_id=r.categoria_id,
            modulo=MODULO_ID,
            controle_texto=r.controle_texto,
            orientacao=r.orientacao,
        )
        for r in rows
    ]
    por_categoria = {cat: [c for c in controles if c.categoria_id == cat] for cat in categorias}
    return categorias, controles, por_categoria


CATEGORIAS, CONTROLES, CONTROLES_POR_CATEGORIA = _carregar()
