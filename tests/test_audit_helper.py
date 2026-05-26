import logging
import os
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture
def db_path() -> object:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    os.environ["DIAGNOSTICO_DB_PATH"] = path
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    yield path
    if os.path.exists(path):
        os.remove(path)
    os.environ.pop("DIAGNOSTICO_DB_PATH", None)
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)


def test_registrar_persiste_evento(db_path: str) -> None:
    from core.audit import Acao, AlvoTipo, registrar
    from core.db import init_db, listar_eventos

    init_db()
    registrar(
        Acao.DIAGNOSTICO_CRIADO,
        alvo_tipo=AlvoTipo.DIAGNOSTICO,
        alvo_id=42,
        detalhes={"modulo": "iso27001"},
    )
    eventos = listar_eventos()
    assert len(eventos) == 1
    e = eventos[0]
    assert e.acao == "diagnostico.criado"
    assert e.alvo_tipo == "diagnostico"
    assert e.alvo_id == "42"  # convertido para str
    assert e.detalhes == {"modulo": "iso27001"}


def test_registrar_aceita_alvo_id_int_e_str(db_path: str) -> None:
    from core.audit import registrar
    from core.db import init_db, listar_eventos

    init_db()
    registrar("a", alvo_id=1)
    registrar("b", alvo_id="abc")
    registrar("c", alvo_id=None)

    eventos = sorted(listar_eventos(), key=lambda e: e.acao)
    assert eventos[0].alvo_id == "1"
    assert eventos[1].alvo_id == "abc"
    assert eventos[2].alvo_id is None


def test_registrar_engole_excecoes_e_loga(db_path: str, caplog: pytest.LogCaptureFixture) -> None:
    """Se a persistência falha, registrar não pode propagar a exceção."""
    from core import audit

    with patch.object(audit, "registrar_evento", side_effect=RuntimeError("disco cheio")):
        with caplog.at_level(logging.WARNING, logger="audit"):
            # não deve levantar
            audit.registrar("teste.acao")

    assert any("Falha ao registrar evento" in r.message for r in caplog.records)


def test_acao_constantes_unicas() -> None:
    """As constantes de Acao não podem colidir - cada evento tem nome único."""
    from core.audit import Acao

    valores = [v for k, v in vars(Acao).items() if not k.startswith("_") and isinstance(v, str)]
    assert len(valores) == len(set(valores))


def test_alvo_tipo_constantes_unicas() -> None:
    from core.audit import AlvoTipo

    valores = [v for k, v in vars(AlvoTipo).items() if not k.startswith("_") and isinstance(v, str)]
    assert len(valores) == len(set(valores))
