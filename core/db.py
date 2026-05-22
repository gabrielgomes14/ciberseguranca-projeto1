import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from core.models import Avaliacao, avaliacao_de_dict, avaliacao_para_dict

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "diagnosticos.db")
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


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


@dataclass(frozen=True)
class Controle27002Row:
    id: str
    titulo: str
    descricao: str
    tema_id: str


@dataclass(frozen=True)
class Controle27701Row:
    id: str
    titulo: str
    descricao: str
    categoria_id: str


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

CREATE TABLE IF NOT EXISTS iso27002_tema (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS iso27002_controle (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tema_id TEXT NOT NULL,
    FOREIGN KEY (tema_id) REFERENCES iso27002_tema(id)
);

CREATE TABLE IF NOT EXISTS iso27701_categoria (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS iso27701_controle (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    categoria_id TEXT NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES iso27701_categoria(id)
);

CREATE INDEX IF NOT EXISTS idx_diag_modulo ON diagnostico(modulo);
CREATE INDEX IF NOT EXISTS idx_snap_diag ON snapshot(diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_iso27002_controle_tema ON iso27002_controle(tema_id);
CREATE INDEX IF NOT EXISTS idx_iso27701_controle_categoria ON iso27701_controle(categoria_id);
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


def _seed_catalogo(con: sqlite3.Connection) -> None:
    """Popula as tabelas de catálogo a partir dos JSONs em `data/` quando vazias.

    Idempotente: usa `INSERT OR IGNORE` para que execuções repetidas não dupliquem
    nem sobrescrevam edições eventuais. Se um arquivo de seed estiver ausente,
    levanta `FileNotFoundError` em vez de silenciar — o catálogo é dado obrigatório.
    """
    n_temas = con.execute("SELECT COUNT(*) FROM iso27002_tema").fetchone()[0]
    n_27002 = con.execute("SELECT COUNT(*) FROM iso27002_controle").fetchone()[0]
    n_cats = con.execute("SELECT COUNT(*) FROM iso27701_categoria").fetchone()[0]
    n_27701 = con.execute("SELECT COUNT(*) FROM iso27701_controle").fetchone()[0]

    if all(n > 0 for n in (n_temas, n_27002, n_cats, n_27701)):
        return

    iso27002_json = _DATA_DIR / "iso27002.json"
    iso27701_json = _DATA_DIR / "iso27701.json"
    if not iso27002_json.exists() or not iso27701_json.exists():
        raise FileNotFoundError(f"Arquivos de seed do catálogo não encontrados em {_DATA_DIR}. Esperado: iso27002.json, iso27701.json.")

    iso27002 = json.loads(iso27002_json.read_text(encoding="utf-8"))
    iso27701 = json.loads(iso27701_json.read_text(encoding="utf-8"))

    con.executemany(
        "INSERT OR IGNORE INTO iso27002_tema (id, label) VALUES (?, ?)",
        list(iso27002["temas"].items()),
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27002_controle (id, titulo, descricao, tema_id) VALUES (?, ?, ?, ?)",
        [(c["id"], c["titulo"], c["descricao"], c["tema_id"]) for c in iso27002["controles"]],
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27701_categoria (id, label) VALUES (?, ?)",
        list(iso27701["categorias"].items()),
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27701_controle (id, titulo, descricao, categoria_id) VALUES (?, ?, ?, ?)",
        [(c["id"], c["titulo"], c["descricao"], c["categoria_id"]) for c in iso27701["controles"]],
    )


def init_db() -> None:
    with conexao() as con:
        con.executescript(_SCHEMA)
        _migrar(con)
        _seed_catalogo(con)


def listar_temas_iso27002() -> dict[str, str]:
    init_db()
    with conexao() as con:
        rows = con.execute("SELECT id, label FROM iso27002_tema ORDER BY id").fetchall()
    return {str(r["id"]): str(r["label"]) for r in rows}


def listar_controles_iso27002() -> list[Controle27002Row]:
    init_db()
    with conexao() as con:
        rows = con.execute(
            "SELECT id, titulo, descricao, tema_id FROM iso27002_controle ORDER BY id",
        ).fetchall()
    return [
        Controle27002Row(
            id=str(r["id"]),
            titulo=str(r["titulo"]),
            descricao=str(r["descricao"]),
            tema_id=str(r["tema_id"]),
        )
        for r in rows
    ]


def listar_categorias_iso27701() -> dict[str, str]:
    init_db()
    with conexao() as con:
        rows = con.execute("SELECT id, label FROM iso27701_categoria ORDER BY id").fetchall()
    return {str(r["id"]): str(r["label"]) for r in rows}


def listar_controles_iso27701() -> list[Controle27701Row]:
    init_db()
    with conexao() as con:
        rows = con.execute(
            "SELECT id, titulo, descricao, categoria_id FROM iso27701_controle ORDER BY id",
        ).fetchall()
    return [
        Controle27701Row(
            id=str(r["id"]),
            titulo=str(r["titulo"]),
            descricao=str(r["descricao"]),
            categoria_id=str(r["categoria_id"]),
        )
        for r in rows
    ]


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _hoje_iso() -> str:
    return date.today().isoformat()


def criar_diagnostico(modulo: str, organizacao: str, data_auditoria: str | None = None) -> int:
    agora = _agora()
    data_aud = (data_auditoria or "").strip() or _hoje_iso()
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO diagnostico (modulo, organizacao, data_auditoria, criado_em, atualizado_em) VALUES (?, ?, ?, ?, ?)",
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
