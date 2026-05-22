"""Testa o seed automático de diagnósticos demo via JSON em `data/`."""

import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from core import db
from core.models import Avaliacao


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


def test_seed_demo_popula_avaliacoes_e_snapshots(db_path: str) -> None:
    db.init_db()
    payload = _ler_demo_json()
    diagnosticos_json = payload["diagnosticos"]
    assert isinstance(diagnosticos_json, list)

    diags = db.listar_diagnosticos()
    diags_por_modulo = {d.modulo: d for d in diags}
    for d_json in diagnosticos_json:
        assert isinstance(d_json, dict)
        modulo = str(d_json["modulo"])
        diag = diags_por_modulo[modulo]
        avaliacoes = db.carregar_avaliacoes(diag.id)
        snapshots = db.listar_snapshots(diag.id)

        avaliacoes_json = d_json["avaliacoes"]
        snapshots_json = d_json["snapshots"]
        assert isinstance(avaliacoes_json, list)
        assert isinstance(snapshots_json, list)
        assert len(avaliacoes) == len(avaliacoes_json)
        assert len(snapshots) == len(snapshots_json)


def test_seed_demo_pula_se_db_ja_tem_diagnostico(db_path: str) -> None:
    """Demo não deve atropelar dados reais do usuário."""
    # Desabilita demo só na primeira chamada, cria diagnóstico real, reabilita demo.
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    db.init_db()
    db.criar_diagnostico("iso27002", "Cliente Real S.A.")
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)

    db.init_db()  # demo ativo, mas DB já tem 1 diagnóstico → deve pular.

    diags = db.listar_diagnosticos()
    assert len(diags) == 1
    assert diags[0].organizacao == "Cliente Real S.A."


def test_seed_demo_e_idempotente(db_path: str) -> None:
    """Após primeira execução, re-init_db não duplica os 2 diagnósticos demo."""
    db.init_db()
    db.init_db()
    db.init_db()
    diags = db.listar_diagnosticos()
    assert len(diags) == 2


def test_seed_demo_desabilitado_via_env(db_path: str) -> None:
    """Env DIAGNOSTICO_SEED_DEMO=0 faz o seed pular mesmo com DB vazio."""
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    db.init_db()
    assert db.listar_diagnosticos() == []


def test_seed_demo_pula_se_arquivo_ausente(db_path: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem o JSON, seed pula silenciosamente — não levanta erro (demo é opcional)."""
    # Aponta _DATA_DIR para diretório temporário; seed catalogo vai falhar antes,
    # então preciso preservar o catálogo e remover só o demo.
    catalogo_dir = tmp_path / "data"
    catalogo_dir.mkdir()
    # Copia só os arquivos de catálogo, deixa diagnostico_demo.json fora.
    for nome in ("iso27002.json", "iso27701.json"):
        (catalogo_dir / nome).write_text(
            (db._DATA_DIR / nome).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    monkeypatch.setattr(db, "_DATA_DIR", catalogo_dir)

    # init_db deve completar sem erro mesmo sem diagnostico_demo.json.
    db.init_db()
    assert db.listar_diagnosticos() == []


def test_seed_demo_scores_dos_snapshots_correspondem_ao_json(db_path: str) -> None:
    """Validação de fidelidade: scores no DB batem com os scores no JSON."""
    db.init_db()
    payload = _ler_demo_json()
    diagnosticos_json = payload["diagnosticos"]
    assert isinstance(diagnosticos_json, list)

    diags = db.listar_diagnosticos()
    diags_por_modulo = {d.modulo: d for d in diags}
    for d_json in diagnosticos_json:
        assert isinstance(d_json, dict)
        modulo = str(d_json["modulo"])
        diag = diags_por_modulo[modulo]
        snaps_db = db.listar_snapshots(diag.id)

        snapshots_json = d_json["snapshots"]
        assert isinstance(snapshots_json, list)
        # Snapshots vêm ordenados por criado_em ASC; idem no JSON.
        for snap_db, snap_json in zip(snaps_db, snapshots_json, strict=True):
            assert isinstance(snap_json, dict)
            assert snap_db.rotulo == snap_json["rotulo"]
            assert snap_db.score_geral == snap_json["score_geral"]


def test_seed_demo_usuario_pode_apagar_demo_e_criar_real(db_path: str) -> None:
    """Cenário real: usuário apaga demo e cria seu próprio diagnóstico."""
    db.init_db()
    diags_demo = db.listar_diagnosticos()
    for d in diags_demo:
        db.excluir_diagnostico(d.id)

    # Próximo init_db NÃO deve repopular o demo (DB já foi tocado).
    # Mas como excluir zerou o DB... seed dispararia. Para simular "usuário decidiu não querer demo",
    # ele cria primeiro o diagnóstico real:
    novo_id = db.criar_diagnostico("iso27002", "Real Co.")
    db.salvar_avaliacoes(novo_id, {"5.1": Avaliacao(status="Conforme")})
    db.init_db()  # não deve seedar demo de novo

    diags = db.listar_diagnosticos()
    assert len(diags) == 1
    assert diags[0].organizacao == "Real Co."
