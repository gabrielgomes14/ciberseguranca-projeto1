from core.action_plan import AcaoPlano
from core.models import Avaliacao
from core.pdf_report import gerar_pdf
from core.scoring import RESPOSTA_CONFORME, RESPOSTA_NAO_CONFORME
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
