import streamlit as st

from core.models import (
    CRITICIDADE_MEDIA,
    CRITICIDADES,
    REMEDIACAO_OPCOES,
    Avaliacao,
)
from core.scoring import RESPOSTA_NAO_AVALIADO, RESPOSTA_NAO_CONFORME, RESPOSTAS_VALIDAS, STATUS_COLORS
from modulos.iso27002.controls import Controle
from modulos.iso27002.guidance import GUIDANCE
from modulos.iso27002.mappings import MAPEAMENTOS


def _render_referencias(controle_id: str) -> None:
    mapeamento = MAPEAMENTOS.get(controle_id)
    if mapeamento is None:
        return
    pares: list[tuple[str, list[str]]] = [
        ("NIST CSF 2.0", mapeamento.nist_csf),
        ("CIS Controls v8", mapeamento.cis_v8),
        ("LGPD", mapeamento.lgpd),
    ]
    pares_validos = [(label, refs) for label, refs in pares if refs]
    if not pares_validos:
        return
    chunks = []
    for label, refs in pares_validos:
        chunks.append(f"**{label}:** {', '.join(refs)}")
    st.caption(" · ".join(chunks))


def render_control_card(controle: Controle, avaliacao: Avaliacao) -> Avaliacao:
    status_atual = avaliacao.status
    cor = STATUS_COLORS.get(status_atual or RESPOSTA_NAO_AVALIADO, STATUS_COLORS[RESPOSTA_NAO_AVALIADO])
    with st.container(border=True):
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
            f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{cor};'></span>"
            f"<strong style='color:#0f172a;'>{controle.id} — {controle.titulo}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(controle.descricao)

        opcoes = ("",) + RESPOSTAS_VALIDAS
        try:
            index = opcoes.index(status_atual)
        except ValueError:
            index = 0
        novo_status = st.radio(
            "Avaliação",
            options=opcoes,
            index=index,
            horizontal=True,
            key=f"radio_{controle.id}",
            format_func=lambda v: "— selecione —" if v == "" else v,
            label_visibility="collapsed",
        )

        with st.expander("Detalhes, orientação e plano"):
            st.markdown("**Orientação da norma**")
            st.write(GUIDANCE.get(controle.id, "Sem orientação cadastrada."))
            _render_referencias(controle.id)

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                criticidade_atual = avaliacao.criticidade if avaliacao.criticidade in CRITICIDADES else CRITICIDADE_MEDIA
                nova_criticidade = st.selectbox(
                    "Criticidade para o negócio",
                    options=CRITICIDADES,
                    index=CRITICIDADES.index(criticidade_atual),
                    key=f"crit_{controle.id}",
                    help="Define o peso do controle no cálculo do score ponderado.",
                )
                novo_responsavel = st.text_input(
                    "Responsável",
                    value=avaliacao.responsavel,
                    key=f"resp_{controle.id}",
                    placeholder="Ex.: Equipe SecOps",
                )
            with col2:
                novo_prazo = st.text_input(
                    "Prazo de adequação",
                    value=avaliacao.prazo,
                    key=f"prazo_{controle.id}",
                    placeholder="AAAA-MM-DD",
                )
                evid_input = st.text_input(
                    "Evidências (separe por ;)",
                    value="; ".join(avaliacao.evidencias),
                    key=f"evid_{controle.id}",
                    placeholder="Ex.: politica.pdf; relatorio_audit.docx",
                )
            nova_observacao = st.text_area(
                "Observações / Justificativa",
                value=avaliacao.observacao,
                key=f"obs_{controle.id}",
                height=80,
                placeholder="Notas, lacunas identificadas, decisões.",
            )

            nova_remediacao = avaliacao.remediacao
            if novo_status == RESPOSTA_NAO_CONFORME:
                st.markdown("**🔧 Há remediação em andamento?**")
                opcoes_rem = ("",) + REMEDIACAO_OPCOES
                idx_rem = opcoes_rem.index(avaliacao.remediacao) if avaliacao.remediacao in opcoes_rem else 0
                nova_remediacao = st.radio(
                    "Remediação em andamento",
                    options=opcoes_rem,
                    index=idx_rem,
                    horizontal=True,
                    key=f"rem_{controle.id}",
                    format_func=lambda v: "— selecione —" if v == "" else v,
                    label_visibility="collapsed",
                )

    evidencias = [e.strip() for e in evid_input.split(";") if e.strip()]
    return Avaliacao(
        status=novo_status,
        observacao=nova_observacao,
        criticidade=nova_criticidade,
        responsavel=novo_responsavel,
        prazo=novo_prazo,
        remediacao=nova_remediacao if novo_status == RESPOSTA_NAO_CONFORME else "",
        evidencias=evidencias,
    )
