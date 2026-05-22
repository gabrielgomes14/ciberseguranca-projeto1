import pandas as pd
import streamlit as st
from core.pdf_report import gerar_pdf

from components.score_gauge import render_bar_temas, render_gauge, render_radar
from components.status_metrics import render_status_metrics
from components.theme_summary import render_theme_summary
from core.action_plan import gerar_plano
from core.db import listar_diagnosticos, salvar_snapshot
from core.export import gerar_csv, montar_linhas
from core.scoring import resumo_tema, score_geral, status_label
from core.state import avaliacoes_do_modulo, diagnostico_ativo, persistir
from modulos.iso27002.controls import TEMA_LABELS, TEMAS, TODOS_CONTROLES


def _barra_diagnostico() -> None:
    ativo_id = diagnostico_ativo("iso27002")
    diags = listar_diagnosticos("iso27002")
    diag_atual = next((d for d in diags if d.id == ativo_id), None)
    col_d1, col_d2 = st.columns([4, 1])
    with col_d1:
        if diag_atual:
            st.info(f"Diagnóstico ativo: **{diag_atual.organizacao}** · ID #{ativo_id} · 📅 {diag_atual.data_auditoria}")
        else:
            st.warning("Nenhum diagnóstico ativo. Selecione/crie um para persistir.")
    with col_d2:
        if st.button("💾 Salvar", use_container_width=True, disabled=ativo_id is None, key="dash_salvar"):
            if persistir("iso27002"):
                st.toast("Salvo.", icon="💾")


def render() -> None:
    st.title("📊 ISO/IEC 27002 — Resultado")
    _barra_diagnostico()
    avaliacoes = avaliacoes_do_modulo("iso27002")

    ponderado = st.toggle(
        "Pontuação ponderada por criticidade",
        value=st.session_state.get("ponderado", True),
        key="ponderado",
        help="Quando ativo, controles 'Alta' pesam 3x e 'Baixa' 1x.",
    )

    todos_ids = [c.id for c in TODOS_CONTROLES]
    score_total = score_geral(avaliacoes, todos_ids, ponderado=ponderado)
    resumos = {
        tema_id: resumo_tema(avaliacoes, tema_id, [c.id for c in controles], ponderado=ponderado)
        for tema_id, controles in TEMAS.items()
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        render_gauge(score_total, "Score Geral")
        st.markdown(f"**Classificação:** {status_label(score_total)}")
    with col2:
        labels = [TEMA_LABELS[t] for t in TEMAS]
        scores = [resumos[t].score for t in TEMAS]
        render_radar(labels, scores)

    st.divider()
    st.subheader("Distribuição dos status")
    render_status_metrics(resumos, "controles")

    st.divider()
    st.subheader("Resumo por tema")
    cols = st.columns(len(TEMAS))
    for col, tema_id in zip(cols, TEMAS, strict=True):
        with col:
            r = resumos[tema_id]
            render_theme_summary(TEMA_LABELS[tema_id], r.score, r.conformes, r.total)

    st.divider()
    st.subheader("Comparativo entre temas")
    render_bar_temas(
        [TEMA_LABELS[t] for t in TEMAS],
        [resumos[t].score for t in TEMAS],
    )

    st.divider()
    st.subheader("Detalhamento por controle")
    linhas = montar_linhas(TODOS_CONTROLES, avaliacoes)
    df = pd.DataFrame([
        {
            "Controle": linha.controle_id,
            "Tema": linha.tema,
            "Título": linha.titulo,
            "Status": linha.status,
            "Criticidade": linha.criticidade,
            "Responsável": linha.responsavel,
            "Prazo": linha.prazo,
        }
        for linha in linhas
    ])
    temas_filtro = st.multiselect("Filtrar por tema", sorted(df["Tema"].unique()), default=list(df["Tema"].unique()))
    status_filtro = st.multiselect("Filtrar por status", sorted(df["Status"].unique()), default=list(df["Status"].unique()))
    df_filtrado = df[df["Tema"].isin(temas_filtro) & df["Status"].isin(status_filtro)]
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📥 Exportar")
    diag_ativo_id = diagnostico_ativo("iso27002")
    diags_lista = listar_diagnosticos("iso27002")
    diag_obj = next((d for d in diags_lista if d.id == diag_ativo_id), None)
    organizacao = diag_obj.organizacao if diag_obj else st.session_state.get("organizacao", "Organização")
    data_aud = diag_obj.data_auditoria if diag_obj else ""
    acoes = gerar_plano(TODOS_CONTROLES, avaliacoes)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            "⬇️ CSV detalhado",
            data=gerar_csv(TODOS_CONTROLES, avaliacoes),
            file_name="relatorio_iso27002.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_d2:
        st.download_button(
            "📄 PDF completo",
            data=gerar_pdf(TODOS_CONTROLES, avaliacoes, acoes, organizacao=organizacao, ponderado=ponderado, data_auditoria=data_aud),
            file_name="relatorio_iso27002.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.divider()
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        rotulo = st.text_input("Rótulo do snapshot", value="", placeholder="Ex.: baseline Q2", key="rotulo_snapshot")
    with col_s2:
        st.write("")
        st.write("")
        diag_id = diagnostico_ativo("iso27002")
        if st.button("📈 Salvar snapshot", use_container_width=True, disabled=diag_id is None):
            if diag_id is not None:
                persistir("iso27002")
                avaliados_n = sum(1 for c in TODOS_CONTROLES if avaliacoes.get(c.id))
                salvar_snapshot(
                    diag_id,
                    rotulo,
                    score_total,
                    {tema: resumos[tema].score for tema in TEMAS},
                    avaliados_n,
                )
                st.toast("Snapshot salvo no banco.", icon="📈")

    with st.sidebar:
        st.markdown("### ISO/IEC 27002:2022")
        if st.button("🏠 Início", use_container_width=True, key="nav_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("← Avaliação", use_container_width=True, key="nav_assess"):
            st.session_state.page = "iso27002_assessment"
            st.rerun()
        if st.button("📌 Plano de ação", use_container_width=True, key="nav_action"):
            st.session_state.page = "iso27002_action_plan"
            st.rerun()
        if st.button("📈 Histórico", use_container_width=True, key="nav_hist"):
            st.session_state.page = "history"
            st.rerun()
