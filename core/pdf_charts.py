from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.units import cm

from core.scoring import (
    RESPOSTA_CONFORME,
    RESPOSTA_NA,
    RESPOSTA_NAO_AVALIADO,
    RESPOSTA_NAO_CONFORME,
    RESPOSTA_PARCIAL,
    STATUS_COLORS,
    ResultadoTema,
)


def _hx(hex_color: str) -> colors.Color:
    """Atalho para `colors.HexColor`. Tipado para clareza nas anotações."""
    return colors.HexColor(hex_color)


def chart_donut_status(
    resumos: dict[str, ResultadoTema],
    largura_cm: float = 16.0,
    altura_cm: float = 5.5,
) -> Drawing:
    """Gera um pie/donut com a distribuição de status (Conforme/Parcial/Não Conforme/N/A/Não avaliado).

    Agrega contagens vindas de `ResultadoTema` por categoria e desenha apenas as
    fatias com `qtd > 0`. Se não houver dados, retorna um Drawing com a mensagem
    "Sem dados".
    """
    total_conf = sum(r.conformes for r in resumos.values())
    total_parc = sum(r.parciais for r in resumos.values())
    total_nc = sum(r.nao_conformes for r in resumos.values())
    total_na = sum(r.na for r in resumos.values())
    total_itens = sum(r.total for r in resumos.values())
    nao_aval = total_itens - (total_conf + total_parc + total_nc + total_na)

    pares = [
        (RESPOSTA_CONFORME, total_conf),
        (RESPOSTA_PARCIAL, total_parc),
        (RESPOSTA_NAO_CONFORME, total_nc),
        (RESPOSTA_NA, total_na),
        (RESPOSTA_NAO_AVALIADO, nao_aval),
    ]
    visiveis = [(label, qtd) for label, qtd in pares if qtd > 0]

    d = Drawing(largura_cm * cm, altura_cm * cm)
    if not visiveis or total_itens == 0:
        d.add(
            String(
                largura_cm * cm / 2,
                altura_cm * cm / 2,
                "Sem dados",
                textAnchor="middle",
                fontSize=10,
            )
        )
        return d

    pie = Pie()
    pie.x = 10
    pie.y = 10
    pie.width = altura_cm * cm - 20
    pie.height = altura_cm * cm - 20
    pie.data = [qtd for _, qtd in visiveis]
    pie.labels = [str(qtd) for _, qtd in visiveis]
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1.5
    pie.sideLabels = False
    pie.simpleLabels = 1
    for i, (label, _) in enumerate(visiveis):
        pie.slices[i].fillColor = _hx(STATUS_COLORS[label])
        pie.slices[i].fontSize = 9
        pie.slices[i].fontName = "Helvetica-Bold"
        pie.slices[i].labelRadius = 0.65
    d.add(pie)

    legend = Legend()
    legend.x = altura_cm * cm + 10
    legend.y = altura_cm * cm - 20
    legend.deltay = 14
    legend.fontName = "Helvetica"
    legend.fontSize = 9
    legend.colorNamePairs = [(_hx(STATUS_COLORS[label]), f"{label} ({qtd})") for label, qtd in visiveis]
    d.add(legend)
    return d


def chart_radar(
    categorias: dict[str, str],
    resumos: dict[str, ResultadoTema],
    largura_cm: float = 11.0,
    altura_cm: float = 9.0,
) -> Drawing:
    """Renderiza um radar (spider chart) com o score por categoria.

    Exige pelo menos 3 categorias — abaixo disso, retorna um Drawing com a
    mensagem "Radar exige ≥ 3 categorias" (radar com 1 ou 2 vértices não tem
    leitura visual útil).
    """
    labels = [categorias[c] for c in categorias]
    valores = [resumos[c].score for c in categorias]

    d = Drawing(largura_cm * cm, altura_cm * cm)
    if len(labels) < 3:
        d.add(
            String(
                largura_cm * cm / 2,
                altura_cm * cm / 2,
                "Radar exige ≥ 3 categorias",
                textAnchor="middle",
                fontSize=9,
            )
        )
        return d

    spider = SpiderChart()
    spider.x = 30
    spider.y = 25
    spider.width = largura_cm * cm - 60
    spider.height = altura_cm * cm - 50
    spider.data = [valores]
    spider.labels = labels
    spider.strands[0].strokeColor = _hx("#1d4ed8")
    spider.strands[0].strokeWidth = 2
    spider.strands[0].fillColor = colors.Color(29 / 255, 78 / 255, 216 / 255, alpha=0.25)
    spider.strands[0].symbol = "FilledCircle"
    spider.strands[0].symbolSize = 5
    spider.spokeLabels.fontName = "Helvetica"
    spider.spokeLabels.fontSize = 8
    d.add(spider)
    return d
