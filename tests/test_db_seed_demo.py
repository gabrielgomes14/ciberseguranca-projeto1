"""Testa o seed automático de diagnósticos demo via JSON em `data/`."""

import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from core import db


@pytest.fixture
def db_path() -> Iterator[str]:
    """DB temporário com seed demo HABILITADO. Garante limpeza da env após cada teste."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    os.environ["DIAGNOSTICO_DB_PATH"] = path
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)  # default = ativo
    yield path
    if os.path.exists(path):
        os.remove(path)
    os.environ.pop("DIAGNOSTICO_DB_PATH", None)
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)


def _ler_demo_json() -> dict[str, object]:
    raw = json.loads((db._DATA_DIR / "diagnostico_demo.json").read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def test_seed_demo_popula_dois_diagnosticos_em_db_vazio(db_path: str) -> None:
    db.init_db()
    diags = db.listar_diagnosticos()
    assert len(diags) == 2
    modulos = {d.modulo for d in diags}
    assert modulos == {"iso27002", "iso27701"}
    assert all("(exemplo)" in d.organizacao for d in diags)


def test_seed_demo_e_consistente_com_json(db_path: str) -> None:
    """Conteúdo persistido bate com o JSON-fonte: contagens, ids e scores."""
    db.init_db()
    payload = _ler_demo_json()
    diagnosticos_json = payload["diagnosticos"]
    assert isinstance(diagnosticos_json, list)

    diags_por_modulo = {d.modulo: d for d in db.listar_diagnosticos()}

    for d_json in diagnosticos_json:
        assert isinstance(d_json, dict)
        modulo = str(d_json["modulo"])
        diag = diags_por_modulo[modulo]
        avaliacoes_json = d_json["avaliacoes"]
        snapshots_json = d_json["snapshots"]
        assert isinstance(avaliacoes_json, list)
        assert isinstance(snapshots_json, list)

        avaliacoes_db = db.carregar_avaliacoes(diag.id)
        ids_esperados = {str(av["item_id"]) for av in avaliacoes_json if isinstance(av, dict)}
        assert set(avaliacoes_db.keys()) == ids_esperados

        snaps_db = db.listar_snapshots(diag.id)
        for snap_db, snap_json in zip(snaps_db, snapshots_json, strict=True):
            assert isinstance(snap_json, dict)
            assert snap_db.rotulo == snap_json["rotulo"]
            assert snap_db.score_geral == snap_json["score_geral"]


def test_seed_demo_pula_se_db_ja_tem_diagnostico(db_path: str) -> None:
    """Demo não atropela dados reais e o seed continua idempotente."""
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    db.init_db()
    db.criar_diagnostico("iso27002", "Cliente Real S.A.")
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)

    db.init_db()  # demo ativo, mas DB já tem diagnóstico → pula
    db.init_db()  # 2ª chamada também não muda nada

    diags = db.listar_diagnosticos()
    assert len(diags) == 1
    assert diags[0].organizacao == "Cliente Real S.A."


def test_seed_demo_desabilitado_via_env(db_path: str) -> None:
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    db.init_db()
    assert db.listar_diagnosticos() == []


def test_seed_demo_pula_se_arquivo_ausente(db_path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem o JSON, seed pula silenciosamente — não levanta erro (demo é opcional).

    Preserva os JSONs de catálogo, que SÃO obrigatórios; só o de demo é removido.
    """
    catalogo_dir = tmp_path / "data"
    catalogo_dir.mkdir()
    for nome in ("iso27002.json", "iso27701.json"):
        (catalogo_dir / nome).write_text(
            (db._DATA_DIR / nome).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    monkeypatch.setattr(db, "_DATA_DIR", catalogo_dir)

    db.init_db()
    assert db.listar_diagnosticos() == []
