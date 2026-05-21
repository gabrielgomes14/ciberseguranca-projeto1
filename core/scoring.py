from dataclasses import dataclass

from core.models import PESOS, Avaliacao

RESPOSTA_CONFORME = "Conforme"
RESPOSTA_PARCIAL = "Parcial"
RESPOSTA_NAO_CONFORME = "Não Conforme"
RESPOSTA_NA = "N/A"
RESPOSTA_NAO_AVALIADO = "Não avaliado"

# Thresholds de score (0-100) usados por status_label e por componentes de visualização.
SCORE_THRESHOLD_PARCIAL = 40.0
SCORE_THRESHOLD_CONFORME = 80.0

RESPOSTAS_VALIDAS: tuple[str, ...] = (
    RESPOSTA_CONFORME,
    RESPOSTA_PARCIAL,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_NA,
)

_STATUS_PARA_SCORE: dict[str, float] = {
    RESPOSTA_CONFORME: 100.0,
    RESPOSTA_PARCIAL: 50.0,
    RESPOSTA_NAO_CONFORME: 0.0,
}

STATUS_COLORS: dict[str, str] = {
    RESPOSTA_CONFORME: "#16a34a",
    RESPOSTA_PARCIAL: "#d97706",
    RESPOSTA_NAO_CONFORME: "#dc2626",
    RESPOSTA_NA: "#6b7280",
    RESPOSTA_NAO_AVALIADO: "#cbd5e1",
}


@dataclass(frozen=True)
class ResultadoTema:
    tema_id: str
    score: float
    total: int
    avaliados: int
    conformes: int
    parciais: int
    nao_conformes: int
    na: int


def score_controle(status: str) -> float:
    return _STATUS_PARA_SCORE.get(status, 0.0)


def clamp_score(score: float) -> float:
    """Garante que o score fique no intervalo [0, 100]."""
    return max(0.0, min(100.0, score))


def _avaliacoes_pontuaveis(
    avaliacoes: dict[str, Avaliacao],
    ids: list[str],
) -> list[Avaliacao]:
    return [
        avaliacoes[c]
        for c in ids
        if c in avaliacoes and avaliacoes[c].status in _STATUS_PARA_SCORE
    ]


def score_tema(avaliacoes: dict[str, Avaliacao], ids: list[str], *, ponderado: bool = True) -> float:
    pontuaveis = _avaliacoes_pontuaveis(avaliacoes, ids)
    if not pontuaveis:
        return 0.0
    if not ponderado:
        return sum(score_controle(a.status) for a in pontuaveis) / len(pontuaveis)
    soma_ponderada = sum(score_controle(a.status) * PESOS[a.criticidade] for a in pontuaveis)
    soma_pesos = sum(PESOS[a.criticidade] for a in pontuaveis)
    return soma_ponderada / soma_pesos if soma_pesos > 0 else 0.0


def score_geral(avaliacoes: dict[str, Avaliacao], todos_ids: list[str], *, ponderado: bool = True) -> float:
    return score_tema(avaliacoes, todos_ids, ponderado=ponderado)


def status_label(score: float) -> str:
    if score >= SCORE_THRESHOLD_CONFORME:
        return RESPOSTA_CONFORME
    if score >= SCORE_THRESHOLD_PARCIAL:
        return RESPOSTA_PARCIAL
    return RESPOSTA_NAO_CONFORME


def resumo_tema(
    avaliacoes: dict[str, Avaliacao],
    tema_id: str,
    ids: list[str],
    *,
    ponderado: bool = True,
) -> ResultadoTema:
    conformes = sum(1 for c in ids if avaliacoes.get(c, Avaliacao()).status == RESPOSTA_CONFORME)
    parciais = sum(1 for c in ids if avaliacoes.get(c, Avaliacao()).status == RESPOSTA_PARCIAL)
    nao_conformes = sum(1 for c in ids if avaliacoes.get(c, Avaliacao()).status == RESPOSTA_NAO_CONFORME)
    na = sum(1 for c in ids if avaliacoes.get(c, Avaliacao()).status == RESPOSTA_NA)
    avaliados = conformes + parciais + nao_conformes
    return ResultadoTema(
        tema_id=tema_id,
        score=score_tema(avaliacoes, ids, ponderado=ponderado),
        total=len(ids),
        avaliados=avaliados,
        conformes=conformes,
        parciais=parciais,
        nao_conformes=nao_conformes,
        na=na,
    )


def status_individual(avaliacao: Avaliacao | None) -> str:
    if avaliacao is None or not avaliacao.status:
        return RESPOSTA_NAO_AVALIADO
    if avaliacao.status in RESPOSTAS_VALIDAS:
        return avaliacao.status
    return RESPOSTA_NAO_AVALIADO
