from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.units import cm

from core.scoring import (
    RESPOSTA_CONFORME,
    RESPOSTA_EM_ADEQUACAO,
    RESPOSTA_NA,
    RESPOSTA_NAO_AVALIADO,
    RESPOSTA_NAO_CONFORME,
    STATUS_COLORS,
    ResultadoTema,
    status_label,
)


def _hx(hex_color: str) -> colors.Color:
    """Atalho para `colors.HexColor`. Tipado para clareza nas anotações."""
    return colors.HexColor(hex_color)


def _id_curto(label: str) -> str:
    """Extrai o identificador curto do label (ex: 'A.1.2 Condições...' -> 'A.1.2').

    Usado em radar/barras quando o label completo é muito longo para caber.
    """
    return label.split(" ", 1)[0] if label else label


def _truncar(label: str, max_len: int = 38) -> str:
    """Trunca labels para caber em barras horizontais."""
    return label if len(label) <= max_len else label[: max_len - 1] + "…"


def chart_donut_status(
    resumos: dict[str, ResultadoTema],
    largura_cm: float = 16.0,
    altura_cm: float = 5.5,
) -> Drawing:
    """Gera um pie/donut com a distribuição de status (Conforme/Em Adequação/Não Conforme/N/A/Não avaliado).

    Agrega contagens vindas de `ResultadoTema` por categoria e desenha apenas as
    fatias com `qtd > 0`. Se não houver dados, retorna um Drawing com a mensagem
    "Sem dados".
    """
    total_conf = sum(r.conformes for r in resumos.values())
    total_em_adequacao = sum(r.em_adequacao for r in resumos.values())
    total_nc = sum(r.nao_conformes for r in resumos.values())
    total_na = sum(r.na for r in resumos.values())
    total_itens = sum(r.total for r in resumos.values())
    nao_aval = total_itens - (total_conf + total_em_adequacao + total_nc + total_na)

    pares = [
        (RESPOSTA_CONFORME, total_conf),
        (RESPOSTA_EM_ADEQUACAO, total_em_adequacao),
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
    pie.slices.strokeWidth = 1.0
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
    largura_cm: float = 14.0,
    altura_cm: float = 11.0,
) -> Drawing:
    """Renderiza um radar (spider chart) com o score por categoria.

    Exige pelo menos 3 categorias - abaixo disso, retorna um Drawing com a
    mensagem "Radar exige ≥ 3 categorias" (radar com 1 ou 2 vértices não tem
    leitura visual útil).

    Os labels nos vértices usam apenas o identificador curto (ex: "A.1.2") para
    evitar sobreposição. O nome completo aparece nas tabelas e barras do PDF.
    """
    labels = [_id_curto(categorias[c]) for c in categorias]
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
    spider.x = 50
    spider.y = 35
    spider.width = largura_cm * cm - 100
    spider.height = altura_cm * cm - 70
    spider.data = [valores]
    spider.labels = labels
    spider.strands[0].strokeColor = _hx("#1d4ed8")
    spider.strands[0].strokeWidth = 2
    spider.strands[0].fillColor = colors.Color(29 / 255, 78 / 255, 216 / 255, alpha=0.25)
    spider.strands[0].symbol = "FilledCircle"
    spider.strands[0].symbolSize = 5
    spider.spokeLabels.fontName = "Helvetica-Bold"
    spider.spokeLabels.fontSize = 9
    d.add(spider)
    return d


def chart_barras_categoria(
    categorias: dict[str, str],
    resumos: dict[str, ResultadoTema],
    largura_cm: float = 16.0,
    altura_cm: float | None = None,
) -> Drawing:
    """Renderiza barras horizontais com o score por categoria.

    Cada barra é colorida conforme `status_label(score)` (verde/laranja/vermelho).
    A altura é calculada automaticamente em função do número de categorias se
    `altura_cm` não for informado.
    """
    labels = [_truncar(categorias[c], 42) for c in categorias]
    valores = [resumos[c].score for c in categorias]
    if altura_cm is None:
        altura_cm = max(4.0, 0.7 * len(labels) + 1.5)

    d = Drawing(largura_cm * cm, altura_cm * cm)

    chart = HorizontalBarChart()
    chart.x = 200
    chart.y = 25
    chart.width = largura_cm * cm - 220
    chart.height = altura_cm * cm - 40
    chart.data = [valores]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 9
    chart.categoryAxis.labels.boxAnchor = "e"
    chart.categoryAxis.labels.dx = -4
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.gridStrokeColor = _hx("#e2e8f0")
    chart.valueAxis.visibleGrid = True
    chart.bars.strokeWidth = 0
    for i, valor in enumerate(valores):
        chart.bars[(0, i)].fillColor = _hx(STATUS_COLORS[status_label(valor)])
    chart.barLabels.fontName = "Helvetica-Bold"
    chart.barLabels.fontSize = 8
    chart.barLabels.nudge = 8
    chart.barLabelFormat = "%.1f%%"
    chart.barLabels.dx = 0
    d.add(chart)
    return d


def chart_prioridades(
    qtds: dict[str, int],
    largura_cm: float = 16.0,
    altura_cm: float = 4.5,
) -> Drawing:
    """Renderiza barras horizontais com a contagem de ações por prioridade.

    Espera as chaves "Crítica", "Alta", "Média", "Baixa" (mesmas geradas por
    `core.action_plan`). Chaves ausentes contam 0. Se não houver ações
    pendentes, retorna um Drawing com a mensagem "Sem ações pendentes".
    """
    ordem = ["Crítica", "Alta", "Média", "Baixa"]
    cores = {
        "Crítica": "#7f1d1d",
        "Alta": "#dc2626",
        "Média": "#d97706",
        "Baixa": "#16a34a",
    }
    valores = [qtds.get(p, 0) for p in ordem]
    d = Drawing(largura_cm * cm, altura_cm * cm)
    if sum(valores) == 0:
        d.add(
            String(
                largura_cm * cm / 2,
                altura_cm * cm / 2,
                "Sem ações pendentes",
                textAnchor="middle",
                fontSize=10,
            )
        )
        return d

    chart = HorizontalBarChart()
    chart.x = 90
    chart.y = 25
    chart.width = largura_cm * cm - 110
    chart.height = altura_cm * cm - 40
    chart.data = [valores]
    chart.categoryAxis.categoryNames = ordem
    chart.categoryAxis.labels.fontName = "Helvetica-Bold"
    chart.categoryAxis.labels.fontSize = 9
    chart.categoryAxis.labels.boxAnchor = "e"
    chart.categoryAxis.labels.dx = -4
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(valores) + max(1, max(valores) // 5)
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.gridStrokeColor = _hx("#e2e8f0")
    chart.valueAxis.visibleGrid = True
    chart.bars.strokeWidth = 0
    for i, prioridade in enumerate(ordem):
        chart.bars[(0, i)].fillColor = _hx(cores[prioridade])
    chart.barLabels.fontName = "Helvetica-Bold"
    chart.barLabels.fontSize = 8
    chart.barLabels.nudge = 6
    chart.barLabelFormat = "%d"
    d.add(chart)
    return d
