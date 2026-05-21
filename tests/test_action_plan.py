from core.action_plan import gerar_plano, plano_para_csv
from core.models import Avaliacao
from modulos.iso27002.controls import TODOS_CONTROLES


def test_plano_inclui_apenas_nao_conformes_e_parciais() -> None:
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


def test_plano_ordena_nao_conforme_primeiro() -> None:
    avaliacoes = {
        "5.2": Avaliacao(status="Parcial", criticidade="Baixa"),
        "5.3": Avaliacao(status="Não Conforme", criticidade="Baixa"),
    }
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].status == "Não Conforme"


def test_prioridade_critica_para_nao_conforme_alto() -> None:
    avaliacoes = {"5.1": Avaliacao(status="Não Conforme", criticidade="Alta")}
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    assert plano[0].prioridade == "Crítica"


def test_csv_contem_cabecalho() -> None:
    avaliacoes = {"5.1": Avaliacao(status="Não Conforme", remediacao="Sim")}
    plano = gerar_plano(TODOS_CONTROLES, avaliacoes)
    csv = plano_para_csv(plano).decode("utf-8-sig")
    assert "Controle" in csv
    assert "Prioridade" in csv
    assert "Remediação em andamento" in csv
    assert "Sim" in csv
    assert "5.1" in csv
