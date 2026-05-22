from core.action_plan import gerar_plano, plano_para_csv
from core.models import Avaliacao
from modulos.iso27002.controls import TODOS_CONTROLES


def test_plano_inclui_apenas_nao_conformes_e_parciais_legado() -> None:
    """Conforme e N/A não geram ação. Parcial (legado) ainda gera durante a transição."""
    avaliacoes = {
        "5.1": Avaliacao(status="Conforme"),
        "5.2": Avaliacao(status="Parcial", criticidade="Alta"),
        "5.3": Avaliacao(status="Não Conforme", criticidade="Média"),
        "5.4": Avaliacao(status="N/A"),
    }
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    ids = [a.controle_id for a in plano]
    assert "5.1" not in ids
    assert "5.4" not in ids
    assert "5.2" in ids
    assert "5.3" in ids


def test_plano_ordena_por_prioridade() -> None:
    """A ordenação prioriza pelo rótulo (Crítica > Alta > Média > Baixa)."""
    avaliacoes = {
        "5.2": Avaliacao(status="Parcial", criticidade="Baixa"),  # → Média
        "5.3": Avaliacao(status="Não Conforme", criticidade="Baixa"),  # → Alta
    }
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].controle_id == "5.3"
    assert plano[0].prioridade == "Alta"
    assert plano[1].prioridade == "Média"


def test_prioridade_critica_para_nao_conforme_alto_sem_remediacao() -> None:
    avaliacoes = {"5.1": Avaliacao(status="Não Conforme", criticidade="Alta")}
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].prioridade == "Crítica"


def test_remediacao_em_andamento_reduz_prioridade_critica_para_alta() -> None:
    avaliacoes = {
        "5.1": Avaliacao(status="Não Conforme", criticidade="Alta", remediacao="Sim"),
    }
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].prioridade == "Alta"


def test_remediacao_em_andamento_reduz_prioridade_alta_para_media() -> None:
    avaliacoes = {
        "5.1": Avaliacao(status="Não Conforme", criticidade="Média", remediacao="Sim"),
    }
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].prioridade == "Média"


def test_parcial_legado_equivale_a_nao_conforme_com_remediacao_sim() -> None:
    """Parcial e NC+remediação=Sim devem produzir a mesma prioridade durante a transição."""
    av_parcial = {"5.1": Avaliacao(status="Parcial", criticidade="Alta")}
    av_nc_rem = {"5.1": Avaliacao(status="Não Conforme", criticidade="Alta", remediacao="Sim")}
    p1 = gerar_plano(TODOS_CONTROLES, av_parcial)
    p2 = gerar_plano(TODOS_CONTROLES, av_nc_rem)
    assert p1[0].prioridade == p2[0].prioridade == "Alta"


def test_csv_contem_cabecalho() -> None:
    avaliacoes = {"5.1": Avaliacao(status="Não Conforme", remediacao="Sim")}
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    csv = plano_para_csv(plano).decode("utf-8-sig")
    assert "Controle" in csv
    assert "Prioridade" in csv
    assert "Remediação em andamento" in csv
    assert "Sim" in csv
    assert "5.1" in csv
