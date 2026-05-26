"""API de alto nível para a trilha de auditoria.

Wrapper sobre `core.db.registrar_evento` que:

* expõe constantes (`Acao`) com os nomes oficiais dos eventos, evitando
  strings mágicas espalhadas pelo código;
* engole exceções para garantir que uma falha no log nunca interrompa a
  operação que o usuário está executando (em SGSI o log é importante,
  mas perder um evento é menos grave do que impedir o auditor de salvar
  uma avaliação). Falhas são reportadas no logger Python `audit` para
  diagnóstico do operador.

Quando a autenticação for implementada, basta as views passarem
`usuario_email=st.user.email` em cada chamada - a API já aceita o campo.
"""

import logging
from typing import Final

from core.db import registrar_evento

_log = logging.getLogger("audit")


class Acao:
    """Constantes com os nomes canônicos das ações registradas na trilha.

    Use esses identificadores em vez de literais para evitar typos e
    facilitar a busca de todos os pontos onde uma ação é registrada.
    """

    DIAGNOSTICO_CRIADO: Final = "diagnostico.criado"
    DIAGNOSTICO_ATUALIZADO: Final = "diagnostico.atualizado"
    DIAGNOSTICO_EXCLUIDO: Final = "diagnostico.excluido"
    AVALIACOES_SALVAS: Final = "avaliacoes.salvas"
    SNAPSHOT_CRIADO: Final = "snapshot.criado"
    SNAPSHOT_EXCLUIDO: Final = "snapshot.excluido"


class AlvoTipo:
    """Constantes com os tipos de alvo - facilitam filtros consistentes."""

    DIAGNOSTICO: Final = "diagnostico"
    SNAPSHOT: Final = "snapshot"
    USUARIO: Final = "usuario"


def registrar(
    acao: str,
    *,
    usuario_email: str | None = None,
    alvo_tipo: str | None = None,
    alvo_id: str | int | None = None,
    detalhes: dict[str, object] | None = None,
) -> None:
    """Persiste um evento de auditoria, sem propagar exceções.

    `alvo_id` aceita int por conveniência (ex.: `diagnostico.id`); é convertido
    para str na persistência para permitir alvos heterogêneos (emails, UUIDs).

    Em caso de falha (banco indisponível, disco cheio, etc.) o evento é perdido
    e um aviso é emitido no logger Python `audit`. A operação principal segue
    sem ser afetada.
    """
    try:
        registrar_evento(
            acao,
            usuario_email=usuario_email,
            alvo_tipo=alvo_tipo,
            alvo_id=str(alvo_id) if alvo_id is not None else None,
            detalhes=detalhes or {},
        )
    except Exception as e:  # noqa: BLE001 - propósito explícito é não vazar
        _log.warning("Falha ao registrar evento de auditoria %r: %s", acao, e)
