import streamlit as st

from core.scoring import STATUS_COLORS, status_label


def render_theme_summary(tema: str, score: float, n_conf: int, n_total: int) -> None:
    cor = STATUS_COLORS[status_label(score)]
    with st.container(border=True):
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<strong style='color:#0f172a;'>{tema}</strong>"
            f"<span style='background:{cor};color:#fff;padding:2px 10px;border-radius:999px;font-size:0.8rem;'>"
            f"{score:.1f}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(min(int(score), 100))
        st.caption(f"{n_conf}/{n_total} controles conformes")
