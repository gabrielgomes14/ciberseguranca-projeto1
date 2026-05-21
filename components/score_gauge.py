import plotly.graph_objects as go
import streamlit as st

from core.scoring import (
    RESPOSTA_CONFORME,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_PARCIAL,
    SCORE_THRESHOLD_CONFORME,
    SCORE_THRESHOLD_PARCIAL,
    STATUS_COLORS,
    status_label,
)

_LAYOUT_TRANSPARENT_BG = "rgba(0,0,0,0)"


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converte uma cor #RRGGBB em rgba(r,g,b,a). Lança ValueError para formatos inesperados."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Esperado #RRGGBB, recebido: {hex_color!r}")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _clamp_score(score: float) -> float:
    """Garante que o score fique no intervalo [0, 100]."""
    return max(0.0, min(100.0, score))


def render_gauge(score: float, label: str, *, key: str | None = None) -> None:
    """Renderiza um gauge 0–100 colorido conforme `status_label(score)`."""
    score_safe = _clamp_score(score)
    cor = STATUS_COLORS[status_label(score_safe)]
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_safe,
            number={"suffix": "%", "font": {"size": 36, "color": "#0f172a"}},
            title={"text": label, "font": {"size": 16, "color": "#475569"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
                "bar": {"color": cor, "thickness": 0.3},
                "bgcolor": "#f1f5f9",
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, SCORE_THRESHOLD_PARCIAL],
                        "color": _hex_to_rgba(STATUS_COLORS[RESPOSTA_NAO_CONFORME], 0.15),
                    },
                    {
                        "range": [SCORE_THRESHOLD_PARCIAL, SCORE_THRESHOLD_CONFORME],
                        "color": _hex_to_rgba(STATUS_COLORS[RESPOSTA_PARCIAL], 0.15),
                    },
                    {
                        "range": [SCORE_THRESHOLD_CONFORME, 100],
                        "color": _hex_to_rgba(STATUS_COLORS[RESPOSTA_CONFORME], 0.15),
                    },
                ],
            },
        )
    )
    fig.update_layout(
        height=240,
        margin={"t": 30, "b": 10, "l": 20, "r": 20},
        paper_bgcolor=_LAYOUT_TRANSPARENT_BG,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_radar(temas: list[str], scores: list[float], *, key: str | None = None) -> None:
    """Renderiza um radar comparando o score por tema. Exibe info se não houver dados."""
    if not temas or not scores:
        st.info("Sem dados suficientes para o radar.")
        return
    if len(temas) != len(scores):
        raise ValueError(f"temas ({len(temas)}) e scores ({len(scores)}) com tamanhos diferentes")

    valores = scores + [scores[0]]
    eixos = temas + [temas[0]]
    fig = go.Figure(
        go.Scatterpolar(
            r=valores,
            theta=eixos,
            fill="toself",
            line={"color": "#1d4ed8"},
            fillcolor="rgba(29, 78, 216, 0.25)",
            name="Score",
        )
    )
    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 100]}},
        showlegend=False,
        height=380,
        margin={"t": 20, "b": 20, "l": 40, "r": 40},
        paper_bgcolor=_LAYOUT_TRANSPARENT_BG,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_bar_temas(temas: list[str], scores: list[float], *, key: str | None = None) -> None:
    """Renderiza barras horizontais com score por tema, coloridas por `status_label`."""
    if not temas or not scores:
        st.info("Sem dados suficientes para o gráfico de temas.")
        return
    if len(temas) != len(scores):
        raise ValueError(f"temas ({len(temas)}) e scores ({len(scores)}) com tamanhos diferentes")

    cores = [STATUS_COLORS[status_label(s)] for s in scores]
    fig = go.Figure(
        go.Bar(
            x=scores,
            y=temas,
            orientation="h",
            marker={"color": cores},
            text=[f"{s:.1f}%" for s in scores],
            textposition="auto",
        )
    )
    fig.update_layout(
        xaxis={"range": [0, 100], "title": "Score"},
        height=300,
        margin={"t": 20, "b": 30, "l": 100, "r": 20},
        paper_bgcolor=_LAYOUT_TRANSPARENT_BG,
        plot_bgcolor=_LAYOUT_TRANSPARENT_BG,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)
