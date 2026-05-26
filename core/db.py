import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
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
    usuario_email: str | None = None


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
class Controle27001Row:
    id: str
    titulo: str
    descricao: str
    tema_id: str
    controle_texto: str = ""
    orientacao: str = ""


@dataclass(frozen=True)
class Controle27701Row:
    id: str
    titulo: str
    descricao: str
    categoria_id: str
    controle_texto: str = ""
    orientacao: str = ""


@dataclass(frozen=True)
class Usuario:
    """Conta de auditor para login local. Senha é hash bcrypt."""

    email: str
    nome: str
    senha_hash: str
    criado_em: str
    ativo: bool = True


@dataclass(frozen=True)
class EventoAuditoria:
    """Registro imutável de uma ação relevante no sistema.

    `usuario_email` é opcional: enquanto a autenticação não estiver implementada,
    eventos são registrados sem identificação. `detalhes` é JSON serializado.
    """

    id: int
    quando: str
    acao: str
    usuario_email: str | None = None
    alvo_tipo: str | None = None
    alvo_id: str | None = None
    detalhes: dict[str, object] = field(default_factory=dict)



_SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnostico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modulo TEXT NOT NULL,
    organizacao TEXT NOT NULL,
    data_auditoria TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    usuario_email TEXT
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

CREATE TABLE IF NOT EXISTS iso27001_tema (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS iso27001_controle (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tema_id TEXT NOT NULL,
    controle_texto TEXT NOT NULL DEFAULT '',
    orientacao TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (tema_id) REFERENCES iso27001_tema(id)
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
    controle_texto TEXT NOT NULL DEFAULT '',
    orientacao TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (categoria_id) REFERENCES iso27701_categoria(id)
);

CREATE INDEX IF NOT EXISTS idx_diag_modulo ON diagnostico(modulo);
CREATE INDEX IF NOT EXISTS idx_snap_diag ON snapshot(diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_iso27001_controle_tema ON iso27001_controle(tema_id);
CREATE INDEX IF NOT EXISTS idx_iso27701_controle_categoria ON iso27701_controle(categoria_id);

CREATE TABLE IF NOT EXISTS usuario (
    email TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quando TEXT NOT NULL,
    usuario_email TEXT,
    acao TEXT NOT NULL,
    alvo_tipo TEXT,
    alvo_id TEXT,
    detalhes TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_quando ON audit_log(quando DESC);
CREATE INDEX IF NOT EXISTS idx_audit_alvo ON audit_log(alvo_tipo, alvo_id);
CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_log(usuario_email);
CREATE INDEX IF NOT EXISTS idx_audit_acao ON audit_log(acao);
"""


@contextmanager
def conexao() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _seed_catalogo(con: sqlite3.Connection) -> None:
    """Popula as tabelas de catálogo a partir dos JSONs em `data/` quando vazias.

    Idempotente: usa `INSERT OR IGNORE` para que execuções repetidas não dupliquem
    nem sobrescrevam edições eventuais. Se um arquivo de seed estiver ausente,
    levanta `FileNotFoundError` em vez de silenciar - o catálogo é dado obrigatório.
    """
    n_temas = con.execute("SELECT COUNT(*) FROM iso27001_tema").fetchone()[0]
    n_27001 = con.execute("SELECT COUNT(*) FROM iso27001_controle").fetchone()[0]
    n_cats = con.execute("SELECT COUNT(*) FROM iso27701_categoria").fetchone()[0]
    n_27701 = con.execute("SELECT COUNT(*) FROM iso27701_controle").fetchone()[0]

    if all(n > 0 for n in (n_temas, n_27001, n_cats, n_27701)):
        return

    iso27001_json = _DATA_DIR / "iso27001.json"
    iso27701_json = _DATA_DIR / "iso27701.json"
    if not iso27001_json.exists() or not iso27701_json.exists():
        raise FileNotFoundError(f"Arquivos de seed do catálogo não encontrados em {_DATA_DIR}. Esperado: iso27001.json, iso27701.json.")

    iso27001 = json.loads(iso27001_json.read_text(encoding="utf-8"))
    iso27701 = json.loads(iso27701_json.read_text(encoding="utf-8"))

    con.executemany(
        "INSERT OR IGNORE INTO iso27001_tema (id, label) VALUES (?, ?)",
        list(iso27001["temas"].items()),
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27001_controle (id, titulo, descricao, tema_id, controle_texto, orientacao) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                c["id"],
                c["titulo"],
                c["descricao"],
                c["tema_id"],
                c.get("controle_texto", ""),
                c.get("orientacao", ""),
            )
            for c in iso27001["controles"]
        ],
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27701_categoria (id, label) VALUES (?, ?)",
        list(iso27701["categorias"].items()),
    )
    con.executemany(
        "INSERT OR IGNORE INTO iso27701_controle (id, titulo, descricao, categoria_id, controle_texto, orientacao) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                c["id"],
                c["titulo"],
                c["descricao"],
                c["categoria_id"],
                c.get("controle_texto", ""),
                c.get("orientacao", ""),
            )
            for c in iso27701["controles"]
        ],
    )


def _seed_demo(con: sqlite3.Connection) -> None:
    """Popula um diagnóstico demo por norma se não houver nenhum diagnóstico real.

    Lê `data/diagnostico_demo.json` e insere 2 diagnósticos (27001 e 27701) com
    suas avaliações e 3 snapshots cada. Pula completamente se o banco já tem
    qualquer diagnóstico - protegendo o usuário de re-seed após criar dados reais.

    Diferente do seed de catálogo, o JSON do demo é opcional: se o arquivo não
    existir (ex.: instalação minimalista), apenas pula sem erro.

    Pode ser desabilitado via env `DIAGNOSTICO_SEED_DEMO=0` (útil em testes que
    contam diagnósticos e não querem o ruído do demo).
    """
    if os.environ.get("DIAGNOSTICO_SEED_DEMO", "1") == "0":
        return

    n_diag = con.execute("SELECT COUNT(*) FROM diagnostico").fetchone()[0]
    if n_diag > 0:
        return

    demo_json = _DATA_DIR / "diagnostico_demo.json"
    if not demo_json.exists():
        return

    payload = json.loads(demo_json.read_text(encoding="utf-8"))
    for d in payload.get("diagnosticos", []):
        cur = con.execute(
            "INSERT INTO diagnostico (modulo, organizacao, data_auditoria, criado_em, atualizado_em) VALUES (?, ?, ?, ?, ?)",
            (d["modulo"], d["organizacao"], d["data_auditoria"], d["criado_em"], d["atualizado_em"]),
        )
        diag_id = cur.lastrowid
        if diag_id is None:
            continue

        con.executemany(
            """INSERT INTO avaliacao
               (diagnostico_id, item_id, status, criticidade, responsavel, prazo,
                observacao, remediacao, evidencias)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    diag_id,
                    av["item_id"],
                    av["status"],
                    av["criticidade"],
                    av["responsavel"],
                    av["prazo"],
                    av["observacao"],
                    av["remediacao"],
                    json.dumps(av["evidencias"], ensure_ascii=False),
                )
                for av in d["avaliacoes"]
            ],
        )

        con.executemany(
            """INSERT INTO snapshot
               (diagnostico_id, rotulo, criado_em, score_geral, scores_por_categoria, avaliados)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (
                    diag_id,
                    snap["rotulo"],
                    snap["criado_em"],
                    snap["score_geral"],
                    json.dumps(snap["scores_por_categoria"], ensure_ascii=False),
                    snap["avaliados"],
                )
                for snap in d["snapshots"]
            ],
        )


def _colunas_tabela(con: sqlite3.Connection, tabela: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({tabela})").fetchall()
    return {str(r["name"]) for r in rows}


def _adicionar_coluna(con: sqlite3.Connection, tabela: str, coluna: str, ddl: str) -> None:
    colunas = _colunas_tabela(con, tabela)
    if coluna not in colunas:
        con.execute(f"ALTER TABLE {tabela} ADD COLUMN {ddl}")


def _migrar(con: sqlite3.Connection) -> None:
    _adicionar_coluna(con, "iso27001_controle", "controle_texto", "controle_texto TEXT NOT NULL DEFAULT ''")
    _adicionar_coluna(con, "iso27001_controle", "orientacao", "orientacao TEXT NOT NULL DEFAULT ''")
    _adicionar_coluna(con, "iso27701_controle", "controle_texto", "controle_texto TEXT NOT NULL DEFAULT ''")
    _adicionar_coluna(con, "iso27701_controle", "orientacao", "orientacao TEXT NOT NULL DEFAULT ''")
    _adicionar_coluna(con, "diagnostico", "usuario_email", "usuario_email TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS idx_diag_usuario ON diagnostico(usuario_email)")


def init_db() -> None:
    with conexao() as con:
        con.executescript(_SCHEMA)
        _migrar(con)
        _seed_catalogo(con)
        _seed_demo(con)


def listar_temas_iso27001() -> dict[str, str]:
    init_db()
    with conexao() as con:
        rows = con.execute("SELECT id, label FROM iso27001_tema ORDER BY id").fetchall()
    return {str(r["id"]): str(r["label"]) for r in rows}


def listar_controles_iso27001() -> list[Controle27001Row]:
    init_db()
    with conexao() as con:
        rows = con.execute(
            "SELECT id, titulo, descricao, tema_id, controle_texto, orientacao FROM iso27001_controle ORDER BY CAST(SUBSTR(id, 1, INSTR(id, '.') - 1) AS INTEGER), CAST(SUBSTR(id, INSTR(id, '.') + 1) AS INTEGER)",
        ).fetchall()
    return [
        Controle27001Row(
            id=str(r["id"]),
            titulo=str(r["titulo"]),
            descricao=str(r["descricao"]),
            tema_id=str(r["tema_id"]),
            controle_texto=str(r["controle_texto"]),
            orientacao=str(r["orientacao"]),
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
            "SELECT id, titulo, descricao, categoria_id, controle_texto, orientacao FROM iso27701_controle ORDER BY id",
        ).fetchall()
    return [
        Controle27701Row(
            id=str(r["id"]),
            titulo=str(r["titulo"]),
            descricao=str(r["descricao"]),
            categoria_id=str(r["categoria_id"]),
            controle_texto=str(r["controle_texto"]),
            orientacao=str(r["orientacao"]),
        )
        for r in rows
    ]


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _hoje_iso() -> str:
    return date.today().isoformat()


def criar_diagnostico(
    modulo: str,
    organizacao: str,
    data_auditoria: str | None = None,
    usuario_email: str | None = None,
) -> int:
    agora = _agora()
    data_aud = (data_auditoria or "").strip() or _hoje_iso()
    email = (usuario_email or "").strip().lower() or None
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO diagnostico (modulo, organizacao, data_auditoria, criado_em, atualizado_em, usuario_email) VALUES (?, ?, ?, ?, ?, ?)",
            (modulo, organizacao, data_aud, agora, agora, email),
        )
        diag_id = int(cur.lastrowid or 0)

    from core import audit  # lazy import: audit.py importa de db.py

    audit.registrar(
        audit.Acao.DIAGNOSTICO_CRIADO,
        usuario_email=email,
        alvo_tipo=audit.AlvoTipo.DIAGNOSTICO,
        alvo_id=diag_id,
        detalhes={"modulo": modulo, "organizacao": organizacao, "data_auditoria": data_aud},
    )
    return diag_id


def listar_diagnosticos(
    modulo: str | None = None,
    usuario_email: str | None = None,
) -> list[Diagnostico]:
    """Lista diagnósticos, opcionalmente filtrando por módulo e/ou usuário.

    Quando `usuario_email` é informado, retorna apenas os diagnósticos do
    próprio usuário e os "públicos" (sem dono - oriundos do seed demo ou de
    bancos antigos antes da migração). Quando não é informado (ex.: bypass
    de dev), retorna todos.
    """
    where: list[str] = []
    params: list[object] = []
    if modulo:
        where.append("modulo = ?")
        params.append(modulo)
    if usuario_email:
        where.append("(usuario_email = ? OR usuario_email IS NULL)")
        params.append(usuario_email.strip().lower())

    sql = "SELECT * FROM diagnostico"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY atualizado_em DESC"

    with conexao() as con:
        rows = con.execute(sql, tuple(params)).fetchall()
    return [
        Diagnostico(
            id=int(r["id"]),
            modulo=str(r["modulo"]),
            organizacao=str(r["organizacao"]),
            data_auditoria=str(r["data_auditoria"] or ""),
            criado_em=str(r["criado_em"]),
            atualizado_em=str(r["atualizado_em"]),
            usuario_email=str(r["usuario_email"]) if r["usuario_email"] is not None else None,
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

    from core import audit

    contagens: dict[str, int] = {}
    for a in avaliacoes.values():
        chave = a.status or "Não avaliado"
        contagens[chave] = contagens.get(chave, 0) + 1
    audit.registrar(
        audit.Acao.AVALIACOES_SALVAS,
        alvo_tipo=audit.AlvoTipo.DIAGNOSTICO,
        alvo_id=diagnostico_id,
        detalhes={"total": len(avaliacoes), "por_status": contagens},
    )


def atualizar_diagnostico(diagnostico_id: int, organizacao: str, data_auditoria: str) -> None:
    with conexao() as con:
        con.execute(
            "UPDATE diagnostico SET organizacao = ?, data_auditoria = ?, atualizado_em = ? WHERE id = ?",
            (organizacao, data_auditoria, _agora(), diagnostico_id),
        )

    from core import audit

    audit.registrar(
        audit.Acao.DIAGNOSTICO_ATUALIZADO,
        alvo_tipo=audit.AlvoTipo.DIAGNOSTICO,
        alvo_id=diagnostico_id,
        detalhes={"organizacao": organizacao, "data_auditoria": data_auditoria},
    )


def excluir_diagnostico(diagnostico_id: int) -> None:
    with conexao() as con:
        con.execute("DELETE FROM diagnostico WHERE id = ?", (diagnostico_id,))

    from core import audit

    audit.registrar(
        audit.Acao.DIAGNOSTICO_EXCLUIDO,
        alvo_tipo=audit.AlvoTipo.DIAGNOSTICO,
        alvo_id=diagnostico_id,
    )


def salvar_snapshot(
    diagnostico_id: int,
    rotulo: str,
    score_geral: float,
    scores_por_categoria: dict[str, float],
    avaliados: int,
) -> int:
    rotulo_final = rotulo or _agora()
    with conexao() as con:
        cur = con.execute(
            """INSERT INTO snapshot (diagnostico_id, rotulo, criado_em, score_geral, scores_por_categoria, avaliados)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                diagnostico_id,
                rotulo_final,
                _agora(),
                score_geral,
                json.dumps(scores_por_categoria, ensure_ascii=False),
                avaliados,
            ),
        )
        snap_id = int(cur.lastrowid or 0)

    from core import audit

    audit.registrar(
        audit.Acao.SNAPSHOT_CRIADO,
        alvo_tipo=audit.AlvoTipo.SNAPSHOT,
        alvo_id=snap_id,
        detalhes={
            "diagnostico_id": diagnostico_id,
            "rotulo": rotulo_final,
            "score_geral": score_geral,
            "avaliados": avaliados,
        },
    )
    return snap_id


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

    from core import audit

    audit.registrar(
        audit.Acao.SNAPSHOT_EXCLUIDO,
        alvo_tipo=audit.AlvoTipo.SNAPSHOT,
        alvo_id=snapshot_id,
    )


def criar_usuario(email: str, nome: str, senha_hash: str) -> None:
    """Persiste um novo usuário. Levanta `ValueError` se o email já existir."""
    email = email.strip().lower()
    with conexao() as con:
        existing = con.execute("SELECT 1 FROM usuario WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ValueError(f"Email já cadastrado: {email}")
        con.execute(
            "INSERT INTO usuario (email, nome, senha_hash, criado_em, ativo) VALUES (?, ?, ?, ?, 1)",
            (email, nome, senha_hash, _agora()),
        )


def listar_usuarios(somente_ativos: bool = True) -> list[Usuario]:
    """Lista todos os usuários cadastrados; por padrão filtra os ativos."""
    sql = "SELECT email, nome, senha_hash, criado_em, ativo FROM usuario"
    if somente_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY criado_em ASC"
    with conexao() as con:
        rows = con.execute(sql).fetchall()
    return [
        Usuario(
            email=str(r["email"]),
            nome=str(r["nome"]),
            senha_hash=str(r["senha_hash"]),
            criado_em=str(r["criado_em"]),
            ativo=bool(r["ativo"]),
        )
        for r in rows
    ]


def buscar_usuario(email: str) -> Usuario | None:
    """Retorna um usuário pelo email ou None se não existir."""
    email = email.strip().lower()
    with conexao() as con:
        row = con.execute(
            "SELECT email, nome, senha_hash, criado_em, ativo FROM usuario WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        return None
    return Usuario(
        email=str(row["email"]),
        nome=str(row["nome"]),
        senha_hash=str(row["senha_hash"]),
        criado_em=str(row["criado_em"]),
        ativo=bool(row["ativo"]),
    )


def atualizar_senha_usuario(email: str, novo_hash: str) -> None:
    """Atualiza o hash da senha de um usuário existente."""
    with conexao() as con:
        con.execute(
            "UPDATE usuario SET senha_hash = ? WHERE email = ?",
            (novo_hash, email.strip().lower()),
        )


def registrar_evento(
    acao: str,
    *,
    usuario_email: str | None = None,
    alvo_tipo: str | None = None,
    alvo_id: str | None = None,
    detalhes: dict[str, object] | None = None,
) -> int:
    """Persiste um evento na tabela `audit_log`.

    Não silencia exceções - quem chama (helper `core.audit.registrar`) decide
    se uma falha de log deve propagar ou ser engolida.
    """
    payload = json.dumps(detalhes or {}, ensure_ascii=False)
    with conexao() as con:
        cur = con.execute(
            """INSERT INTO audit_log (quando, usuario_email, acao, alvo_tipo, alvo_id, detalhes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_agora(), usuario_email, acao, alvo_tipo, alvo_id, payload),
        )
        return int(cur.lastrowid or 0)


def listar_eventos(
    *,
    usuario_email: str | None = None,
    acao: str | None = None,
    alvo_tipo: str | None = None,
    alvo_id: str | None = None,
    desde: str | None = None,
    ate: str | None = None,
    limite: int = 200,
) -> list[EventoAuditoria]:
    """Lista eventos do `audit_log` ordenados do mais recente para o mais antigo.

    Todos os filtros são opcionais e combinam com AND. `desde`/`ate` esperam
    strings ISO 8601 (mesmo formato salvo em `quando`). `limite` evita carregar
    o histórico inteiro de uma vez na UI.
    """
    where: list[str] = []
    params: list[object] = []
    if usuario_email is not None:
        where.append("usuario_email = ?")
        params.append(usuario_email)
    if acao is not None:
        where.append("acao = ?")
        params.append(acao)
    if alvo_tipo is not None:
        where.append("alvo_tipo = ?")
        params.append(alvo_tipo)
    if alvo_id is not None:
        where.append("alvo_id = ?")
        params.append(alvo_id)
    if desde is not None:
        where.append("quando >= ?")
        params.append(desde)
    if ate is not None:
        where.append("quando <= ?")
        params.append(ate)
    sql = "SELECT * FROM audit_log"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY quando DESC, id DESC LIMIT ?"
    params.append(int(limite))

    with conexao() as con:
        rows = con.execute(sql, tuple(params)).fetchall()
    out: list[EventoAuditoria] = []
    for r in rows:
        try:
            detalhes = json.loads(r["detalhes"] or "{}")
        except json.JSONDecodeError:
            detalhes = {}
        out.append(
            EventoAuditoria(
                id=int(r["id"]),
                quando=str(r["quando"]),
                acao=str(r["acao"]),
                usuario_email=str(r["usuario_email"]) if r["usuario_email"] is not None else None,
                alvo_tipo=str(r["alvo_tipo"]) if r["alvo_tipo"] is not None else None,
                alvo_id=str(r["alvo_id"]) if r["alvo_id"] is not None else None,
                detalhes=detalhes,
            )
        )
    return out
