import streamlit as st

from components._helpers import _render_header_card
from core.models import (
    CRITICIDADE_MEDIA,
    CRITICIDADES,
    REMEDIACAO_OPCOES,
    Avaliacao,
)
from core.scoring import RESPOSTA_NAO_AVALIADO, RESPOSTA_NAO_CONFORME, RESPOSTAS_SELECIONAVEIS, STATUS_COLORS
from core.types import ItemDiagnostico


def render_item_card(item: ItemDiagnostico, avaliacao: Avaliacao) -> Avaliacao:
    status_atual = avaliacao.status
    cor = STATUS_COLORS.get(status_atual or RESPOSTA_NAO_AVALIADO, STATUS_COLORS[RESPOSTA_NAO_AVALIADO])
    with st.container(border=True):
        _render_header_card(item.id, item.titulo, cor)
        st.caption(item.descricao)

        opcoes = ("",) + RESPOSTAS_SELECIONAVEIS
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
            format_func=lambda v: "- selecione -" if v == "" else v,
            label_visibility="collapsed",
        )

        nova_remediacao = avaliacao.remediacao
        if novo_status == RESPOSTA_NAO_CONFORME:
            st.markdown("**Há remediação em andamento?**")
            opcoes_rem = ("",) + REMEDIACAO_OPCOES
            idx_rem = opcoes_rem.index(avaliacao.remediacao) if avaliacao.remediacao in opcoes_rem else 0
            nova_remediacao = st.radio(
                "Remediação em andamento",
                options=opcoes_rem,
                index=idx_rem,
                horizontal=True,
                key=f"rem_{item.modulo}_{item.id}",
                format_func=lambda v: "- selecione -" if v == "" else v,
                label_visibility="collapsed",
            )

        with st.expander("Detalhes, orientação e plano"):
            st.markdown("**Controle**")
            st.write(item.controle_texto or "Sem texto do controle cadastrado.")
            st.markdown("**Orientação da norma**")
            st.write(item.orientacao or "Sem orientação cadastrada.")

            st.divider()
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
                prazo_valor = None
                if avaliacao.prazo:
                    try:
                        from datetime import date as _date

                        prazo_valor = _date.fromisoformat(avaliacao.prazo)
                    except ValueError:
                        prazo_valor = None
                novo_prazo_date = st.date_input(
                    "Prazo",
                    value=prazo_valor,
                    key=f"prazo_{item.modulo}_{item.id}",
                    format="DD/MM/YYYY",
                )
                novo_prazo = novo_prazo_date.isoformat() if novo_prazo_date else ""
            nova_observacao = st.text_area(
                "Observação",
                value=avaliacao.observacao,
                key=f"obs_{item.modulo}_{item.id}",
                height=80,
            )

    return Avaliacao(
        status=novo_status,
        observacao=nova_observacao,
        criticidade=nova_criticidade,
        responsavel=novo_responsavel,
        prazo=novo_prazo,
        remediacao=nova_remediacao if novo_status == RESPOSTA_NAO_CONFORME else "",
        evidencias=list(avaliacao.evidencias),
    )
