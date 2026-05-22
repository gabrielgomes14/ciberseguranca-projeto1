import pandas as pd
import streamlit as st

from components.generic_item_card import render_item_card
from components.score_gauge import render_bar_temas, render_gauge, render_radar
from components.status_metrics import render_status_metrics
from components.theme_summary import render_theme_summary
from core.db import listar_diagnosticos, salvar_snapshot
from core.models import Avaliacao
from core.pdf_report import gerar_pdf_27701
from core.scoring import RESPOSTAS_SELECIONAVEIS, resumo_tema, score_geral, status_label
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
            width="stretch",
            disabled=ativo_id is None,
            key="27701_salvar",
        ):
            if persistir(MODULO_ID):
                st.toast("Salvo.", icon="💾")
    with col_d3:
        if st.button("📁 Diagnósticos", width="stretch", key="27701_lista"):
            st.session_state.modulo_alvo = MODULO_ID
            st.session_state.page = "diagnosticos"
            st.rerun()


def _render_sidebar(respondidos: int) -> None:
    """Sidebar de navegação do módulo. `respondidos` desabilita 'Resultado' quando 0."""
    with st.sidebar:
        st.markdown(f"### {MODULO_NOME}")
        if st.button("🏠 Início", width="stretch", key="27701_nav_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📋 Avaliar", width="stretch", key="27701_nav_assess"):
            st.session_state.page = "iso27701_assessment"
            st.rerun()
        if st.button(
            "📊 Resultado",
            width="stretch",
            disabled=respondidos == 0,
            key="27701_nav_dash",
        ):
            st.session_state.page = "iso27701_dashboard"
            st.rerun()
        if st.button("📈 Histórico", width="stretch", key="27701_nav_hist"):
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
            width="stretch",
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
                        options=RESPOSTAS_SELECIONAVEIS,
                        key=f"27701_massa_{cat_id}",
                        label_visibility="collapsed",
                    )
                with col_m2:
                    if st.button(
                        "Aplicar",
                        key=f"27701_massa_btn_{cat_id}",
                        width="stretch",
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
    """Tela de resultado do módulo: gauge geral, radar, métricas, resumo por categoria,
    tabela de controles, export PDF e captura de snapshot.
    """
    st.title(f"📊 {MODULO_NOME} — Resultado")
    _barra_diagnostico()
    avaliacoes = avaliacoes_do_modulo(MODULO_ID)

    ponderado = st.toggle(
        "Pontuação ponderada por criticidade",
        value=st.session_state.get("27701_ponderado", True),
        key="27701_ponderado",
    )

    todos_ids = [c.id for c in CONTROLES]
    score_total = score_geral(avaliacoes, todos_ids, ponderado=ponderado)
    resumos = {
        cat: resumo_tema(avaliacoes, cat, [c.id for c in controles], ponderado=ponderado)
        for cat, controles in CONTROLES_POR_CATEGORIA.items()
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        render_gauge(score_total, "Score Geral SGPI")
        st.markdown(f"**Classificação:** {status_label(score_total)}")
    with col2:
        labels = list(CATEGORIAS.keys())
        scores = [resumos[c].score for c in CATEGORIAS]
        render_radar(labels, scores)

    st.divider()
    st.subheader("Distribuição dos status")
    render_status_metrics(resumos, "controles")

    st.divider()
    st.subheader("Resumo por categoria")
    cols = st.columns(min(len(CATEGORIAS), 4))
    for idx, cat_id in enumerate(CATEGORIAS):
        with cols[idx % len(cols)]:
            r = resumos[cat_id]
            render_theme_summary(f"{cat_id}", r.score, r.conformes, r.total)

    st.divider()
    render_bar_temas(
        list(CATEGORIAS.keys()),
        [resumos[c].score for c in CATEGORIAS],
    )

    st.divider()
    linhas: list[dict[str, object]] = []
    for c in CONTROLES:
        a = avaliacoes.get(c.id, Avaliacao())
        linhas.append(
            {
                "Controle": c.id,
                "Categoria": c.categoria_id,
                "Título": c.titulo,
                "Status": a.status or "Não avaliado",
                "Responsável": a.responsavel,
                "Prazo": a.prazo,
            }
        )
    st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True)

    st.divider()
    st.subheader("📥 Exportar")
    diag_id_atual = diagnostico_ativo(MODULO_ID)
    diags_27701 = listar_diagnosticos(MODULO_ID)
    diag_obj = next((d for d in diags_27701 if d.id == diag_id_atual), None)
    organizacao = diag_obj.organizacao if diag_obj else "Organização"
    data_aud = diag_obj.data_auditoria if diag_obj else ""
    st.download_button(
        "📄 PDF completo (27701)",
        data=gerar_pdf_27701(
            CONTROLES,
            CATEGORIAS,
            CONTROLES_POR_CATEGORIA,
            avaliacoes,
            organizacao=organizacao,
            ponderado=ponderado,
            data_auditoria=data_aud,
        ),
        file_name="relatorio_iso27701.pdf",
        mime="application/pdf",
        width="stretch",
    )

    st.divider()
    diag_id = diagnostico_ativo(MODULO_ID)
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        rotulo = st.text_input("Rótulo do snapshot", value="", key="27701_rotulo")
    with col_s2:
        st.write("")
        st.write("")
        if st.button(
            "📈 Salvar snapshot",
            width="stretch",
            disabled=diag_id is None,
            key="27701_snap",
        ):
            if diag_id is not None:
                persistir(MODULO_ID)
                avaliados_n = sum(1 for c in CONTROLES if avaliacoes.get(c.id, Avaliacao()).status)
                salvar_snapshot(
                    diag_id,
                    rotulo,
                    score_total,
                    {cat: resumos[cat].score for cat in CATEGORIAS},
                    avaliados_n,
                )
                st.toast("Snapshot salvo.", icon="📈")

    _render_sidebar(sum(1 for c in CONTROLES if avaliacoes.get(c.id, Avaliacao()).status))
