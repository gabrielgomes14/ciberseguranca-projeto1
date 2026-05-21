from dataclasses import dataclass, field

CRITICIDADE_ALTA = "Alta"
CRITICIDADE_MEDIA = "Média"
CRITICIDADE_BAIXA = "Baixa"

CRITICIDADES: tuple[str, ...] = (CRITICIDADE_ALTA, CRITICIDADE_MEDIA, CRITICIDADE_BAIXA)

REMEDIACAO_SIM = "Sim"
REMEDIACAO_NAO = "Não"
REMEDIACAO_OPCOES: tuple[str, ...] = (REMEDIACAO_SIM, REMEDIACAO_NAO)

PESOS: dict[str, float] = {
    CRITICIDADE_ALTA: 3.0,
    CRITICIDADE_MEDIA: 2.0,
    CRITICIDADE_BAIXA: 1.0,
}


@dataclass
class Avaliacao:
    status: str = ""
    observacao: str = ""
    criticidade: str = CRITICIDADE_MEDIA
    responsavel: str = ""
    prazo: str = ""
    remediacao: str = ""
    evidencias: list[str] = field(default_factory=list)


def avaliacao_de_dict(d: dict[str, object]) -> Avaliacao:
    evid_raw = d.get("evidencias") or []
    evidencias = [str(e) for e in evid_raw] if isinstance(evid_raw, list) else []
    return Avaliacao(
        status=str(d.get("status", "")),
        observacao=str(d.get("observacao", "")),
        criticidade=str(d.get("criticidade", CRITICIDADE_MEDIA)),
        responsavel=str(d.get("responsavel", "")),
        prazo=str(d.get("prazo", "")),
        remediacao=str(d.get("remediacao", "")),
        evidencias=evidencias,
    )


def avaliacao_para_dict(a: Avaliacao) -> dict[str, object]:
    return {
        "status": a.status,
        "observacao": a.observacao,
        "criticidade": a.criticidade,
        "responsavel": a.responsavel,
        "prazo": a.prazo,
        "remediacao": a.remediacao,
        "evidencias": list(a.evidencias),
    }
