import html

import streamlit as st

from core.models import (
    CRITICIDADE_MEDIA,
    CRITICIDADES,
    Avaliacao,
)
from core.scoring import RESPOSTA_NAO_AVALIADO, RESPOSTA_NAO_CONFORME, RESPOSTAS_VALIDAS, STATUS_COLORS
from core.types import ItemDiagnostico


def render_item_card(item: ItemDiagnostico, avaliacao: Avaliacao) -> Avaliacao:
    status_atual = avaliacao.status
    cor = STATUS_COLORS.get(status_atual or RESPOSTA_NAO_AVALIADO) or STATUS_COLORS[RESPOSTA_NAO_AVALIADO]

    with st.container(border=True):
        titulo_safe = html.escape(f"{item.id} — {item.titulo}")
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
            f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{cor};'></span>"
            f"<strong style='color:#0f172a;'>{titulo_safe}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(item.descricao)

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
            key=f"radio_{item.modulo}_{item.id}",
            format_func=lambda v: "— selecione —" if v == "" else v,
            label_visibility="collapsed",
        )

        with st.expander("Detalhes e plano"):
            col1, col2 = st.columns(2)
            with col1:
                criticidade_atual = avaliacao.criticidade if avaliacao.criticidade in CRITICIDADES else CRITICIDADE_MEDIA
                nova_criticidade = st.selectbox(
                    "Criticidade",
                    options=CRITICIDADES,
                    index=CRITICIDADES.index(criticidade_atual),
                    key=f"crit_{item.modulo}_{item.id}",
                )
                novo_responsavel = st.text_input(
                    "Responsável",
                    value=avaliacao.responsavel,
                    key=f"resp_{item.modulo}_{item.id}",
                )
            with col2:
                novo_prazo = st.text_input(
                    "Prazo",
                    value=avaliacao.prazo,
                    key=f"prazo_{item.modulo}_{item.id}",
                    placeholder="AAAA-MM-DD",
                )
                evid_input = st.text_input(
                    "Evidências (; separa)",
                    value="; ".join(avaliacao.evidencias),
                    key=f"evid_{item.modulo}_{item.id}",
                )

            nova_observacao = st.text_area(
                "Observação",
                value=avaliacao.observacao,
                key=f"obs_{item.modulo}_{item.id}",
                height=68,
            )

            nova_remediacao = avaliacao.remediacao
            if novo_status == RESPOSTA_NAO_CONFORME:
                st.markdown("**🔧 Remediação em andamento** *(obrigatório para Não Conforme)*")

                nova_remediacao = st.text_area(
                    "Descreva as ações em andamento",
                    value=avaliacao.remediacao,
                    key=f"rem_{item.modulo}_{item.id}",
                    height=68,
                    placeholder="Ex.: Plano aprovado, treinamento agendado, fornecedor em homologação.",
                    label_visibility="collapsed",
                )

    evidencias = [e.strip() for e in evid_input.split(";") if e.strip()]

    return Avaliacao(
        status=novo_status,
        observacao=nova_observacao,
        criticidade=nova_criticidade,
        responsavel=novo_responsavel,
        prazo=novo_prazo,
        remediacao=nova_remediacao,
        evidencias=evidencias,
    )
