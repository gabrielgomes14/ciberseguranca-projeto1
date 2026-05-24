import plotly.graph_objects as go
import streamlit as st

from core.scoring import (
    RESPOSTA_CONFORME,
    RESPOSTA_EM_ADEQUACAO,
    RESPOSTA_NAO_CONFORME,
    SCORE_THRESHOLD_CONFORME,
    SCORE_THRESHOLD_EM_ADEQUACAO,
    STATUS_COLORS,
    clamp_score,
    status_label,
)

_LAYOUT_TRANSPARENT_BG = "rgba(0,0,0,0)"
_THEME_PALETTES = {
    "light": {
        "primary": "#1d4ed8",
        "surface": "#f1f5f9",
        "text": "#0f172a",
        "muted": "#475569",
        "axis": "#94a3b8",
    },
    "dark": {
        "primary": "#60a5fa",
        "surface": "#111827",
        "text": "#e5e7eb",
        "muted": "#9ca3af",
        "axis": "#64748b",
    },
}


def _theme_palette() -> dict[str, str]:
    theme_name = st.session_state.get("theme", "dark")
    return _THEME_PALETTES.get(theme_name, _THEME_PALETTES["dark"])


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Converte uma cor hex em rgba(r,g,b,a).

    Aceita `#RRGGBB` e `#RRGGBBAA`. Quando o hex tem 8 dígitos, o canal alpha
    embutido é descartado em favor do parâmetro `alpha`, para manter consistência
    com os call sites existentes.
    """
    h = hex_color.lstrip("#")
    if len(h) not in (6, 8):
        raise ValueError(f"Esperado #RRGGBB ou #RRGGBBAA, recebido: {hex_color!r}")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def render_gauge(score: float, label: str, *, key: str | None = None) -> None:
    """Renderiza um gauge 0–100 colorido conforme `status_label(score)`."""
    score_safe = clamp_score(score)
    cor = STATUS_COLORS[status_label(score_safe)]
    palette = _theme_palette()
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_safe,
            number={"suffix": "%", "font": {"size": 36, "color": palette["text"]}},
            title={"text": label, "font": {"size": 16, "color": palette["muted"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": palette["axis"]},
                "bar": {"color": cor, "thickness": 0.3},
                "bgcolor": palette["surface"],
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, SCORE_THRESHOLD_EM_ADEQUACAO],
                        "color": _hex_to_rgba(STATUS_COLORS[RESPOSTA_NAO_CONFORME], 0.15),
                    },
                    {
                        "range": [SCORE_THRESHOLD_EM_ADEQUACAO, SCORE_THRESHOLD_CONFORME],
                        "color": _hex_to_rgba(STATUS_COLORS[RESPOSTA_EM_ADEQUACAO], 0.15),
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
    st.plotly_chart(fig, width="stretch", key=key)


def render_radar(temas: list[str], scores: list[float], *, key: str | None = None) -> None:
    """Renderiza um radar comparando o score por tema. Exibe info se não houver dados."""
    if not temas or not scores:
        st.info("Sem dados suficientes para o radar.")
        return
    if len(temas) != len(scores):
        raise ValueError(f"temas ({len(temas)}) e scores ({len(scores)}) com tamanhos diferentes")

    valores = scores + [scores[0]]
    eixos = temas + [temas[0]]
    palette = _theme_palette()
    fig = go.Figure(
        go.Scatterpolar(
            r=valores,
            theta=eixos,
            fill="toself",
            line={"color": palette["primary"]},
            fillcolor=_hex_to_rgba(palette["primary"], 0.25),
            name="Score",
        )
    )
    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"color": palette["text"]},
                "gridcolor": palette["axis"],
            },
            "angularaxis": {"tickfont": {"color": palette["text"]}, "gridcolor": palette["axis"]},
        },
        showlegend=False,
        height=380,
        margin={"t": 20, "b": 20, "l": 40, "r": 40},
        font={"color": palette["text"]},
        paper_bgcolor=_LAYOUT_TRANSPARENT_BG,
    )
    st.plotly_chart(fig, width="stretch", key=key)


def render_bar_temas(temas: list[str], scores: list[float], *, key: str | None = None) -> None:
    """Renderiza barras horizontais com score por tema, coloridas por `status_label`."""
    if not temas or not scores:
        st.info("Sem dados suficientes para o gráfico de temas.")
        return
    if len(temas) != len(scores):
        raise ValueError(f"temas ({len(temas)}) e scores ({len(scores)}) com tamanhos diferentes")

    cores = [STATUS_COLORS[status_label(s)] for s in scores]
    palette = _theme_palette()
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
        xaxis={
            "range": [0, 100],
            "title": "Score",
            "tickfont": {"color": palette["text"]},
            "titlefont": {"color": palette["text"]},
        },
        yaxis={"tickfont": {"color": palette["text"]}},
        height=300,
        margin={"t": 20, "b": 30, "l": 100, "r": 20},
        font={"color": palette["text"]},
        paper_bgcolor=_LAYOUT_TRANSPARENT_BG,
        plot_bgcolor=_LAYOUT_TRANSPARENT_BG,
    )
    st.plotly_chart(fig, width="stretch", key=key)
