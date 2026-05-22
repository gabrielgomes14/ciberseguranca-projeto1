"""Testa o auto-seed do catálogo ISO via JSON em `data/`."""

import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from core import db


@pytest.fixture
def db_path() -> Iterator[str]:
    """DB temporário isolado por teste, mesmo padrão do test_db.py existente."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    os.environ["DIAGNOSTICO_DB_PATH"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)
    os.environ.pop("DIAGNOSTICO_DB_PATH", None)


def _contagens() -> dict[str, int]:
    """Conta linhas das 4 tabelas de catálogo."""
    with db.conexao() as con:
        return {
            t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in (
                "iso27002_tema",
                "iso27002_controle",
                "iso27701_categoria",
                "iso27701_controle",
            )
        }


def test_seed_popula_catalogo_em_db_vazio(db_path: str) -> None:
    db.init_db()
    c = _contagens()
    # Tamanhos esperados conforme os JSONs em data/.
    assert c["iso27002_tema"] == 4
    assert c["iso27002_controle"] == 93
    assert c["iso27701_categoria"] == 9
    assert c["iso27701_controle"] == 78


def test_seed_e_idempotente(db_path: str) -> None:
    """Reexecutar `init_db` não duplica nem sobrescreve."""
    db.init_db()
    antes = _contagens()
    db.init_db()
    db.init_db()
    depois = _contagens()
    assert antes == depois


def test_seed_preserva_edicoes_existentes(db_path: str) -> None:
    """`INSERT OR IGNORE`: PKs já presentes no DB não são sobrescritas."""
    db.init_db()
    # Edita um label existente.
    with db.conexao() as con:
        con.execute("UPDATE iso27002_tema SET label = ? WHERE id = ?", ("Custom Org", "org"))
    # Reexecutar init_db não deve reverter a edição.
    db.init_db()
    with db.conexao() as con:
        label = con.execute("SELECT label FROM iso27002_tema WHERE id = 'org'").fetchone()[0]
    assert label == "Custom Org"


def test_seed_falha_se_arquivos_ausentes(db_path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Se data/iso27002.json sumir, init_db deve falhar com erro claro."""
    monkeypatch.setattr(db, "_DATA_DIR", tmp_path)  # diretório vazio
    with pytest.raises(FileNotFoundError, match="iso27002.json"):
        db.init_db()


def test_seed_consistente_com_jsons(db_path: str) -> None:
    """Os IDs no DB pós-seed batem com os IDs nos JSONs de origem."""
    db.init_db()
    with open(db._DATA_DIR / "iso27002.json", encoding="utf-8") as f:
        esperado_27002 = {c["id"] for c in json.load(f)["controles"]}
    with open(db._DATA_DIR / "iso27701.json", encoding="utf-8") as f:
        esperado_27701 = {c["id"] for c in json.load(f)["controles"]}

    with db.conexao() as con:
        ids_27002 = {r["id"] for r in con.execute("SELECT id FROM iso27002_controle")}
        ids_27701 = {r["id"] for r in con.execute("SELECT id FROM iso27701_controle")}

    assert ids_27002 == esperado_27002
    assert ids_27701 == esperado_27701
