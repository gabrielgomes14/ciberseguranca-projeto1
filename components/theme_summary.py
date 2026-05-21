import html

import streamlit as st

from core.scoring import STATUS_COLORS, clamp_score, status_label


def render_theme_summary(tema: str, score: float, n_conf: int, n_total: int) -> None:
    """Renderiza um resumo compacto de tema com badge de score colorido e barra de progresso.

    Args:
        tema: nome do tema/categoria a exibir.
        score: score 0-100; valores fora do intervalo são ajustados.
        n_conf: número de controles conformes.
        n_total: número total de controles. Deve ser >= n_conf >= 0.
    """
    if n_total < 0 or n_conf < 0 or n_conf > n_total:
        raise ValueError(f"Contagens inválidas: n_conf={n_conf}, n_total={n_total} (esperado 0 <= n_conf <= n_total)")

    score_safe = clamp_score(score)
    cor = STATUS_COLORS[status_label(score_safe)]
    tema_safe = html.escape(tema)
    with st.container(border=True):
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<strong style='color:#0f172a;'>{tema_safe}</strong>"
            f"<span style='background:{cor};color:#fff;padding:2px 10px;border-radius:999px;font-size:0.8rem;'>"
            f"{score_safe:.1f}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(int(score_safe))
        st.caption(f"{n_conf}/{n_total} controles conformes")
