import streamlit as st

from core.db import listar_diagnosticos
from core.types import ModuloInfo

MODULOS: list[ModuloInfo] = [
    ModuloInfo(
        id="iso27001",
        nome="ISO/IEC 27001:2022",
        norma="SGSI — Requisitos",
        descricao="Cláusulas 4 a 10 do Sistema de Gestão da Segurança da Informação. Use a 27002 para avaliar a aplicabilidade dos controles do Anexo A.",
        icone="🏛️",
    ),
    ModuloInfo(
        id="iso27002",
        nome="ISO/IEC 27002:2022",
        norma="Controles de Segurança",
        descricao="93 controles distribuídos em 4 temas (organizacionais, pessoas, físicos, tecnológicos). Suporta o diagnóstico do Anexo A da 27001.",
        icone="🛡️",
    ),
    ModuloInfo(
        id="iso27701",
        nome="ISO/IEC 27701:2019",
        norma="Privacidade — Extensão do SGSI",
        descricao="Controles adicionais para gestão de informações de privacidade (SGPI) — Anexo A (Controladores) e Anexo B (Operadores) com mapeamento à LGPD.",
        icone="🔒",
    ),
]


def _abrir_modulo(modulo_id: str) -> None:
    st.session_state.modulo_ativo = modulo_id
    st.session_state.modulo_alvo = modulo_id
    st.session_state.page = "diagnosticos"
    st.rerun()


def render() -> None:
    st.title("🛡️ Diagnóstico de Conformidade — Família ISO/IEC 27000")
    st.markdown(
        "Ferramenta para diagnóstico de conformidade com as normas **27001**, **27002** e **27701**. "
        "Dados persistidos em SQLite local — você pode manter múltiplos diagnósticos comparáveis no tempo."
    )
    st.divider()

    st.subheader("Selecionar módulo")
    cols = st.columns(len(MODULOS))
    for col, modulo in zip(cols, MODULOS, strict=True):
        with col, st.container(border=True):
            st.markdown(f"### {modulo.icone} {modulo.nome}")
            st.caption(modulo.norma)
            st.write(modulo.descricao)
            diags = listar_diagnosticos(modulo.id)
            if diags:
                st.success(f"{len(diags)} diagnóstico(s) salvo(s)")
            else:
                st.info("Nenhum diagnóstico ainda")
            disponivel = modulo.id in {"iso27001", "iso27002", "iso27701"}
            if st.button(
                "Abrir módulo" if disponivel else "Em breve",
                key=f"abrir_{modulo.id}",
                use_container_width=True,
                type="primary" if disponivel else "secondary",
                disabled=not disponivel,
            ):
                _abrir_modulo(modulo.id)

    st.divider()
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        if st.button("📈 Ver histórico", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
    with col_h2:
        total = sum(len(listar_diagnosticos(m.id)) for m in MODULOS)
        st.metric("Diagnósticos totais", total)
