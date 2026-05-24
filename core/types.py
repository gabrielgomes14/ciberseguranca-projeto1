from dataclasses import dataclass


@dataclass(frozen=True)
class ItemDiagnostico:
    id: str
    titulo: str
    descricao: str
    categoria_id: str
    modulo: str
    controle_texto: str = ""
    orientacao: str = ""


@dataclass(frozen=True)
class ModuloInfo:
    id: str
    nome: str
    norma: str
    descricao: str
