import pandas as pd
import streamlit as st

from core.action_plan import gerar_plano, plano_para_csv
from core.models import Avaliacao
from core.state import avaliacoes_do_modulo
from modulos.iso27002.controls import TODOS_CONTROLES


def render() -> None:
    st.title("📌 Plano de Ação")
    st.caption("Gerado a partir dos controles avaliados como Não Conforme ou Parcial.")

    avaliacoes: dict[str, Avaliacao] = avaliacoes_do_modulo("iso27002")
    acoes = gerar_plano(TODOS_CONTROLES, avaliacoes)

    if not acoes:
        st.success("Nenhuma ação pendente. Todos os controles avaliados estão conformes ou marcados como N/A.")
        return

    col_a, col_b, col_c, col_d = st.columns(4)
    contagem = {"Crítica": 0, "Alta": 0, "Média": 0, "Baixa": 0}
    for a in acoes:
        contagem[a.prioridade] = contagem.get(a.prioridade, 0) + 1
    col_a.metric("🔴 Críticas", contagem.get("Crítica", 0))
    col_b.metric("🟠 Altas", contagem.get("Alta", 0))
    col_c.metric("🟡 Médias", contagem.get("Média", 0))
    col_d.metric("🟢 Baixas", contagem.get("Baixa", 0))

    st.divider()

    df = pd.DataFrame([
        {
            "Controle": a.controle_id,
            "Tema": a.tema,
            "Título": a.titulo,
            "Status": a.status,
            "Criticidade": a.criticidade,
            "Prioridade": a.prioridade,
            "Responsável": a.responsavel,
            "Prazo": a.prazo,
            "Observação": a.observacao,
        }
        for a in acoes
    ])

    prioridades = st.multiselect("Filtrar por prioridade", sorted(df["Prioridade"].unique()), default=list(df["Prioridade"].unique()))
    df_filt = df[df["Prioridade"].isin(prioridades)]

    st.dataframe(
        df_filt,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Observação": st.column_config.TextColumn(width="large"),
            "Título": st.column_config.TextColumn(width="medium"),
        },
    )

    st.info("💡 Para editar **Responsável**, **Prazo** ou **Observação** de cada ação, volte à página de Avaliação e expanda o controle.")

    st.divider()
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.download_button(
            "⬇️ Exportar plano CSV",
            data=plano_para_csv(acoes),
            file_name="plano_de_acao_iso27002.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_e2:
        if st.button("← Voltar ao resultado", use_container_width=True):
            st.session_state.page = "iso27002_dashboard"
            st.rerun()

    with st.sidebar:
        st.markdown("### ISO/IEC 27002:2022")
        if st.button("🏠 Início", use_container_width=True, key="ap_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📋 Avaliação", use_container_width=True, key="ap_assess"):
            st.session_state.page = "iso27002_assessment"
            st.rerun()
        if st.button("📊 Resultado", use_container_width=True, key="ap_dash"):
            st.session_state.page = "iso27002_dashboard"
            st.rerun()