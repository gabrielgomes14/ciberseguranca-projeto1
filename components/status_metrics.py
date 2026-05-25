import streamlit as st

from core.scoring import ResultadoTema


def render_status_metrics(resumos: dict[str, ResultadoTema], label_itens: str = "itens") -> None:
    total = sum(r.total for r in resumos.values())
    conformes = sum(r.conformes for r in resumos.values())
    em_adequacao = sum(r.em_adequacao for r in resumos.values())
    nao_conformes = sum(r.nao_conformes for r in resumos.values())
    na = sum(r.na for r in resumos.values())
    nao_avaliado = total - (conformes + em_adequacao + nao_conformes + na)
    base_calc = conformes + em_adequacao + nao_conformes

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🟢 Conforme", conformes)
    col2.metric("🟡 Em Adequação", em_adequacao)
    col3.metric("🔴 Não Conforme", nao_conformes)
    col4.metric("⚪ Não Aplicável", na, help="Excluído do cálculo do score (denominador)")
    col5.metric("⚫ Não avaliado", nao_avaliado, help="Ainda sem resposta - também fora do cálculo")

    st.caption(
        f"**Base do cálculo:** {base_calc} de {total} {label_itens} avaliados "
        f"(Conformes + Em Adequação + Não Conformes). "
        f"Os **{na} {label_itens} N/A** e os **{nao_avaliado} não avaliados** "
        f"não entram no denominador do score."
    )
