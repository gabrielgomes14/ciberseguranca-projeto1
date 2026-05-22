"""Testa a migração de avaliações com status legado 'Parcial'."""

import os
import tempfile
from collections.abc import Iterator

import pytest

from core import db
from core.models import Avaliacao


@pytest.fixture
def db_path() -> Iterator[str]:
    """DB temporário isolado, mesmo padrão usado em test_db.py."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    os.environ["DIAGNOSTICO_DB_PATH"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)
    os.environ.pop("DIAGNOSTICO_DB_PATH", None)


def _inserir_parcial_legado(diag_id: int, item_id: str, criticidade: str = "Média") -> None:
    """Insere uma linha com status='Parcial' diretamente, simulando dados pré-migração."""
    with db.conexao() as con:
        con.execute(
            "INSERT INTO avaliacao (diagnostico_id, item_id, status, criticidade) VALUES (?, ?, 'Parcial', ?)",
            (diag_id, item_id, criticidade),
        )


def _ler_avaliacao(diag_id: int, item_id: str) -> tuple[str, str]:
    with db.conexao() as con:
        row = con.execute(
            "SELECT status, remediacao FROM avaliacao WHERE diagnostico_id = ? AND item_id = ?",
            (diag_id, item_id),
        ).fetchone()
    return (str(row["status"]), str(row["remediacao"]))


def test_migra_parcial_para_nao_conforme_com_remediacao(db_path: str) -> None:
    db.init_db()
    did = db.criar_diagnostico("iso27002", "Acme")
    _inserir_parcial_legado(did, "5.1", criticidade="Alta")

    # Reexecutar init_db dispara a migração.
    db.init_db()

    status, remediacao = _ler_avaliacao(did, "5.1")
    assert status == "Não Conforme"
    assert remediacao == "Sim"


def test_migracao_e_idempotente(db_path: str) -> None:
    """Rodar a migração 2× não muda nada após a primeira execução."""
    db.init_db()
    did = db.criar_diagnostico("iso27002", "Acme")
    _inserir_parcial_legado(did, "5.2")
    db.init_db()  # primeira migração
    primeiro = _ler_avaliacao(did, "5.2")
    db.init_db()  # segunda migração — não deve regredir
    segundo = _ler_avaliacao(did, "5.2")
    assert primeiro == segundo == ("Não Conforme", "Sim")


def test_migracao_nao_afeta_outros_status(db_path: str) -> None:
    """Conforme, Não Conforme e N/A não devem ser tocados."""
    db.init_db()
    did = db.criar_diagnostico("iso27002", "Acme")
    db.salvar_avaliacoes(
        did,
        {
            "5.1": Avaliacao(status="Conforme"),
            "5.2": Avaliacao(status="Não Conforme", remediacao="Não"),
            "5.3": Avaliacao(status="N/A"),
        },
    )
    db.init_db()  # migração

    av = db.carregar_avaliacoes(did)
    assert av["5.1"].status == "Conforme"
    assert av["5.2"].status == "Não Conforme"
    assert av["5.2"].remediacao == "Não"
    assert av["5.3"].status == "N/A"


def test_migracao_via_carregar_avaliacoes_exibe_estado_pos_migracao(db_path: str) -> None:
    """Caminho de leitura padrão: após init_db, o usuário vê o estado migrado."""
    db.init_db()
    did = db.criar_diagnostico("iso27002", "Acme")
    _inserir_parcial_legado(did, "5.4")
    # carregar_avaliacoes não chama init_db; chamamos manual antes.
    db.init_db()
    av = db.carregar_avaliacoes(did)
    assert av["5.4"].status == "Não Conforme"
    assert av["5.4"].remediacao == "Sim"
