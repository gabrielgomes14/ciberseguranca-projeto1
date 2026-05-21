import csv
import io
from dataclasses import dataclass

from core.models import CRITICIDADE_ALTA, CRITICIDADE_BAIXA, CRITICIDADE_MEDIA, Avaliacao
from core.scoring import RESPOSTA_NAO_CONFORME, RESPOSTA_PARCIAL
from modulos.iso27002.controls import TEMA_LABELS, Controle

PRIORIDADE_RANK: dict[str, int] = {
    RESPOSTA_NAO_CONFORME: 0,
    RESPOSTA_PARCIAL: 1,
}

CRITICIDADE_RANK: dict[str, int] = {
    CRITICIDADE_ALTA: 0,
    CRITICIDADE_MEDIA: 1,
    CRITICIDADE_BAIXA: 2,
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


def _prioridade(status: str, criticidade: str) -> str:
    if status == RESPOSTA_NAO_CONFORME and criticidade == CRITICIDADE_ALTA:
        return "Crítica"
    if status == RESPOSTA_NAO_CONFORME:
        return "Alta"
    if status == RESPOSTA_PARCIAL and criticidade == CRITICIDADE_ALTA:
        return "Alta"
    if status == RESPOSTA_PARCIAL:
        return "Média"
    return "Baixa"


def gerar_plano(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> list[AcaoPlano]:
    acoes: list[AcaoPlano] = []
    for c in controles:
        a = avaliacoes.get(c.id)
        if a is None or a.status not in PRIORIDADE_RANK:
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
                prioridade=_prioridade(a.status, a.criticidade),
            )
        )
    acoes.sort(key=lambda x: (PRIORIDADE_RANK[x.status], CRITICIDADE_RANK[x.criticidade], x.controle_id))
    return acoes


def plano_para_csv(acoes: list[AcaoPlano]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Controle", "Tema", "Título", "Status", "Criticidade", "Prioridade",
        "Responsável", "Prazo", "Observação", "Remediação em andamento",
    ])
    for a in acoes:
        writer.writerow([
            a.controle_id, a.tema, a.titulo, a.status, a.criticidade, a.prioridade,
            a.responsavel, a.prazo, a.observacao, a.remediacao,
        ])
    return buffer.getvalue().encode("utf-8-sig")
