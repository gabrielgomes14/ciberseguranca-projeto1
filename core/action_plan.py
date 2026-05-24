import csv
import io
from dataclasses import dataclass

from core.models import (
    CRITICIDADE_ALTA,
    CRITICIDADE_BAIXA,
    CRITICIDADE_MEDIA,
    REMEDIACAO_SIM,
    Avaliacao,
)
from core.scoring import RESPOSTA_NAO_CONFORME
from modulos.iso27001.controls import TEMA_LABELS, Controle

# Status legado pré-migração (Parcial → NC + remediacao=Sim). Mantido para tolerância
# de leitura até `_migrar` rodar; não exposto como constante pública.
_STATUS_LEGADO_PARCIAL = "Parcial"

# Status que geram ação no plano. Inclui o legado retrocompatível.
_STATUS_NO_PLANO: frozenset[str] = frozenset({RESPOSTA_NAO_CONFORME, _STATUS_LEGADO_PARCIAL})

CRITICIDADE_RANK: dict[str, int] = {
    CRITICIDADE_ALTA: 0,
    CRITICIDADE_MEDIA: 1,
    CRITICIDADE_BAIXA: 2,
}

# Ordem de prioridade do plano (Crítica > Alta > Média > Baixa).
_PRIORIDADE_ORDEM: dict[str, int] = {
    "Crítica": 0,
    "Alta": 1,
    "Média": 2,
    "Baixa": 3,
}


@dataclass(frozen=True)
class AcaoPlano:
    controle_id: str
    tema: str
    titulo: str
    status: str
    criticidade: str
    responsavel: str
    prazo: str
    observacao: str
    remediacao: str
    prioridade: str


def _prioridade(status: str, criticidade: str, remediacao: str) -> str:
    """Calcula a prioridade da ação a partir de status + criticidade + remediação.

    Regra: criticidade Alta + remediação ausente é o pior cenário (Crítica).
    Remediação em andamento reduz a prioridade em um nível. Status legado "Parcial"
    é equivalente a "Não Conforme + remediacao=Sim" durante a transição.
    """
    em_andamento = remediacao == REMEDIACAO_SIM or status == _STATUS_LEGADO_PARCIAL
    if status not in _STATUS_NO_PLANO:
        return "Baixa"
    if criticidade == CRITICIDADE_ALTA:
        return "Alta" if em_andamento else "Crítica"
    return "Média" if em_andamento else "Alta"


def gerar_plano(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> list[AcaoPlano]:
    acoes: list[AcaoPlano] = []
    for c in controles:
        a = avaliacoes.get(c.id)
        if a is None or a.status not in _STATUS_NO_PLANO:
            continue
        acoes.append(
            AcaoPlano(
                controle_id=c.id,
                tema=TEMA_LABELS[c.tema_id],
                titulo=c.titulo,
                status=a.status,
                criticidade=a.criticidade,
                responsavel=a.responsavel,
                prazo=a.prazo,
                observacao=a.observacao,
                remediacao=a.remediacao,
                prioridade=_prioridade(a.status, a.criticidade, a.remediacao),
            )
        )
    acoes.sort(key=lambda x: (_PRIORIDADE_ORDEM[x.prioridade], CRITICIDADE_RANK[x.criticidade], x.controle_id))
    return acoes


def plano_para_csv(acoes: list[AcaoPlano]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(
        [
            "Controle",
            "Tema",
            "Título",
            "Status",
            "Criticidade",
            "Prioridade",
            "Responsável",
            "Prazo",
            "Observação",
            "Remediação em andamento",
        ]
    )
    for a in acoes:
        writer.writerow(
            [
                a.controle_id,
                a.tema,
                a.titulo,
                a.status,
                a.criticidade,
                a.prioridade,
                a.responsavel,
                a.prazo,
                a.observacao,
                a.remediacao,
            ]
        )
    return buffer.getvalue().encode("utf-8-sig")
