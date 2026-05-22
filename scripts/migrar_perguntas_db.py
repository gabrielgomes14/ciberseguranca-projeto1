from typing import Sequence, cast

from core.db import (
    Controle27002Like,
    Controle27701Like,
    init_db,
    salvar_categorias_iso27701,
    salvar_controles_iso27002,
    salvar_controles_iso27701,
    salvar_temas_iso27002,
)
from modulos.iso27002.controls import TEMA_LABELS, TODOS_CONTROLES
from modulos.iso27701.controles import CATEGORIAS, CONTROLES


def main() -> None:
    init_db()
    salvar_temas_iso27002(TEMA_LABELS)
    salvar_controles_iso27002(cast(Sequence[Controle27002Like], TODOS_CONTROLES))
    salvar_categorias_iso27701(CATEGORIAS)
    salvar_controles_iso27701(cast(Sequence[Controle27701Like], CONTROLES))
    print("OK: perguntas migradas para o SQLite")


if __name__ == "__main__":
    main()
