"""Testa o helper interno `_render_header_card` sem depender de Streamlit em runtime."""

from unittest.mock import MagicMock, patch

from components._helpers import _render_header_card


def _capturar_markdown(item_id: str, titulo: str, cor: str) -> str:
    """Invoca o helper com `st.markdown` mockado e devolve o HTML gerado."""
    with patch("components._helpers.st") as st_mock:
        st_mock.markdown = MagicMock()
        _render_header_card(item_id, titulo, cor)
        assert st_mock.markdown.called
        return str(st_mock.markdown.call_args[0][0])


def test_render_header_card_inclui_id_e_titulo() -> None:
    html_str = _capturar_markdown("5.1", "Políticas de SI", "#16a34a")
    assert "5.1" in html_str
    assert "Políticas de SI" in html_str
    assert "#16a34a" in html_str


def test_render_header_card_escapa_titulo_xss() -> None:
    """Títulos maliciosos não devem ser injetados como HTML."""
    html_str = _capturar_markdown("X.1", "<script>alert(1)</script>", "#000")
    assert "<script>" not in html_str
    assert "&lt;script&gt;" in html_str


def test_render_header_card_escapa_id_xss() -> None:
    html_str = _capturar_markdown("<b>injetado</b>", "Título", "#000")
    assert "<b>injetado</b>" not in html_str
    assert "&lt;b&gt;injetado&lt;/b&gt;" in html_str


def test_render_header_card_passa_unsafe_allow_html() -> None:
    """O helper precisa de `unsafe_allow_html=True` para renderizar o dot colorido."""
    with patch("components._helpers.st") as st_mock:
        st_mock.markdown = MagicMock()
        _render_header_card("X", "T", "#000")
        kwargs = st_mock.markdown.call_args[1]
        assert kwargs.get("unsafe_allow_html") is True


def test_render_header_card_usa_constante_de_cor_de_texto() -> None:
    """A cor do texto do cabeçalho vem de `_COR_INK`, não de literal duplicado."""
    from components._helpers import _COR_INK

    html_str = _capturar_markdown("X", "T", "#000")
    assert _COR_INK in html_str
