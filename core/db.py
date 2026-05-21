import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime

from core.models import Avaliacao, avaliacao_de_dict, avaliacao_para_dict

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "diagnosticos.db")


def _db_path() -> str:
    return os.environ.get("DIAGNOSTICO_DB_PATH", _DEFAULT_PATH)

@dataclass(frozen=True)
class Diagnostico:
    id: int
    modulo: str
    organizacao: str
    data_auditoria: str
    criado_em: str
    atualizado_em: str

@dataclass(frozen=True)
class Snapshot:
    id: int
    diagnostico_id: int
    rotulo: str
    criado_em: str
    score_geral: float
    scores_por_categoria: dict[str, float]
    avaliados: int

_SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnostico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modulo TEXT NOT NULL,
    organizacao TEXT NOT NULL,
    data_auditoria TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS avaliacao (
    diagnostico_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '',
    criticidade TEXT NOT NULL DEFAULT 'Média',
    responsavel TEXT NOT NULL DEFAULT '',
    prazo TEXT NOT NULL DEFAULT '',
    observacao TEXT NOT NULL DEFAULT '',
    remediacao TEXT NOT NULL DEFAULT '',
    evidencias TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (diagnostico_id, item_id),
    FOREIGN KEY (diagnostico_id) REFERENCES diagnostico(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diagnostico_id INTEGER NOT NULL,
    rotulo TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    score_geral REAL NOT NULL,
    scores_por_categoria TEXT NOT NULL,
    avaliados INTEGER NOT NULL,
    FOREIGN KEY (diagnostico_id) REFERENCES diagnostico(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_diag_modulo ON diagnostico(modulo);
CREATE INDEX IF NOT EXISTS idx_snap_diag ON snapshot(diagnostico_id);
"""


@contextmanager
def conexao() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(_db_path())
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _migrar(con: sqlite3.Connection) -> None:
    cols_diag = {r["name"] for r in con.execute("PRAGMA table_info(diagnostico)")}
    if "data_auditoria" not in cols_diag:
        con.execute("ALTER TABLE diagnostico ADD COLUMN data_auditoria TEXT NOT NULL DEFAULT ''")
        con.execute("UPDATE diagnostico SET data_auditoria = substr(criado_em, 1, 10) WHERE data_auditoria = ''")

    cols_av = {r["name"] for r in con.execute("PRAGMA table_info(avaliacao)")}
    if "remediacao" not in cols_av:
        con.execute("ALTER TABLE avaliacao ADD COLUMN remediacao TEXT NOT NULL DEFAULT ''")


def init_db() -> None:
    with conexao() as con:
        con.executescript(_SCHEMA)
        _migrar(con)


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _hoje_iso() -> str:
    return date.today().isoformat()


def criar_diagnostico(modulo: str, organizacao: str, data_auditoria: str | None = None) -> int:
    agora = _agora()
    data_aud = (data_auditoria or "").strip() or _hoje_iso()
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO diagnostico (modulo, organizacao, data_auditoria, criado_em, atualizado_em) "
            "VALUES (?, ?, ?, ?, ?)",
            (modulo, organizacao, data_aud, agora, agora),
        )
        return int(cur.lastrowid or 0)


def listar_diagnosticos(modulo: str | None = None) -> list[Diagnostico]:
    with conexao() as con:
        if modulo:
            rows = con.execute(
                "SELECT * FROM diagnostico WHERE modulo = ? ORDER BY atualizado_em DESC",
                (modulo,),
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM diagnostico ORDER BY atualizado_em DESC").fetchall()
    return [
        Diagnostico(
            id=int(r["id"]),
            modulo=str(r["modulo"]),
            organizacao=str(r["organizacao"]),
            data_auditoria=str(r["data_auditoria"] or ""),
            criado_em=str(r["criado_em"]),
            atualizado_em=str(r["atualizado_em"]),
        )
        for r in rows
    ]


def carregar_avaliacoes(diagnostico_id: int) -> dict[str, Avaliacao]:
    with conexao() as con:
        rows = con.execute(
            "SELECT * FROM avaliacao WHERE diagnostico_id = ?",
            (diagnostico_id,),
        ).fetchall()
    resultado: dict[str, Avaliacao] = {}
    for r in rows:
        try:
            evidencias = json.loads(r["evidencias"] or "[]")
        except json.JSONDecodeError:
            evidencias = []
        d: dict[str, object] = {
            "status": r["status"],
            "criticidade": r["criticidade"],
            "responsavel": r["responsavel"],
            "prazo": r["prazo"],
            "observacao": r["observacao"],
            "remediacao": r["remediacao"] if "remediacao" in r.keys() else "",
            "evidencias": evidencias,
        }
        resultado[str(r["item_id"])] = avaliacao_de_dict(d)
    return resultado


def salvar_avaliacoes(diagnostico_id: int, avaliacoes: dict[str, Avaliacao]) -> None:
    with conexao() as con:
        con.execute("DELETE FROM avaliacao WHERE diagnostico_id = ?", (diagnostico_id,))
        for item_id, a in avaliacoes.items():
            d = avaliacao_para_dict(a)
            con.execute(
                """INSERT INTO avaliacao
                   (diagnostico_id, item_id, status, criticidade, responsavel, prazo, observacao, remediacao, evidencias)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    diagnostico_id,
                    item_id,
                    d["status"],
                    d["criticidade"],
                    d["responsavel"],
                    d["prazo"],
                    d["observacao"],
                    d["remediacao"],
                    json.dumps(d["evidencias"], ensure_ascii=False),
                ),
            )
        con.execute(
            "UPDATE diagnostico SET atualizado_em = ? WHERE id = ?",
            (_agora(), diagnostico_id),
        )


def atualizar_diagnostico(diagnostico_id: int, organizacao: str, data_auditoria: str) -> None:
    with conexao() as con:
        con.execute(
            "UPDATE diagnostico SET organizacao = ?, data_auditoria = ?, atualizado_em = ? WHERE id = ?",
            (organizacao, data_auditoria, _agora(), diagnostico_id),
        )


def excluir_diagnostico(diagnostico_id: int) -> None:
    with conexao() as con:
        con.execute("DELETE FROM diagnostico WHERE id = ?", (diagnostico_id,))


def salvar_snapshot(
    diagnostico_id: int,
    rotulo: str,
    score_geral: float,
    scores_por_categoria: dict[str, float],
    avaliados: int,
) -> int:
    with conexao() as con:
        cur = con.execute(
            """INSERT INTO snapshot (diagnostico_id, rotulo, criado_em, score_geral, scores_por_categoria, avaliados)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                diagnostico_id,
                rotulo or _agora(),
                _agora(),
                score_geral,
                json.dumps(scores_por_categoria, ensure_ascii=False),
                avaliados,
            ),
        )
        return int(cur.lastrowid or 0)


def listar_snapshots(diagnostico_id: int) -> list[Snapshot]:
    with conexao() as con:
        rows = con.execute(
            "SELECT * FROM snapshot WHERE diagnostico_id = ? ORDER BY criado_em ASC",
            (diagnostico_id,),
        ).fetchall()
    out: list[Snapshot] = []
    for r in rows:
        try:
            scores = json.loads(r["scores_por_categoria"] or "{}")
        except json.JSONDecodeError:
            scores = {}
        out.append(
            Snapshot(
                id=int(r["id"]),
                diagnostico_id=int(r["diagnostico_id"]),
                rotulo=str(r["rotulo"]),
                criado_em=str(r["criado_em"]),
                score_geral=float(r["score_geral"]),
                scores_por_categoria={str(k): float(v) for k, v in scores.items()},
                avaliados=int(r["avaliados"]),
            )
        )
    return out


def excluir_snapshot(snapshot_id: int) -> None:
    with conexao() as con:
        con.execute("DELETE FROM snapshot WHERE id = ?", (snapshot_id,))
