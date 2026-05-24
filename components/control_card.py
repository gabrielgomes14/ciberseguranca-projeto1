import streamlit as st

from components._helpers import _parse_prazo, _render_header_card
from core.models import (
    CRITICIDADE_MEDIA,
    CRITICIDADES,
    REMEDIACAO_OPCOES,
    Avaliacao,
)
from core.scoring import RESPOSTA_NAO_AVALIADO, RESPOSTA_NAO_CONFORME, RESPOSTAS_SELECIONAVEIS, STATUS_COLORS
from modulos.iso27001.controls import Controle


def render_control_card(controle: Controle, avaliacao: Avaliacao) -> Avaliacao:
    status_atual = avaliacao.status
    cor = STATUS_COLORS.get(status_atual or RESPOSTA_NAO_AVALIADO, STATUS_COLORS[RESPOSTA_NAO_AVALIADO])
    with st.container(border=True):
        _render_header_card(controle.id, controle.titulo, cor)
        st.caption(controle.descricao)

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
            key=f"radio_{controle.id}",
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
                key=f"rem_{controle.id}",
                format_func=lambda v: "- selecione -" if v == "" else v,
                label_visibility="collapsed",
            )

        with st.expander("Detalhes, orientação e plano"):
            st.markdown("**Controle**")
            st.write(controle.controle_texto or "Sem texto do controle cadastrado.")
            st.markdown("**Orientação da norma**")
            st.write(controle.orientacao or "Sem orientação cadastrada.")

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
                novo_prazo_date = st.date_input(
                    "Prazo de adequação",
                    value=_parse_prazo(avaliacao.prazo),
                    key=f"prazo_{controle.id}",
                    format="DD/MM/YYYY",
                )
                novo_prazo = novo_prazo_date.isoformat() if novo_prazo_date else ""
            nova_observacao = st.text_area(
                "Observações / Justificativa",
                value=avaliacao.observacao,
                key=f"obs_{controle.id}",
                height=80,
                placeholder="Notas, lacunas identificadas, decisões.",
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
