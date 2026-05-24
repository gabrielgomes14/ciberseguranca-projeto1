from dataclasses import dataclass

from core.db import init_db, listar_controles_iso27001, listar_temas_iso27001


@dataclass(frozen=True)
class Controle:
    id: str
    titulo: str
    descricao: str
    tema_id: str
    controle_texto: str = ""
    proposito: str = ""
    orientacao: str = ""


def _carregar() -> tuple[dict[str, str], list[Controle], dict[str, list[Controle]]]:
    """Lê o catálogo ISO/IEC 27001 do banco, garantindo o seed automático.

    Retorna `(TEMA_LABELS, TODOS_CONTROLES, TEMAS)`. Chamado uma única vez no
    import do módulo. O conteúdo vem dos JSONs em `data/`, populados em
    `init_db()` via `_seed_catalogo`.
    """
    init_db()
    temas = listar_temas_iso27001()
    rows = listar_controles_iso27001()
    todos = [Controle(r.id, r.titulo, r.descricao, r.tema_id, r.controle_texto, r.proposito, r.orientacao) for r in rows]
    por_tema = {tema_id: [c for c in todos if c.tema_id == tema_id] for tema_id in temas}
    return temas, todos, por_tema


TEMA_LABELS, TODOS_CONTROLES, TEMAS = _carregar()
