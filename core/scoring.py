from dataclasses import dataclass

from core.models import PESOS, REMEDIACAO_SIM, Avaliacao

RESPOSTA_CONFORME = "Conforme"
RESPOSTA_PARCIAL = "Parcial"
RESPOSTA_NAO_CONFORME = "Não Conforme"
RESPOSTA_NA = "N/A"
RESPOSTA_NAO_AVALIADO = "Não avaliado"
RESPOSTA_EM_ADEQUACAO = "Em Adequação"

# Thresholds de score (0-100) usados por status_label e por componentes de visualização.
SCORE_THRESHOLD_EM_ADEQUACAO = 40.0
SCORE_THRESHOLD_PARCIAL = SCORE_THRESHOLD_EM_ADEQUACAO  # Alias retrocompatível durante a transição.
SCORE_THRESHOLD_CONFORME = 80.0

RESPOSTAS_VALIDAS: tuple[str, ...] = (
    RESPOSTA_CONFORME,
    RESPOSTA_PARCIAL,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_NA,
)

RESPOSTAS_SELECIONAVEIS: tuple[str, ...] = (
    RESPOSTA_CONFORME,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_NA,
)

# Status que entram no cálculo de score (excluídos: N/A, vazio, Em Adequação como rótulo derivado).
_STATUS_PONTUAVEIS: frozenset[str] = frozenset({RESPOSTA_CONFORME, RESPOSTA_PARCIAL, RESPOSTA_NAO_CONFORME})

STATUS_COLORS: dict[str, str] = {
    RESPOSTA_CONFORME: "#16a34a",
    RESPOSTA_PARCIAL: "#d97706",
    RESPOSTA_EM_ADEQUACAO: "#d97706",
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


def score_controle(avaliacao: Avaliacao) -> float:
    """Pontuação 0-100 do controle conforme status + remediação.

    Regras:
    - Conforme → 100.
    - Não Conforme + remediação "Sim" → 50 (substitui o antigo "Parcial").
    - Não Conforme sem remediação ou negativa → 0.
    - Outros (N/A, vazio) → 0 (não devem ser passados; chamadores filtram via `_STATUS_PONTUAVEIS`).
    - "Parcial" legado: tratado como 50 para compatibilidade até a migração do DB rodar.
    """
    if avaliacao.status == RESPOSTA_CONFORME:
        return 100.0
    if avaliacao.status == RESPOSTA_NAO_CONFORME:
        return 50.0 if avaliacao.remediacao == REMEDIACAO_SIM else 0.0
    if avaliacao.status == RESPOSTA_PARCIAL:
        return 50.0
    return 0.0


def clamp_score(score: float) -> float:
    """Garante que o score fique no intervalo [0, 100]."""
    return max(0.0, min(100.0, score))


def _avaliacoes_pontuaveis(
    avaliacoes: dict[str, Avaliacao],
    ids: list[str],
) -> list[Avaliacao]:
    return [avaliacoes[c] for c in ids if c in avaliacoes and avaliacoes[c].status in _STATUS_PONTUAVEIS]


def score_tema(avaliacoes: dict[str, Avaliacao], ids: list[str], *, ponderado: bool = True) -> float:
    pontuaveis = _avaliacoes_pontuaveis(avaliacoes, ids)
    if not pontuaveis:
        return 0.0
    if not ponderado:
        return sum(score_controle(a) for a in pontuaveis) / len(pontuaveis)
    soma_ponderada = sum(score_controle(a) * PESOS[a.criticidade] for a in pontuaveis)
    soma_pesos = sum(PESOS[a.criticidade] for a in pontuaveis)
    return soma_ponderada / soma_pesos if soma_pesos > 0 else 0.0


def score_geral(avaliacoes: dict[str, Avaliacao], todos_ids: list[str], *, ponderado: bool = True) -> float:
    return score_tema(avaliacoes, todos_ids, ponderado=ponderado)


def status_label(score: float) -> str:
    if score >= SCORE_THRESHOLD_CONFORME:
        return RESPOSTA_CONFORME
    if score >= SCORE_THRESHOLD_EM_ADEQUACAO:
        return RESPOSTA_EM_ADEQUACAO
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
