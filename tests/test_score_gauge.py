import pytest

from components.score_gauge import _hex_to_rgba


def test_hex6_basico() -> None:
    assert _hex_to_rgba("#16a34a", 0.5) == "rgba(22,163,74,0.5)"


def test_hex6_sem_hash() -> None:
    assert _hex_to_rgba("16a34a", 1.0) == "rgba(22,163,74,1.0)"


def test_hex8_alpha_embutido_e_ignorado() -> None:
    # O parâmetro alpha (0.15) tem precedência sobre o byte alpha do hex (CC).
    assert _hex_to_rgba("#16a34acc", 0.15) == "rgba(22,163,74,0.15)"


def test_hex8_branco_com_alpha() -> None:
    assert _hex_to_rgba("#ffffff80", 0.25) == "rgba(255,255,255,0.25)"


@pytest.mark.parametrize(
    "valor",
    [
        "",
        "#",
        "#fff",  # 3 dígitos não suportado
        "#fffffffff",  # 9 dígitos
        "red",
        "rgb(0,0,0)",
    ],
)
def test_formatos_invalidos(valor: str) -> None:
    with pytest.raises(ValueError):
        _hex_to_rgba(valor, 0.5)


def test_hex_invalido_nao_numerico() -> None:
    # 6 dígitos mas com caractere não-hex.
    with pytest.raises(ValueError):
        _hex_to_rgba("#zzzzzz", 0.5)
