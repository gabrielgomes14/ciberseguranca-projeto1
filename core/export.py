import csv
import io
from dataclasses import asdict, dataclass, fields

from core.models import Avaliacao
from core.scoring import status_individual
from modulos.iso27001.controls import TEMA_LABELS, Controle

# Caracteres que, no início de uma célula CSV, são interpretados como fórmula
# por Excel/LibreOffice/Google Sheets. Mitigação para CSV Injection (CWE-1236).
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value: str) -> str:
    """Mitiga CSV Injection prefixando com aspa simples valores que começam com caractere de fórmula."""
    if value and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


@dataclass(frozen=True)
class LinhaRelatorio:
    controle_id: str
    tema: str
    titulo: str
    status: str
    criticidade: str
    responsavel: str
    prazo: str
    observacao: str
    remediacao: str
    descricao: str


# Mapeia atributo da dataclass -> rótulo em pt-BR exibido no cabeçalho do CSV.
# Mantém uma única fonte de verdade para ordem e nomes das colunas.
_HEADERS: dict[str, str] = {
    "controle_id": "Controle",
    "tema": "Tema",
    "titulo": "Título",
    "status": "Status",
    "criticidade": "Criticidade",
    "responsavel": "Responsável",
    "prazo": "Prazo",
    "observacao": "Observação",
    "remediacao": "Remediação em andamento",
    "descricao": "Descrição",
}

# Garante em tempo de import que _HEADERS cobre exatamente os campos da dataclass.
assert set(_HEADERS) == {f.name for f in fields(LinhaRelatorio)}, "_HEADERS desalinhado com LinhaRelatorio"


def montar_linhas(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> list[LinhaRelatorio]:
    """Monta as linhas do relatório a partir do catálogo de controles e das avaliações atuais.

    Controles sem avaliação aparecem com status "Não avaliado". Tema desconhecido
    cai no próprio `tema_id` (não quebra a exportação).
    """
    linhas: list[LinhaRelatorio] = []
    for c in controles:
        a = avaliacoes.get(c.id, Avaliacao())
        linhas.append(
            LinhaRelatorio(
                controle_id=c.id,
                tema=TEMA_LABELS.get(c.tema_id, c.tema_id),
                titulo=c.titulo,
                status=status_individual(a),
                criticidade=a.criticidade,
                responsavel=a.responsavel,
                prazo=a.prazo,
                observacao=a.observacao,
                remediacao=a.remediacao,
                descricao=c.descricao,
            )
        )
    return linhas


def gerar_csv(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> bytes:
    """Gera o relatório CSV em UTF-8 com BOM, separador `;` e proteção contra CSV Injection.

    Retorna `bytes` prontos para `st.download_button(data=...)`.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(list(_HEADERS.values()))
    for linha in montar_linhas(controles, avaliacoes):
        valores = asdict(linha)
        writer.writerow([_safe_cell(str(valores[campo])) for campo in _HEADERS])
    return buffer.getvalue().encode("utf-8-sig")
