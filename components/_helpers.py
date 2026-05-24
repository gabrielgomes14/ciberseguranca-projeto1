"""Helpers internos compartilhados entre os componentes de cards."""

import html
from datetime import date

import streamlit as st

_COR_INK = "var(--text-color)"


def _parse_prazo(s: str) -> date | None:
    """Converte string ISO (YYYY-MM-DD) em date, ou None se vazia/inválida."""
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def _render_header_card(item_id: str, titulo: str, cor: str) -> None:
    """Renderiza o cabeçalho compartilhado por `render_control_card` e `render_item_card`.

    Layout: dot colorido + "ID - Título". Usa `html.escape` no título para evitar
    quebra de layout ou XSS via `unsafe_allow_html=True`.
    """
    titulo_safe = html.escape(titulo)
    id_safe = html.escape(item_id)
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
        f"<span style='display:inline-block;width:10px;height:10px;"
        f"border-radius:50%;background:{cor};'></span>"
        f"<strong style='color:{_COR_INK};'>{id_safe} - {titulo_safe}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )
