from reportlab.graphics.shapes import Drawing

from core.pdf_charts import chart_barras_categoria, chart_donut_status, chart_radar
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


# --- chart_radar ------------------------------------------------------------


def test_chart_radar_com_tres_categorias() -> None:
    categorias = {"a": "A", "b": "B", "c": "C"}
    resumos = {
        "a": _resumo("a", total=1, conformes=1, score=100.0),
        "b": _resumo("b", total=1, parciais=1, score=50.0),
        "c": _resumo("c", total=1, nao_conformes=1, score=0.0),
    }
    d = chart_radar(categorias, resumos)
    assert isinstance(d, Drawing)
    # Espera-se o spider chart como único elemento.
    assert len(d.contents) == 1


def test_chart_radar_menos_de_tres_categorias_retorna_aviso() -> None:
    categorias = {"a": "A", "b": "B"}
    resumos = {
        "a": _resumo("a", total=1, score=80.0),
        "b": _resumo("b", total=1, score=60.0),
    }
    d = chart_radar(categorias, resumos)
    assert isinstance(d, Drawing)
    # Apenas a mensagem de aviso (String).
    assert len(d.contents) == 1


def test_chart_radar_sem_categorias() -> None:
    d = chart_radar({}, {})
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


def test_chart_radar_dimensoes_customizadas() -> None:
    categorias = {"a": "A", "b": "B", "c": "C", "d": "D"}
    resumos = {k: _resumo(k, total=1, score=50.0) for k in categorias}
    d = chart_radar(categorias, resumos, largura_cm=14.0, altura_cm=12.0)
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


# --- chart_barras_categoria -------------------------------------------------


def test_chart_barras_categoria_caminho_feliz() -> None:
    categorias = {"a": "A", "b": "B", "c": "C"}
    resumos = {
        "a": _resumo("a", total=10, conformes=9, score=90.0),
        "b": _resumo("b", total=10, parciais=5, score=50.0),
        "c": _resumo("c", total=10, nao_conformes=8, score=10.0),
    }
    d = chart_barras_categoria(categorias, resumos)
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


def test_chart_barras_categoria_uma_categoria() -> None:
    categorias = {"a": "Apenas uma"}
    resumos = {"a": _resumo("a", total=1, conformes=1, score=100.0)}
    d = chart_barras_categoria(categorias, resumos)
    # Diferente do radar, barras horizontais funcionam com 1 categoria.
    assert isinstance(d, Drawing)
    assert len(d.contents) == 1


def test_chart_barras_categoria_altura_calculada_automaticamente() -> None:
    """Sem altura_cm, ela é derivada do número de categorias."""
    categorias = {f"k{i}": f"Cat {i}" for i in range(8)}
    resumos = {k: _resumo(k, total=1, score=50.0) for k in categorias}
    d = chart_barras_categoria(categorias, resumos)
    # Altura esperada: max(4.0, 0.7 * 8 + 1.5) = 7.1 cm.
    altura_esperada_pts = 7.1 * 28.3464567  # 1 cm ≈ 28.35 pt
    assert abs(d.height - altura_esperada_pts) < 1.0


def test_chart_barras_categoria_altura_explicita_respeitada() -> None:
    categorias = {"a": "A", "b": "B"}
    resumos = {k: _resumo(k, total=1, score=50.0) for k in categorias}
    d = chart_barras_categoria(categorias, resumos, altura_cm=5.0)
    altura_esperada_pts = 5.0 * 28.3464567
    assert abs(d.height - altura_esperada_pts) < 1.0
