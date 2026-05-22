from reportlab.graphics.shapes import Drawing

from core.pdf_charts import chart_donut_status
from core.scoring import ResultadoTema


def _resumo(
    tema_id: str,
    *,
    total: int = 0,
    conformes: int = 0,
    parciais: int = 0,
    nao_conformes: int = 0,
    na: int = 0,
    score: float = 0.0,
) -> ResultadoTema:
    avaliados = conformes + parciais + nao_conformes
    return ResultadoTema(
        tema_id=tema_id,
        score=score,
        total=total,
        avaliados=avaliados,
        conformes=conformes,
        parciais=parciais,
        nao_conformes=nao_conformes,
        na=na,
    )


# --- chart_donut_status -----------------------------------------------------


def test_chart_donut_status_retorna_drawing() -> None:
    resumos = {
        "org": _resumo("org", total=10, conformes=6, parciais=2, nao_conformes=1, na=1),
    }
    d = chart_donut_status(resumos)
    assert isinstance(d, Drawing)
    # Drawing sem dados teria 1 elemento (String). Com fatias, esperamos pie + legend = 2.
    assert len(d.contents) == 2


def test_chart_donut_status_sem_dados() -> None:
    """resumos vazio → mensagem 'Sem dados'."""
    d = chart_donut_status({})
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


def test_chart_donut_status_total_zero() -> None:
    """resumos com total=0 → mensagem 'Sem dados'."""
    d = chart_donut_status({"x": _resumo("x", total=0)})
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


def test_chart_donut_status_apenas_uma_categoria_visivel() -> None:
    """Quando só conformes > 0, ainda assim renderiza pie + legend."""
    resumos = {"org": _resumo("org", total=5, conformes=5)}
    d = chart_donut_status(resumos)
    assert len(d.contents) == 2


def test_chart_donut_status_inclui_nao_avaliados() -> None:
    """total > soma(avaliados+na) implica fatia de 'Não avaliado'."""
    resumos = {"org": _resumo("org", total=10, conformes=2)}
    d = chart_donut_status(resumos)
    # Conformes (2) + Não avaliado (8) → pie + legend = 2 elementos.
    assert len(d.contents) == 2


def test_chart_donut_status_dimensoes_customizadas() -> None:
    resumos = {"x": _resumo("x", total=4, conformes=4)}
    d = chart_donut_status(resumos, largura_cm=20.0, altura_cm=8.0)
    assert isinstance(d, Drawing)
