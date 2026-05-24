import csv
import io

from core.export import _HEADERS, _safe_cell, gerar_csv, montar_linhas
from core.models import Avaliacao
from core.scoring import RESPOSTA_CONFORME, RESPOSTA_NAO_AVALIADO
from modulos.iso27001.controls import Controle


def _decode_csv(blob: bytes) -> list[list[str]]:
    text = blob.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text), delimiter=";"))


# --- _safe_cell -------------------------------------------------------------


def test_safe_cell_passa_valor_normal() -> None:
    assert _safe_cell("Texto comum") == "Texto comum"


def test_safe_cell_neutraliza_formula_excel() -> None:
    assert _safe_cell("=SUM(A1:A2)") == "'=SUM(A1:A2)"


def test_safe_cell_neutraliza_prefixos_perigosos() -> None:
    for prefixo in ("=", "+", "-", "@", "\t", "\r"):
        assert _safe_cell(f"{prefixo}payload").startswith("'")


def test_safe_cell_string_vazia_intacta() -> None:
    assert _safe_cell("") == ""


# --- montar_linhas ----------------------------------------------------------


def test_montar_linhas_status_nao_avaliado_para_avaliacao_ausente() -> None:
    controles = [Controle("5.1", "Título", "Desc", "org")]
    linhas = montar_linhas(controles, avaliacoes={})
    assert len(linhas) == 1
    assert linhas[0].status == RESPOSTA_NAO_AVALIADO
    assert linhas[0].tema == "Organizacionais"


def test_montar_linhas_tema_desconhecido_nao_quebra() -> None:
    controles = [Controle("X.1", "T", "D", "tema_inexistente")]
    linhas = montar_linhas(controles, {})
    # Cai no próprio tema_id como fallback.
    assert linhas[0].tema == "tema_inexistente"


def test_montar_linhas_usa_avaliacao_quando_existe() -> None:
    controles = [Controle("5.1", "T", "D", "org")]
    av = Avaliacao(status=RESPOSTA_CONFORME, responsavel="Alice")
    linhas = montar_linhas(controles, {"5.1": av})
    assert linhas[0].status == RESPOSTA_CONFORME
    assert linhas[0].responsavel == "Alice"


# --- gerar_csv --------------------------------------------------------------


def test_gerar_csv_tem_bom_utf8() -> None:
    blob = gerar_csv([], {})
    # BOM UTF-8 = EF BB BF.
    assert blob.startswith(b"\xef\xbb\xbf")


def test_gerar_csv_header_em_pt_br() -> None:
    blob = gerar_csv([], {})
    linhas = _decode_csv(blob)
    assert linhas[0] == list(_HEADERS.values())


def test_gerar_csv_csv_injection_neutralizada() -> None:
    controles = [Controle("5.1", "T", "D", "org")]
    avaliacoes = {
        "5.1": Avaliacao(
            status=RESPOSTA_CONFORME,
            observacao='=HYPERLINK("http://evil","x")',
            responsavel="+1+1",
        )
    }
    blob = gerar_csv(controles, avaliacoes)
    linhas = _decode_csv(blob)
    # Header + 1 linha de dados.
    assert len(linhas) == 2
    cabecalho = linhas[0]
    dados = linhas[1]
    idx_obs = cabecalho.index("Observação")
    idx_resp = cabecalho.index("Responsável")
    assert dados[idx_obs].startswith("'=")
    assert dados[idx_resp].startswith("'+")


def test_gerar_csv_separador_ponto_e_virgula() -> None:
    blob = gerar_csv([], {})
    text = blob.decode("utf-8-sig")
    # Pelo menos uma linha (header) com ;
    assert ";" in text.splitlines()[0]
