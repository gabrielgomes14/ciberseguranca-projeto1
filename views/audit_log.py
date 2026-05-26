"""Tela de visualização da trilha de auditoria.

Lista os eventos registrados no `audit_log` em ordem cronológica reversa,
com filtros por ação, tipo de alvo e período. Cumpre o controle 8.15
(Logging) da ISO/IEC 27001:2022 ao tornar visíveis as ações relevantes
realizadas no sistema.
"""

import json
from datetime import date, datetime, timedelta

import streamlit as st

from core.audit import Acao
from core.db import EventoAuditoria, listar_eventos


def _formatar_quando(quando: str) -> str:
    """Converte ISO 8601 em DD/MM/YYYY HH:MM:SS - mantém data/hora local legível."""
    try:
        return datetime.fromisoformat(quando).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return quando


def _formatar_detalhes(detalhes: dict[str, object]) -> str:
    """Renderiza o JSON de detalhes em uma única linha legível."""
    if not detalhes:
        return "-"
    partes: list[str] = []
    for k, v in detalhes.items():
        if isinstance(v, dict):
            v_str = json.dumps(v, ensure_ascii=False)
        else:
            v_str = str(v)
        partes.append(f"{k}={v_str}")
    return " · ".join(partes)


def _acoes_disponiveis() -> list[str]:
    """Retorna a lista de ações conhecidas em Acao, ordenadas alfabeticamente."""
    return sorted(
        v for k, v in vars(Acao).items() if not k.startswith("_") and isinstance(v, str)
    )


def render() -> None:
    st.title("Trilha de Auditoria")
    st.caption(
        "Registros das ações realizadas no sistema. Esta trilha implementa o controle "
        "8.15 (Logging) da ABNT NBR ISO/IEC 27001:2022."
    )

    with st.container(border=True):
        st.markdown("**Filtros**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            acao = st.selectbox(
                "Ação",
                options=["(todas)", *_acoes_disponiveis()],
                key="audit_filtro_acao",
            )
        with col_b:
            desde = st.date_input(
                "De",
                value=date.today() - timedelta(days=30),
                key="audit_filtro_desde",
                format="DD/MM/YYYY",
            )
        with col_c:
            ate = st.date_input(
                "Até",
                value=date.today(),
                key="audit_filtro_ate",
                format="DD/MM/YYYY",
            )

    eventos: list[EventoAuditoria] = listar_eventos(
        acao=None if acao == "(todas)" else acao,
        desde=desde.isoformat() + "T00:00:00",
        ate=ate.isoformat() + "T23:59:59",
        limite=500,
    )

    if not eventos:
        st.info("Nenhum evento encontrado para os filtros selecionados.")
        if st.button("Voltar para a Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    st.caption(f"{len(eventos)} evento(s) - mais recente primeiro (limite 500).")

    linhas = [
        {
            "Quando": _formatar_quando(e.quando),
            "Usuário": e.usuario_email or "-",
            "Ação": e.acao,
            "Alvo": f"{e.alvo_tipo}#{e.alvo_id}" if e.alvo_tipo and e.alvo_id else "-",
            "Detalhes": _formatar_detalhes(e.detalhes),
        }
        for e in eventos
    ]
    st.dataframe(linhas, hide_index=True, width="stretch")

    if st.button("Voltar para a Home"):
        st.session_state.page = "home"
        st.rerun()
