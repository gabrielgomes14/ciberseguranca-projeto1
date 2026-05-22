from core.action_plan import AcaoPlano
from core.models import Avaliacao
from core.pdf_report import gerar_pdf, gerar_pdf_27001
from core.scoring import RESPOSTA_CONFORME, RESPOSTA_NAO_CONFORME
from core.types import ItemDiagnostico
from modulos.iso27002.controls import TODOS_CONTROLES


def test_gerar_pdf_retorna_bytes_pdf() -> None:
    pdf = gerar_pdf(TODOS_CONTROLES, {}, [])
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-"), "Saída não tem o magic number de PDF"
    assert len(pdf) > 1000, "PDF suspeitosamente pequeno"


def test_gerar_pdf_com_avaliacoes_e_acoes() -> None:
    controles = TODOS_CONTROLES[:5]
    avaliacoes = {
        controles[0].id: Avaliacao(status=RESPOSTA_CONFORME),
        controles[1].id: Avaliacao(status=RESPOSTA_NAO_CONFORME, responsavel="Alice"),
    }
    acoes = [
        AcaoPlano(
            controle_id=controles[1].id,
            tema=controles[1].tema_id,
            titulo=controles[1].titulo,
            status=RESPOSTA_NAO_CONFORME,
            criticidade="Alta",
            responsavel="Alice",
            prazo="2026-12-31",
            observacao="",
            remediacao="Em andamento",
            prioridade="P1",
        )
    ]
    pdf = gerar_pdf(controles, avaliacoes, acoes, organizacao="Acme Ltda.", data_auditoria="2026-05-21")
    assert pdf.startswith(b"%PDF-")


def test_gerar_pdf_sem_acoes_nao_quebra() -> None:
    pdf = gerar_pdf(TODOS_CONTROLES[:3], {}, [])
    assert pdf.startswith(b"%PDF-")


# --- gerar_pdf_27001 --------------------------------------------------------


def test_gerar_pdf_27001_retorna_bytes_pdf() -> None:
    requisitos = [
        ItemDiagnostico(id="4.1", titulo="Contexto da organização", descricao="d", categoria_id="4", modulo="iso27001"),
        ItemDiagnostico(id="6.1", titulo="Riscos e oportunidades", descricao="d", categoria_id="6", modulo="iso27001"),
    ]
    secoes = {"4": "Contexto", "6": "Planejamento"}
    por_secao = {
        "4": [requisitos[0]],
        "6": [requisitos[1]],
    }
    pdf = gerar_pdf_27001(requisitos, secoes, por_secao, avaliacoes={})
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


def test_gerar_pdf_27001_com_avaliacoes() -> None:
    requisitos = [
        ItemDiagnostico(id="4.1", titulo="Contexto", descricao="d", categoria_id="4", modulo="iso27001"),
    ]
    secoes = {"4": "Contexto"}
    por_secao = {"4": requisitos}
    avaliacoes = {"4.1": Avaliacao(status=RESPOSTA_CONFORME, responsavel="Alice")}
    pdf = gerar_pdf_27001(requisitos, secoes, por_secao, avaliacoes, organizacao="Acme Ltda.", data_auditoria="2026-05-21")
    assert pdf.startswith(b"%PDF-")


def test_gerar_pdf_27001_sem_plano_de_acao() -> None:
    """27001 não inclui seção de plano de ação no PDF (acoes=None na base)."""
    pdf = gerar_pdf_27001([], {}, {}, {})
    # Sem itens, gera só cabeçalho e tabelas vazias — ainda assim é um PDF válido.
    assert pdf.startswith(b"%PDF-")
