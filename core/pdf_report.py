import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.action_plan import AcaoPlano
from core.models import Avaliacao
from core.pdf_charts import (
    chart_barras_categoria,
    chart_donut_status,
    chart_prioridades,
    chart_radar,
)
from core.scoring import (
    RESPOSTA_NAO_AVALIADO,
    STATUS_COLORS,
    resumo_tema,
    score_geral,
    status_individual,
    status_label,
)
from core.types import ItemDiagnostico
from modulos.iso27001.controls import TEMA_LABELS, TEMAS, Controle

_PRIMARY = colors.HexColor("#1d4ed8")
_INK = colors.HexColor("#0f172a")
_MUTED = colors.HexColor("#475569")
_BORDER = colors.HexColor("#cbd5e1")
_BG_LIGHT = colors.HexColor("#f1f5f9")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontSize=22, textColor=_INK, spaceAfter=4),
        "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontSize=11, textColor=_MUTED, spaceAfter=14),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, textColor=_PRIMARY, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, textColor=_INK, leading=14),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=9, textColor=_INK, leading=12),
        "cell_muted": ParagraphStyle("cell_muted", parent=base["Normal"], fontSize=9, textColor=_MUTED, leading=12),
    }


def _barra(score: float, largura_cm: float = 8.0) -> Table:
    """Renderiza uma barra de progresso colorida conforme `status_label(score)`."""
    largura = largura_cm * cm
    preenchido = max(0.01, min(score / 100.0, 1.0)) * largura
    cor = colors.HexColor(STATUS_COLORS[status_label(score)])
    fg = Table([[""]], colWidths=[preenchido], rowHeights=[0.5 * cm])
    fg.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), cor)]))
    container = Table([[fg, ""]], colWidths=[preenchido, largura - preenchido], rowHeights=[0.5 * cm])
    container.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (1, 0), (1, 0), _BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return container


def _badge_status(label: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    cor = colors.HexColor(STATUS_COLORS.get(label, STATUS_COLORS[RESPOSTA_NAO_AVALIADO]))
    return Paragraph(f'<font color="{cor.hexval()}"><b>{label}</b></font>', styles["cell"])


def _tabela_estilo() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BG_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.25, _BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )


def _gerar_pdf_base(
    norma: str,
    titulo_categoria: str,
    label_item: str,
    itens: list[ItemDiagnostico],
    categorias: dict[str, str],
    itens_por_categoria: dict[str, list[ItemDiagnostico]],
    avaliacoes: dict[str, Avaliacao],
    acoes: list[AcaoPlano] | None,
    organizacao: str,
    ponderado: bool,
    data_auditoria: str = "",
) -> bytes:
    """Gera um PDF executivo de conformidade independente da norma.

    Permite reuso entre 27001 (requisitos por seção), 27001 (controles por tema)
    e 27701 (controles por categoria). O parâmetro `acoes` é opcional: se `None`,
    a seção "Plano de Ação" é omitida (útil para normas que não modelam plano).

    Layout: cabeçalho, sumário executivo, gráficos vetoriais (donut, radar,
    barras), tabela tabular por categoria, plano de ação opcional (com gráfico
    de prioridades) e detalhamento completo dos itens.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Relatório {norma}",
        author="Diagnóstico de Conformidade",
    )
    s = _styles()
    flow: list[object] = []

    # Cabeçalho
    flow.append(Paragraph(f"Relatório de Conformidade - {norma}", s["titulo"]))
    subtitulo_partes = [organizacao]
    if data_auditoria:
        subtitulo_partes.append(f"Data da auditoria: {data_auditoria}")
    subtitulo_partes.append(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    flow.append(Paragraph(" · ".join(subtitulo_partes), s["subtitulo"]))

    # Sumário Executivo
    todos_ids = [it.id for it in itens]
    score_total = score_geral(avaliacoes, todos_ids, ponderado=ponderado)
    avaliados = sum(1 for it in itens if avaliacoes.get(it.id, Avaliacao()).status)
    total_na = sum(1 for it in itens if avaliacoes.get(it.id, Avaliacao()).status == "N/A")

    flow.append(Paragraph("Sumário Executivo", s["h2"]))
    cabecalho = Table(
        [
            [
                Paragraph(f"<b>{score_total:.1f}%</b>", s["body"]),
                _barra(score_total, 10),
                Paragraph(f"<b>{status_label(score_total)}</b>", s["body"]),
            ]
        ],
        colWidths=[2.0 * cm, 11.0 * cm, 4.0 * cm],
    )
    cabecalho.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow.append(cabecalho)
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(
        Paragraph(
            f"Foram avaliados <b>{avaliados}</b> de <b>{len(itens)}</b> {label_item.lower()}s. "
            f"Dos avaliados, <b>{total_na}</b> são <b>Não Aplicáveis (N/A)</b> e estão "
            f"excluídos do cálculo do score. "
            f"Critério de pontuação: {'ponderado por criticidade' if ponderado else 'simples'}.",
            s["body"],
        )
    )

    # Resumos por categoria (usados na tabela)
    resumos = {
        cat_id: resumo_tema(
            avaliacoes,
            cat_id,
            [it.id for it in itens_por_categoria.get(cat_id, [])],
            ponderado=ponderado,
        )
        for cat_id in categorias
    }

    # Distribuição dos status (donut)
    flow.append(Paragraph("Distribuição dos Status", s["h2"]))
    flow.append(chart_donut_status(resumos))

    # Radar de aderência por categoria (apenas se houver ≥ 3 categorias)
    if len(categorias) >= 3:
        flow.append(Paragraph(f"Aderência por {titulo_categoria} (Radar)", s["h2"]))
        flow.append(chart_radar(categorias, resumos))

    # Barras de score por categoria
    flow.append(Paragraph(f"Score por {titulo_categoria}", s["h2"]))
    flow.append(chart_barras_categoria(categorias, resumos))

    # Resultado tabular por categoria
    flow.append(Paragraph(f"Resultado Tabular por {titulo_categoria}", s["h2"]))
    linhas_cat: list[list[object]] = [[titulo_categoria, "Score", "Status", "Conformes", "Em Adequação", "Não Conf.", "N/A"]]
    for cat_id, cat_label in categorias.items():
        r = resumos[cat_id]
        linhas_cat.append(
            [
                Paragraph(cat_label, s["cell"]),
                Paragraph(f"{r.score:.1f}%", s["cell"]),
                _badge_status(status_label(r.score), s),
                Paragraph(str(r.conformes), s["cell"]),
                Paragraph(str(r.em_adequacao), s["cell"]),
                Paragraph(str(r.nao_conformes), s["cell"]),
                Paragraph(str(r.na), s["cell"]),
            ]
        )
    tabela_cat = Table(linhas_cat, colWidths=[5 * cm, 2 * cm, 3 * cm, 2 * cm, 2 * cm, 2 * cm, 1.5 * cm])
    tabela_cat.setStyle(_tabela_estilo())
    flow.append(tabela_cat)

    # Plano de Ação (opcional)
    if acoes is not None:
        flow.append(PageBreak())
        flow.append(Paragraph("Plano de Ação", s["h2"]))
        if not acoes:
            flow.append(Paragraph("Nenhuma ação pendente.", s["body"]))
        else:
            qtds: dict[str, int] = {}
            for ac in acoes:
                qtds[ac.prioridade] = qtds.get(ac.prioridade, 0) + 1
            flow.append(Paragraph("Distribuição por Prioridade", s["body"]))
            flow.append(chart_prioridades(qtds))
            flow.append(Spacer(1, 0.3 * cm))
            flow.append(Paragraph("Ações Prioritárias", s["body"]))
            linhas_acoes: list[list[object]] = [[label_item, "Título", "Prioridade", "Remediação em andamento", "Prazo"]]
            for a in acoes[:40]:
                linhas_acoes.append(
                    [
                        Paragraph(a.controle_id, s["cell"]),
                        Paragraph(a.titulo, s["cell"]),
                        _badge_status(a.prioridade, s),
                        Paragraph(a.remediacao or "-", s["cell_muted"]),
                        Paragraph(a.prazo or "-", s["cell_muted"]),
                    ]
                )
            tabela_acoes = Table(linhas_acoes, colWidths=[1.8 * cm, 5.5 * cm, 2.2 * cm, 5.5 * cm, 2.3 * cm])
            tabela_acoes.setStyle(_tabela_estilo())
            flow.append(tabela_acoes)
            if len(acoes) > 40:
                flow.append(Spacer(1, 0.2 * cm))
                flow.append(
                    Paragraph(
                        f"Mostrando 40 de {len(acoes)} ações. Exporte o CSV para a lista completa.",
                        s["cell_muted"],
                    )
                )

    # Detalhamento completo
    flow.append(PageBreak())
    flow.append(Paragraph(f"Detalhamento Completo dos {label_item}s", s["h2"]))
    linhas_det: list[list[object]] = [[label_item, "Título", "Status", "Criticidade"]]
    for it in itens:
        av = avaliacoes.get(it.id, Avaliacao())
        label = status_individual(av if av.status else None)
        linhas_det.append(
            [
                Paragraph(it.id, s["cell"]),
                Paragraph(it.titulo, s["cell"]),
                _badge_status(label, s),
                Paragraph(av.criticidade if av.status else "-", s["cell_muted"]),
            ]
        )
    tabela_det = Table(linhas_det, colWidths=[1.8 * cm, 9.5 * cm, 3.2 * cm, 2.5 * cm], repeatRows=1)
    tabela_det.setStyle(_tabela_estilo())
    flow.append(tabela_det)

    flow.append(Spacer(1, 0.5 * cm))
    flow.append(
        Paragraph(
            "Documento gerado automaticamente. Resultados refletem auto-avaliação e não substituem auditoria independente.",
            s["cell_muted"],
        )
    )

    doc.build(flow)
    return buffer.getvalue()


def gerar_pdf(
    controles: list[Controle],
    avaliacoes: dict[str, Avaliacao],
    acoes: list[AcaoPlano],
    organizacao: str = "Organização",
    ponderado: bool = True,
    data_auditoria: str = "",
) -> bytes:
    """Gera o PDF executivo de conformidade ISO/IEC 27001:2022."""
    itens: list[ItemDiagnostico] = [
        ItemDiagnostico(id=c.id, titulo=c.titulo, descricao=c.descricao, categoria_id=c.tema_id, modulo="iso27001") for c in controles
    ]
    itens_por_categoria = {tema_id: [it for it in itens if it.categoria_id == tema_id] for tema_id in TEMAS}
    return _gerar_pdf_base(
        norma="ISO/IEC 27001:2022",
        titulo_categoria="Tema",
        label_item="Controle",
        itens=itens,
        categorias=TEMA_LABELS,
        itens_por_categoria=itens_por_categoria,
        avaliacoes=avaliacoes,
        acoes=acoes,
        organizacao=organizacao,
        ponderado=ponderado,
        data_auditoria=data_auditoria,
    )


def gerar_pdf_27001(
    requisitos: list[ItemDiagnostico],
    secoes: dict[str, str],
    requisitos_por_secao: dict[str, list[ItemDiagnostico]],
    avaliacoes: dict[str, Avaliacao],
    organizacao: str = "Organização",
    ponderado: bool = True,
    data_auditoria: str = "",
) -> bytes:
    """Gera o PDF executivo de conformidade ISO/IEC 27001:2022 (SGSI).

    Diferente do 27001, a 27001 organiza os itens em "seções/cláusulas" e não
    possui plano de ação no relatório (por isso `acoes=None` em `_gerar_pdf_base`).
    Os parâmetros `secoes` e `requisitos_por_secao` vêm do catálogo da norma
    (definido em `modulos/iso27001/clausulas.py`), mantendo `core/pdf_report.py`
    desacoplado do módulo.
    """
    return _gerar_pdf_base(
        norma="ISO/IEC 27001:2022 - SGSI",
        titulo_categoria="Seção",
        label_item="Requisito",
        itens=requisitos,
        categorias=secoes,
        itens_por_categoria=requisitos_por_secao,
        avaliacoes=avaliacoes,
        acoes=None,
        organizacao=organizacao,
        ponderado=ponderado,
        data_auditoria=data_auditoria,
    )


def gerar_pdf_27701(
    controles: list[ItemDiagnostico],
    categorias: dict[str, str],
    controles_por_categoria: dict[str, list[ItemDiagnostico]],
    avaliacoes: dict[str, Avaliacao],
    organizacao: str = "Organização",
    ponderado: bool = True,
    data_auditoria: str = "",
) -> bytes:
    """Gera o PDF executivo de conformidade ISO/IEC 27701:2019 (SGPI).

    A 27701 organiza os itens em "categorias" (privacidade) e, como a 27001,
    não inclui plano de ação no relatório. Os parâmetros de catálogo vêm do
    chamador (definidos em `modulos/iso27701/...`), mantendo este módulo
    desacoplado do módulo da norma.
    """
    return _gerar_pdf_base(
        norma="ISO/IEC 27701:2019 - SGPI",
        titulo_categoria="Categoria",
        label_item="Controle",
        itens=controles,
        categorias=categorias,
        itens_por_categoria=controles_por_categoria,
        avaliacoes=avaliacoes,
        acoes=None,
        organizacao=organizacao,
        ponderado=ponderado,
        data_auditoria=data_auditoria,
    )


def gerar_pdf_comparativo(
    norma: str,
    titulo_categoria: str,
    categorias_label: dict[str, str],
    snap_a: object,
    snap_b: object,
    organizacao: str = "Organização",
) -> bytes:
    """Gera PDF comparativo entre dois snapshots persistidos (A vs B).

    Os parâmetros `snap_a` e `snap_b` são tipados como `object` para evitar
    acoplar este módulo a `core.db.Snapshot`. Espera-se que tenham os atributos:
    `score_geral` (float), `scores_por_categoria` (dict[str, float]),
    `rotulo` (str), `criado_em` (str) e `avaliados` (int).
    """
    score_a = float(getattr(snap_a, "score_geral", 0.0))
    score_b = float(getattr(snap_b, "score_geral", 0.0))
    rotulo_a = str(getattr(snap_a, "rotulo", ""))
    rotulo_b = str(getattr(snap_b, "rotulo", ""))
    quando_a = str(getattr(snap_a, "criado_em", ""))
    quando_b = str(getattr(snap_b, "criado_em", ""))
    scores_a: dict[str, float] = dict(getattr(snap_a, "scores_por_categoria", {}) or {})
    scores_b: dict[str, float] = dict(getattr(snap_b, "scores_por_categoria", {}) or {})
    avaliados_a = int(getattr(snap_a, "avaliados", 0))
    avaliados_b = int(getattr(snap_b, "avaliados", 0))
    delta_geral = score_b - score_a

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Relatório Comparativo {norma}",
        author="Diagnóstico de Conformidade",
    )
    s = _styles()
    flow: list[object] = []

    flow.append(Paragraph(f"Relatório Comparativo - {norma}", s["titulo"]))
    flow.append(
        Paragraph(
            f"{organizacao} · A: <b>{rotulo_a}</b> ({quando_a}) → "
            f"B: <b>{rotulo_b}</b> ({quando_b}) · "
            f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            s["subtitulo"],
        )
    )

    # Variação geral
    flow.append(Paragraph("Variação Geral", s["h2"]))
    seta = "↑" if delta_geral > 0 else ("↓" if delta_geral < 0 else "→")
    if delta_geral > 0:
        cor_delta = colors.HexColor("#16a34a")
    elif delta_geral < 0:
        cor_delta = colors.HexColor("#dc2626")
    else:
        cor_delta = colors.HexColor("#475569")
    cabecalho = Table(
        [
            [
                Paragraph(f"<b>A: {score_a:.1f}%</b>", s["body"]),
                Paragraph(f"<b>B: {score_b:.1f}%</b>", s["body"]),
                Paragraph(
                    f'<font color="{cor_delta.hexval()}"><b>{seta} Δ {delta_geral:+.1f} pp</b></font>',
                    s["body"],
                ),
                Paragraph(f"Avaliados A: {avaliados_a}", s["cell_muted"]),
                Paragraph(f"Avaliados B: {avaliados_b}", s["cell_muted"]),
            ]
        ],
        colWidths=[3.5 * cm, 3.5 * cm, 4.5 * cm, 3.0 * cm, 3.0 * cm],
    )
    cabecalho.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow.append(cabecalho)

    # Variação por categoria
    flow.append(Paragraph(f"Variação por {titulo_categoria}", s["h2"]))
    cats = sorted(set(scores_a) | set(scores_b))
    linhas_cmp: list[list[object]] = [[titulo_categoria, "A (%)", "B (%)", "Δ (pp)", "Tendência"]]
    melhorou = piorou = estavel = 0
    for cat in cats:
        va = scores_a.get(cat, 0.0)
        vb = scores_b.get(cat, 0.0)
        delta = vb - va
        if delta > 0.5:
            tend = "Melhorou"
            melhorou += 1
            cor = colors.HexColor("#16a34a")
        elif delta < -0.5:
            tend = "Piorou"
            piorou += 1
            cor = colors.HexColor("#dc2626")
        else:
            tend = "Estável"
            estavel += 1
            cor = colors.HexColor("#475569")
        linhas_cmp.append(
            [
                Paragraph(categorias_label.get(cat, cat), s["cell"]),
                Paragraph(f"{va:.1f}", s["cell"]),
                Paragraph(f"{vb:.1f}", s["cell"]),
                Paragraph(f'<font color="{cor.hexval()}"><b>{delta:+.1f}</b></font>', s["cell"]),
                Paragraph(f'<font color="{cor.hexval()}"><b>{tend}</b></font>', s["cell"]),
            ]
        )
    tabela_cmp = Table(linhas_cmp, colWidths=[7.0 * cm, 2.2 * cm, 2.2 * cm, 2.4 * cm, 3.2 * cm])
    tabela_cmp.setStyle(_tabela_estilo())
    flow.append(tabela_cmp)

    # Síntese
    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Síntese", s["h2"]))
    flow.append(
        Paragraph(
            f"📈 <b>{melhorou}</b> categoria(s) melhoraram · ➡️ <b>{estavel}</b> estáveis · 📉 <b>{piorou}</b> pioraram.",
            s["body"],
        )
    )
    if delta_geral > 0:
        flow.append(
            Paragraph(
                f"O score geral subiu <b>{delta_geral:+.1f} pp</b>, indicando evolução da postura de conformidade.",
                s["body"],
            )
        )
    elif delta_geral < 0:
        flow.append(
            Paragraph(
                f"O score geral caiu <b>{delta_geral:.1f} pp</b>. Recomenda-se investigar as categorias com maior regressão.",
                s["body"],
            )
        )
    else:
        flow.append(Paragraph("O score geral permaneceu estável entre as auditorias.", s["body"]))

    flow.append(Spacer(1, 0.5 * cm))
    flow.append(
        Paragraph(
            "Documento gerado automaticamente a partir dos snapshots persistidos em SQLite.",
            s["cell_muted"],
        )
    )

    doc.build(flow)
    return buffer.getvalue()
