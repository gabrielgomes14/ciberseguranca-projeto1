import streamlit as st

from core.db import (
    carregar_avaliacoes,
    init_db,
    salvar_avaliacoes,
)
from core.models import Avaliacao


def inicializar_estado() -> None:
    init_db()
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "avaliacoes_por_modulo" not in st.session_state:
        st.session_state.avaliacoes_por_modulo = {}
    if "diagnostico_ativo" not in st.session_state:
        st.session_state.diagnostico_ativo = {}
    if "modulo_ativo" not in st.session_state:
        st.session_state.modulo_ativo = None


def avaliacoes_do_modulo(modulo_id: str) -> dict[str, Avaliacao]:
    bag: dict[str, dict[str, Avaliacao]] = st.session_state.avaliacoes_por_modulo
    if modulo_id not in bag:
        bag[modulo_id] = {}
    return bag[modulo_id]


def limpar_modulo(modulo_id: str) -> None:
    st.session_state.avaliacoes_por_modulo[modulo_id] = {}


def diagnostico_ativo(modulo_id: str) -> int | None:
    val = st.session_state.diagnostico_ativo.get(modulo_id)
    return int(val) if val is not None else None


def definir_diagnostico_ativo(modulo_id: str, diagnostico_id: int) -> None:
    st.session_state.diagnostico_ativo[modulo_id] = diagnostico_id
    st.session_state.avaliacoes_por_modulo[modulo_id] = carregar_avaliacoes(diagnostico_id)


def desativar_diagnostico(modulo_id: str) -> None:
    st.session_state.diagnostico_ativo.pop(modulo_id, None)
    st.session_state.avaliacoes_por_modulo[modulo_id] = {}


def persistir(modulo_id: str) -> bool:
    diag_id = diagnostico_ativo(modulo_id)
    if diag_id is None:
        return False
    salvar_avaliacoes(diag_id, avaliacoes_do_modulo(modulo_id))
    return True
