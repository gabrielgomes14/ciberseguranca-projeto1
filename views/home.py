import streamlit as st

from core import auth
from core.db import listar_diagnosticos
from core.types import ModuloInfo

MODULOS: list[ModuloInfo] = [
    ModuloInfo(
        id="iso27001",
        nome="ISO/IEC 27001:2022",
        norma="Controles de Segurança da Informação",
        descricao="93 controles distribuídos em 4 temas (organizacionais, pessoas, físicos, tecnológicos).",
    ),
    ModuloInfo(
        id="iso27701",
        nome="ISO/IEC 27701:2026",
        norma="SGPI - Sistema de Gestão de Privacidade da Informação",
        descricao="Anexo A da norma ABNT NBR ISO/IEC 27701:2026 - controles para controladores (A.1), operadores (A.2) e segurança da informação aplicada a DP (A.3). Vinculado à LGPD.",
    ),
]

def _abrir_modulo(modulo_id: str) -> None:
    st.session_state.modulo_ativo = modulo_id
    st.session_state.modulo_alvo = modulo_id
    st.session_state.page = "diagnosticos"
    st.rerun()

def render() -> None:
    st.title("Diagnóstico de Conformidade - ISO/IEC 27001 e 27701")
    st.markdown(
        "Ferramenta para diagnóstico de conformidade com as normas **27001** (segurança da informação) "
        "e **27701** (privacidade da informação, com mapeamento à LGPD). "
        "Dados persistidos em SQLite local - você pode manter múltiplos diagnósticos comparáveis no tempo."
    )
    st.divider()

    st.subheader("Selecionar módulo")
    cols = st.columns(len(MODULOS))
    for col, modulo in zip(cols, MODULOS, strict=True):
        with col, st.container(border=True):
            st.markdown(f"### {modulo.nome}")
            st.caption(modulo.norma)
            st.write(modulo.descricao)
            diags = listar_diagnosticos(modulo.id, usuario_email=auth.usuario_logado_email())
            if diags:
                st.success(f"{len(diags)} diagnóstico(s) salvo(s)")
            else:
                st.info("Nenhum diagnóstico ainda")
            disponivel = modulo.id in {"iso27001", "iso27701"}
            if st.button(
                "Abrir módulo" if disponivel else "Em breve",
                key=f"abrir_{modulo.id}",
                width="stretch",
                type="primary" if disponivel else "secondary",
                disabled=not disponivel,
            ):
                _abrir_modulo(modulo.id)

    st.divider()
    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        if st.button("Ver histórico", width="stretch"):
            st.session_state.page = "history"
            st.rerun()
    with col_h2:
        if st.button("Trilha de auditoria", width="stretch"):
            st.session_state.page = "audit_log"
            st.rerun()
    with col_h3:
        total = sum(
            len(listar_diagnosticos(m.id, usuario_email=auth.usuario_logado_email()))
            for m in MODULOS
        )
        st.metric("Diagnósticos totais", total)
