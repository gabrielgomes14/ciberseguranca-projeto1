import streamlit as st

from components.control_card import render_control_card
from core.db import listar_diagnosticos
from core.models import Avaliacao
from core.scoring import RESPOSTA_NAO_AVALIADO, RESPOSTAS_SELECIONAVEIS
from core.state import avaliacoes_do_modulo, diagnostico_ativo, limpar_modulo, persistir
from modulos.iso27001.controls import TEMA_LABELS, TEMAS, TODOS_CONTROLES, Controle


def _filtrar(controles: list[Controle], avaliacoes: dict[str, Avaliacao], busca: str, status_filtros: list[str]) -> list[Controle]:
    busca_norm = busca.strip().lower()
    resultado: list[Controle] = []
    for c in controles:
        if busca_norm and busca_norm not in c.id.lower() and busca_norm not in c.titulo.lower() and busca_norm not in c.descricao.lower():
            continue
        if status_filtros:
            atual = avaliacoes.get(c.id, Avaliacao()).status or RESPOSTA_NAO_AVALIADO
            if atual not in status_filtros:
                continue
        resultado.append(c)
    return resultado


def _aplicar_em_massa(avaliacoes: dict[str, Avaliacao], ids: list[str], status: str) -> None:
    for cid in ids:
        atual = avaliacoes.get(cid, Avaliacao())
        atual.status = status
        avaliacoes[cid] = atual


def _barra_diagnostico() -> None:
    ativo_id = diagnostico_ativo("iso27001")
    diags = listar_diagnosticos("iso27001")
    diag_atual = next((d for d in diags if d.id == ativo_id), None)
    col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
    with col_d1:
        if diag_atual:
            st.info(f"Diagnóstico ativo: **{diag_atual.organizacao}** · ID #{ativo_id} · 📅 {diag_atual.data_auditoria}")
        else:
            st.warning("Nenhum diagnóstico ativo. Suas respostas não serão salvas. Selecione/crie um diagnóstico.")
    with col_d2:
        if st.button("💾 Salvar", width="stretch", disabled=ativo_id is None):
            if persistir("iso27001"):
                st.toast("Diagnóstico salvo no banco.", icon="💾")
    with col_d3:
        if st.button("📁 Diagnósticos", width="stretch"):
            st.session_state.modulo_alvo = "iso27001"
            st.session_state.page = "diagnosticos"
            st.rerun()


def render() -> None:
    st.title("📋 ISO/IEC 27001 - Avaliação dos Controles")
    _barra_diagnostico()

    avaliacoes = avaliacoes_do_modulo("iso27001")
    respondidos = sum(1 for c in TODOS_CONTROLES if avaliacoes.get(c.id, Avaliacao()).status)
    total = len(TODOS_CONTROLES)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.progress(respondidos / total, text=f"Progresso: {respondidos}/{total} controles avaliados")
    with col_b:
        if st.button("Ver Resultado", type="primary", disabled=respondidos == 0, width="stretch"):
            st.session_state.page = "iso27001_dashboard"
            st.rerun()

    with st.expander("🔎 Buscar e filtrar"):
        col_b1, col_b2 = st.columns([2, 3])
        with col_b1:
            busca = st.text_input("Busca por ID, título ou descrição", value=st.session_state.get("busca", ""), key="busca")
        with col_b2:
            opcoes_status = list(RESPOSTAS_SELECIONAVEIS) + [RESPOSTA_NAO_AVALIADO]
            status_filtros = st.multiselect("Filtrar por status atual", opcoes_status, default=[])

    st.divider()

    abas = st.tabs([TEMA_LABELS[t] for t in TEMAS])
    for aba, (tema_id, controles) in zip(abas, TEMAS.items(), strict=True):
        with aba:
            controles_filtrados = _filtrar(controles, avaliacoes, busca, status_filtros)
            st.caption(f"{len(controles_filtrados)} de {len(controles)} controles · {TEMA_LABELS[tema_id]}")

            with st.popover("⚡ Marcar em massa neste tema"):
                ids_filtrados = [c.id for c in controles_filtrados]
                st.write(f"Aplicar status a **{len(ids_filtrados)}** controles visíveis.")
                col_m1, col_m2 = st.columns([3, 1])
                with col_m1:
                    status_massa = st.selectbox(
                        "Status",
                        options=RESPOSTAS_SELECIONAVEIS,
                        key=f"massa_status_{tema_id}",
                        label_visibility="collapsed",
                    )
                with col_m2:
                    if st.button("Aplicar", key=f"massa_btn_{tema_id}", width="stretch", disabled=not ids_filtrados):
                        _aplicar_em_massa(avaliacoes, ids_filtrados, status_massa)
                        st.rerun()

            if not controles_filtrados:
                st.info("Nenhum controle corresponde aos filtros.")
                continue

            for controle in controles_filtrados:
                atual = avaliacoes.get(controle.id, Avaliacao())
                nova = render_control_card(controle, atual)
                if nova != atual:
                    if not nova.status and not nova.observacao and not nova.responsavel and not nova.prazo and not nova.evidencias:
                        avaliacoes.pop(controle.id, None)
                    else:
                        avaliacoes[controle.id] = nova

    with st.sidebar:
        st.markdown("### ISO/IEC 27001:2022")
        if st.button("🏠 Início", width="stretch"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📊 Resultado", width="stretch", disabled=respondidos == 0):
            st.session_state.page = "iso27001_dashboard"
            st.rerun()
        if st.button("📌 Plano de ação", width="stretch", disabled=respondidos == 0):
            st.session_state.page = "iso27001_action_plan"
            st.rerun()
        if st.button("📈 Histórico", width="stretch"):
            st.session_state.page = "history"
            st.rerun()
        st.divider()
        if st.button("Limpar avaliações", width="stretch"):
            limpar_modulo("iso27001")
            st.rerun()
