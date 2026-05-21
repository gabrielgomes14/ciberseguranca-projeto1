from core.models import (
    CRITICIDADE_ALTA,
    CRITICIDADE_BAIXA,
    CRITICIDADE_MEDIA,
    Avaliacao,
)
from core.scoring import (
    RESPOSTA_CONFORME,
    RESPOSTA_NA,
    RESPOSTA_NAO_AVALIADO,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_PARCIAL,
    resumo_tema,
    score_controle,
    score_geral,
    score_tema,
    status_individual,
    status_label,
)


def _av(status: str, criticidade: str = CRITICIDADE_MEDIA) -> Avaliacao:
    return Avaliacao(status=status, criticidade=criticidade)


def test_score_controle_conforme_eh_100() -> None:
    assert score_controle(RESPOSTA_CONFORME) == 100.0


def test_score_controle_parcial_eh_50() -> None:
    assert score_controle(RESPOSTA_PARCIAL) == 50.0


def test_score_controle_nao_conforme_eh_zero() -> None:
    assert score_controle(RESPOSTA_NAO_CONFORME) == 0.0


def test_score_tema_na_excluido_do_denominador() -> None:
    avaliacoes = {"5.1": _av(RESPOSTA_CONFORME), "5.2": _av(RESPOSTA_NA), "5.3": _av(RESPOSTA_NA)}
    assert score_tema(avaliacoes, ["5.1", "5.2", "5.3"]) == 100.0


def test_score_tema_mix_sem_peso() -> None:
    avaliacoes = {
        "5.1": _av(RESPOSTA_CONFORME),
        "5.2": _av(RESPOSTA_PARCIAL),
        "5.3": _av(RESPOSTA_NAO_CONFORME),
        "5.4": _av(RESPOSTA_NA),
    }
    assert score_tema(avaliacoes, ["5.1", "5.2", "5.3", "5.4"], ponderado=False) == 50.0


def test_score_tema_ponderado_critico_pesa_mais() -> None:
    avaliacoes = {
        "a": Avaliacao(status=RESPOSTA_NAO_CONFORME, criticidade=CRITICIDADE_ALTA),
        "b": Avaliacao(status=RESPOSTA_CONFORME, criticidade=CRITICIDADE_BAIXA),
    }
    score = score_tema(avaliacoes, ["a", "b"], ponderado=True)
    assert score == (0.0 * 3.0 + 100.0 * 1.0) / (3.0 + 1.0)


def test_score_geral_tema_sem_respostas_retorna_zero() -> None:
    assert score_geral({}, ["5.1", "5.2"]) == 0.0


def test_status_label_faixas() -> None:
    assert status_label(95.0) == RESPOSTA_CONFORME
    assert status_label(60.0) == RESPOSTA_PARCIAL
    assert status_label(10.0) == RESPOSTA_NAO_CONFORME


def test_status_individual_sem_resposta() -> None:
    assert status_individual(None) == RESPOSTA_NAO_AVALIADO
    assert status_individual(Avaliacao()) == RESPOSTA_NAO_AVALIADO


def test_resumo_tema_contagens() -> None:
    avaliacoes = {
        "a": _av(RESPOSTA_CONFORME),
        "b": _av(RESPOSTA_CONFORME),
        "c": _av(RESPOSTA_PARCIAL),
        "d": _av(RESPOSTA_NAO_CONFORME),
        "e": _av(RESPOSTA_NA),
    }
    r = resumo_tema(avaliacoes, "org", ["a", "b", "c", "d", "e", "f"])
    assert r.conformes == 2
    assert r.parciais == 1
    assert r.nao_conformes == 1
    assert r.na == 1
    assert r.avaliados == 4
    assert r.total == 6
