from datetime import date, datetime

import streamlit as st

from core.db import (
    atualizar_diagnostico,
    criar_diagnostico,
    excluir_diagnostico,
    listar_diagnosticos,
)
from core.state import (
    definir_diagnostico_ativo,
    diagnostico_ativo,
    persistir,
)

_MODULOS = {
    "iso27002": ("ISO/IEC 27002:2022", "iso27002_assessment"),
    "iso27701": ("ISO/IEC 27701:2026", "iso27701_assessment"),
}


def _parse_data(s: str) -> date | None:
    try:
        return datetime.fromisoformat(s).date() if s else None
    except (TypeError, ValueError):
        return None


def render() -> None:
    modulo_id = st.session_state.get("modulo_alvo") or "iso27002"
    nome, rota_abrir = _MODULOS.get(modulo_id, _MODULOS["iso27002"])

    st.title(f"📁 Diagnósticos — {nome}")
    st.caption("Cada diagnóstico é uma auditoria independente, persistida em SQLite local.")

    with st.container(border=True):
        st.markdown("**➕ Novo diagnóstico**")
        col_a, col_b, col_c = st.columns([3, 2, 1])
        with col_a:
            nova_org = st.text_input(
                "Nome da empresa",
                placeholder="Ex.: Acme Ltda.",
                key="nova_org",
            )
        with col_b:
            nova_data = st.date_input(
                "Data da auditoria",
                value=date.today(),
                key="nova_data",
                format="DD/MM/YYYY",
            )
        with col_c:
            st.write("")
            st.write("")
            criar_disabled = not nova_org.strip()
            if st.button("Criar", type="primary", width="stretch", disabled=criar_disabled):
                novo_id = criar_diagnostico(modulo_id, nova_org.strip(), nova_data.isoformat())
                definir_diagnostico_ativo(modulo_id, novo_id)
                st.session_state.page = rota_abrir
                st.rerun()

    st.divider()

    diagnosticos = listar_diagnosticos(modulo_id)
    if not diagnosticos:
        st.info("Nenhum diagnóstico criado para este módulo. Use o formulário acima.")
    else:
        st.subheader(f"{len(diagnosticos)} diagnóstico(s) salvo(s)")
        ativo = diagnostico_ativo(modulo_id)
        for d in diagnosticos:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([4, 3, 1.5, 1.5])
                with col1:
                    marca = "🟢 " if d.id == ativo else ""
                    st.markdown(f"**{marca}{d.organizacao}**")
                    st.caption(f"ID #{d.id} · criado em {d.criado_em}")
                with col2:
                    data_atual = _parse_data(d.data_auditoria) or date.today()
                    nova = st.date_input(
                        "Data da auditoria",
                        value=data_atual,
                        key=f"data_{d.id}",
                        format="DD/MM/YYYY",
                        label_visibility="collapsed",
                    )
                    if nova and nova.isoformat() != d.data_auditoria:
                        atualizar_diagnostico(d.id, d.organizacao, nova.isoformat())
                        st.rerun()
                    st.caption(f"📅 Auditoria: {nova.strftime('%d/%m/%Y') if nova else '—'}")
                with col3:
                    if st.button("Abrir", key=f"abrir_{d.id}", width="stretch"):
                        if ativo and ativo != d.id:
                            persistir(modulo_id)
                        definir_diagnostico_ativo(modulo_id, d.id)
                        st.session_state.page = rota_abrir
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_{d.id}", width="stretch", help="Excluir"):
                        excluir_diagnostico(d.id)
                        if ativo == d.id:
                            st.session_state.diagnostico_ativo.pop(modulo_id, None)
                            st.session_state.avaliacoes_por_modulo[modulo_id] = {}
                        st.rerun()

    st.divider()
    if st.button("← Voltar ao início"):
        st.session_state.page = "home"
        st.rerun()
