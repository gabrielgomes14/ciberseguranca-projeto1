from dataclasses import dataclass

from core.action_plan import AcaoPlano
from core.models import Avaliacao
from core.pdf_report import gerar_pdf, gerar_pdf_27001, gerar_pdf_27701, gerar_pdf_comparativo
from core.scoring import RESPOSTA_CONFORME, RESPOSTA_NAO_CONFORME
from core.types import ItemDiagnostico
from modulos.iso27001.controls import TODOS_CONTROLES


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
    # Sem itens, gera só cabeçalho e tabelas vazias - ainda assim é um PDF válido.
    assert pdf.startswith(b"%PDF-")


# --- gerar_pdf_27701 --------------------------------------------------------


def test_gerar_pdf_27701_retorna_bytes_pdf() -> None:
    controles = [
        ItemDiagnostico(
            id="A.7.2.1",
            titulo="Identificação e documentação de propósito",
            descricao="d",
            categoria_id="A.7.2",
            modulo="iso27701",
        ),
        ItemDiagnostico(
            id="A.7.4.1",
            titulo="Limitação de coleta",
            descricao="d",
            categoria_id="A.7.4",
            modulo="iso27701",
        ),
    ]
    categorias = {"A.7.2": "Condições para coleta", "A.7.4": "Privacy by design"}
    por_categoria = {
        "A.7.2": [controles[0]],
        "A.7.4": [controles[1]],
    }
    pdf = gerar_pdf_27701(controles, categorias, por_categoria, avaliacoes={})
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


def test_gerar_pdf_27701_com_avaliacoes() -> None:
    controles = [
        ItemDiagnostico(
            id="A.7.2.1",
            titulo="Identificação de propósito",
            descricao="d",
            categoria_id="A.7.2",
            modulo="iso27701",
        ),
    ]
    categorias = {"A.7.2": "Condições para coleta"}
    por_categoria = {"A.7.2": controles}
    avaliacoes = {"A.7.2.1": Avaliacao(status=RESPOSTA_CONFORME, responsavel="DPO")}
    pdf = gerar_pdf_27701(
        controles,
        categorias,
        por_categoria,
        avaliacoes,
        organizacao="Acme Ltda.",
        data_auditoria="2026-05-21",
    )
    assert pdf.startswith(b"%PDF-")


def test_gerar_pdf_27701_sem_plano_de_acao() -> None:
    """27701 não inclui seção de plano de ação no PDF (acoes=None na base)."""
    pdf = gerar_pdf_27701([], {}, {}, {})
    assert pdf.startswith(b"%PDF-")


# --- gerar_pdf_comparativo --------------------------------------------------


@dataclass(frozen=True)
class _SnapshotFake:
    """Stub mínimo com a 'forma' que `gerar_pdf_comparativo` espera (duck typing)."""

    score_geral: float
    scores_por_categoria: dict[str, float]
    rotulo: str
    criado_em: str
    avaliados: int


def test_gerar_pdf_comparativo_melhoria() -> None:
    snap_a = _SnapshotFake(
        score_geral=60.0,
        scores_por_categoria={"org": 60.0, "tech": 50.0},
        rotulo="2026-04",
        criado_em="2026-04-01",
        avaliados=80,
    )
    snap_b = _SnapshotFake(
        score_geral=75.0,
        scores_por_categoria={"org": 70.0, "tech": 80.0},
        rotulo="2026-05",
        criado_em="2026-05-01",
        avaliados=85,
    )
    pdf = gerar_pdf_comparativo(
        norma="ISO/IEC 27001:2022",
        titulo_categoria="Tema",
        categorias_label={"org": "Organizacionais", "tech": "Tecnológicos"},
        snap_a=snap_a,
        snap_b=snap_b,
    )
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


def test_gerar_pdf_comparativo_regressao() -> None:
    snap_a = _SnapshotFake(80.0, {"org": 90.0}, "v1", "2026-01-01", 100)
    snap_b = _SnapshotFake(70.0, {"org": 70.0}, "v2", "2026-02-01", 100)
    pdf = gerar_pdf_comparativo("ISO/IEC 27001:2022", "Seção", {"org": "Org"}, snap_a, snap_b)
    assert pdf.startswith(b"%PDF-")


def test_gerar_pdf_comparativo_estavel() -> None:
    snap_a = _SnapshotFake(50.0, {"x": 50.0}, "a", "2026-01-01", 10)
    snap_b = _SnapshotFake(50.0, {"x": 50.0}, "b", "2026-02-01", 10)
    pdf = gerar_pdf_comparativo("Norma", "Cat", {"x": "X"}, snap_a, snap_b)
    assert pdf.startswith(b"%PDF-")


def test_gerar_pdf_comparativo_categoria_apenas_em_um_snapshot() -> None:
    """Categoria em A mas não em B (e vice-versa) cai no default 0.0."""
    snap_a = _SnapshotFake(40.0, {"org": 40.0}, "a", "2026-01-01", 5)
    snap_b = _SnapshotFake(60.0, {"tech": 60.0}, "b", "2026-02-01", 5)
    pdf = gerar_pdf_comparativo("Norma", "Cat", {"org": "Org", "tech": "Tech"}, snap_a, snap_b)
    assert pdf.startswith(b"%PDF-")
