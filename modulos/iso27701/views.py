import streamlit as st

from components.generic_item_card import render_item_card
from core.db import listar_diagnosticos
from core.models import Avaliacao
from core.scoring import RESPOSTAS_VALIDAS
from core.state import avaliacoes_do_modulo, diagnostico_ativo, persistir
from modulos.iso27701.controles import CATEGORIAS, CONTROLES, CONTROLES_POR_CATEGORIA

MODULO_ID = "iso27701"
MODULO_NOME = "ISO/IEC 27701:2019"


def _barra_diagnostico() -> None:
    """Mostra o diagnóstico ativo e ações de salvar/listar no topo da view."""
    ativo_id = diagnostico_ativo(MODULO_ID)
    diags = listar_diagnosticos(MODULO_ID)
    diag_atual = next((d for d in diags if d.id == ativo_id), None)
    col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
    with col_d1:
        if diag_atual:
            st.info(f"Diagnóstico ativo: **{diag_atual.organizacao}** · ID #{ativo_id} · 📅 {diag_atual.data_auditoria}")
        else:
            st.warning("Nenhum diagnóstico ativo. Suas respostas não serão salvas.")
    with col_d2:
        if st.button(
            "💾 Salvar",
            use_container_width=True,
            disabled=ativo_id is None,
            key="27701_salvar",
        ):
            if persistir(MODULO_ID):
                st.toast("Salvo.", icon="💾")
    with col_d3:
        if st.button("📁 Diagnósticos", use_container_width=True, key="27701_lista"):
            st.session_state.modulo_alvo = MODULO_ID
            st.session_state.page = "diagnosticos"
            st.rerun()


def _render_sidebar(respondidos: int) -> None:
    """Sidebar de navegação do módulo. `respondidos` desabilita 'Resultado' quando 0."""
    with st.sidebar:
        st.markdown(f"### {MODULO_NOME}")
        if st.button("🏠 Início", use_container_width=True, key="27701_nav_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📋 Avaliar", use_container_width=True, key="27701_nav_assess"):
            st.session_state.page = "iso27701_assessment"
            st.rerun()
        if st.button(
            "📊 Resultado",
            use_container_width=True,
            disabled=respondidos == 0,
            key="27701_nav_dash",
        ):
            st.session_state.page = "iso27701_dashboard"
            st.rerun()
        if st.button("📈 Histórico", use_container_width=True, key="27701_nav_hist"):
            st.session_state.page = "history"
            st.rerun()


def render_assessment() -> None:
    """Tela de auto-avaliação do módulo 27701, com tabs por categoria."""
    st.title(f"🔒 {MODULO_NOME} — Sistema de Gestão de Informações de Privacidade")
    st.caption("Controles dos Anexos A (Controladores) e B (Operadores) — vinculados à LGPD quando aplicável.")
    _barra_diagnostico()

    avaliacoes = avaliacoes_do_modulo(MODULO_ID)
    respondidos = sum(1 for c in CONTROLES if avaliacoes.get(c.id, Avaliacao()).status)
    total = len(CONTROLES)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.progress(respondidos / total, text=f"Progresso: {respondidos}/{total} controles avaliados")
    with col_b:
        if st.button(
            "Ver Resultado",
            type="primary",
            disabled=respondidos == 0,
            use_container_width=True,
            key="27701_ver",
        ):
            st.session_state.page = "iso27701_dashboard"
            st.rerun()

    st.divider()

    abas = st.tabs(list(CATEGORIAS))
    for aba, (cat_id, controles) in zip(abas, CONTROLES_POR_CATEGORIA.items(), strict=True):
        with aba:
            st.markdown(f"**{cat_id}** — {CATEGORIAS[cat_id]}")
            st.caption(f"{len(controles)} controle(s)")
            with st.popover("⚡ Marcar em massa"):
                col_m1, col_m2 = st.columns([3, 1])
                with col_m1:
                    status_massa = st.selectbox(
                        "Status",
                        options=RESPOSTAS_VALIDAS,
                        key=f"27701_massa_{cat_id}",
                        label_visibility="collapsed",
                    )
                with col_m2:
                    if st.button(
                        "Aplicar",
                        key=f"27701_massa_btn_{cat_id}",
                        use_container_width=True,
                    ):
                        for c in controles:
                            a = avaliacoes.get(c.id, Avaliacao())
                            a.status = status_massa
                            avaliacoes[c.id] = a
                        st.rerun()

            for controle in controles:
                atual = avaliacoes.get(controle.id, Avaliacao())
                nova = render_item_card(controle, atual)
                if nova != atual:
                    if not nova.status and not nova.observacao and not nova.responsavel and not nova.prazo and not nova.evidencias:
                        avaliacoes.pop(controle.id, None)
                    else:
                        avaliacoes[controle.id] = nova

    _render_sidebar(respondidos)


def render_dashboard() -> None:
    """Stub temporário — implementação real no commit seguinte."""
    st.title(f"📊 {MODULO_NOME} — Resultado")
    st.info("Dashboard em construção. Volte em breve.")
    _render_sidebar(0)
