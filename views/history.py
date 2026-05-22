import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.db import Snapshot, excluir_snapshot, listar_diagnosticos, listar_snapshots
from core.pdf_report import gerar_pdf_comparativo
from modulos.iso27002.controls import TEMA_LABELS, TEMAS

MODULO_OPCOES = {
    "iso27002": "ISO/IEC 27002:2022",
    "iso27701": "ISO/IEC 27701:2026",
}


def _render_grafico(snapshots: list[Snapshot], categorias_label: dict[str, str]) -> None:
    if not snapshots:
        return
    rotulos = [s.rotulo for s in snapshots]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rotulos,
        y=[s.score_geral for s in snapshots],
        mode="lines+markers",
        name="Geral",
        line={"color": "#1d4ed8", "width": 3},
    ))
    categorias_presentes = sorted({k for s in snapshots for k in s.scores_por_categoria})
    for cat in categorias_presentes:
        valores = [s.scores_por_categoria.get(cat, 0.0) for s in snapshots]
        fig.add_trace(go.Scatter(
            x=rotulos,
            y=valores,
            mode="lines+markers",
            name=categorias_label.get(cat, cat),
            opacity=0.6,
        ))
    fig.update_layout(
        yaxis={"range": [0, 100], "title": "Score"},
        height=420,
        margin={"t": 20, "b": 30, "l": 40, "r": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.25},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def render() -> None:
    st.title("📈 Histórico de Diagnósticos")

    modulo = st.selectbox(
        "Módulo",
        options=list(MODULO_OPCOES.keys()),
        format_func=lambda k: MODULO_OPCOES[k],
        key="hist_modulo",
    )

    diagnosticos = listar_diagnosticos(modulo)
    if not diagnosticos:
        st.info("Nenhum diagnóstico salvo neste módulo.")
        if st.button("Criar / abrir diagnóstico"):
            st.session_state.modulo_alvo = modulo
            st.session_state.page = "diagnosticos"
            st.rerun()
        return

    diag = st.selectbox(
        "Diagnóstico",
        options=diagnosticos,
        format_func=lambda d: f"#{d.id} — {d.organizacao} · auditoria {d.data_auditoria}",
        key="hist_diag",
    )

    snapshots = listar_snapshots(diag.id)
    if not snapshots:
        st.info("Nenhum snapshot registrado. Vá ao dashboard do módulo e clique em **Salvar snapshot**.")
        return

    st.caption(f"{len(snapshots)} snapshot(s) registrado(s).")
    categorias_label = TEMA_LABELS if modulo == "iso27002" else {k: f"{k} {v}" for k, v in _secoes(modulo).items()}
    _render_grafico(snapshots, categorias_label)

    st.divider()
    st.subheader("Tabela de snapshots")
    linhas: list[dict[str, object]] = []
    for s in snapshots:
        base = {
            "Rótulo": s.rotulo,
            "Quando": s.criado_em,
            "Avaliados": s.avaliados,
            "Score Geral": round(s.score_geral, 1),
        }
        if modulo == "iso27002":
            for tema in TEMAS:
                base[TEMA_LABELS[tema]] = round(s.scores_por_categoria.get(tema, 0.0), 1)
        else:
            for cat, label in _secoes(modulo).items():
                base[f"{cat} {label}"] = round(s.scores_por_categoria.get(cat, 0.0), 1)
        linhas.append(base)
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    if len(snapshots) >= 2:
        st.divider()
        _render_comparativo(snapshots, categorias_label, modulo, diag.organizacao)

    st.divider()
    col_l, col_v = st.columns([3, 1])
    with col_l:
        opcoes_remover = [f"#{s.id} — {s.rotulo} ({s.criado_em})" for s in snapshots]
        idx = st.selectbox("Selecionar snapshot para remover", options=[None] + list(range(len(opcoes_remover))), format_func=lambda i: "—" if i is None else opcoes_remover[i])
    with col_v:
        if st.button("Remover", use_container_width=True, disabled=idx is None):
            if idx is not None:
                excluir_snapshot(snapshots[idx].id)
                st.rerun()

    with st.sidebar:
        st.markdown("### Navegação")
        if st.button("🏠 Início", use_container_width=True, key="hist_home"):
            st.session_state.page = "home"
            st.rerun()


_NORMA_LABELS = {
    "iso27002": ("ISO/IEC 27002:2022", "Tema"),
    "iso27701": ("ISO/IEC 27701:2026 — SGPI", "Grupo"),
}


def _render_comparativo(snapshots: list[Snapshot], categorias_label: dict[str, str], modulo: str, organizacao: str) -> None:
    st.subheader("🔍 Comparar auditorias")
    st.caption("Compare dois snapshots para ver evolução, regressões e variações por categoria.")

    opcoes = list(range(len(snapshots)))
    col_a, col_b, col_swap = st.columns([5, 5, 1])
    with col_a:
        idx_a = st.selectbox(
            "Snapshot base (anterior)",
            options=opcoes,
            index=0,
            format_func=lambda i: f"#{snapshots[i].id} — {snapshots[i].rotulo} ({snapshots[i].criado_em})",
            key="cmp_a",
        )
    with col_b:
        idx_b = st.selectbox(
            "Snapshot comparado (mais recente)",
            options=opcoes,
            index=len(snapshots) - 1,
            format_func=lambda i: f"#{snapshots[i].id} — {snapshots[i].rotulo} ({snapshots[i].criado_em})",
            key="cmp_b",
        )
    with col_swap:
        st.write("")
        st.write("")
        if st.button("🔄", help="Inverter A e B", key="cmp_swap"):
            st.session_state.cmp_a, st.session_state.cmp_b = st.session_state.cmp_b, st.session_state.cmp_a
            st.rerun()

    if idx_a == idx_b:
        st.warning("Selecione dois snapshots diferentes para comparar.")
        return

    snap_a = snapshots[idx_a]
    snap_b = snapshots[idx_b]
    delta_geral = snap_b.score_geral - snap_a.score_geral

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Base (A)", f"{snap_a.score_geral:.1f}%", help=f"{snap_a.rotulo}")
    col_m2.metric("Comparado (B)", f"{snap_b.score_geral:.1f}%", help=f"{snap_b.rotulo}")
    col_m3.metric("Δ Score Geral", f"{delta_geral:+.1f} pp", delta=f"{delta_geral:+.1f}")
    col_m4.metric("Δ Avaliados", f"{snap_b.avaliados - snap_a.avaliados:+d}")

    categorias_presentes = sorted(set(snap_a.scores_por_categoria) | set(snap_b.scores_por_categoria))

    fig = go.Figure()
    labels_x = [categorias_label.get(c, c) for c in categorias_presentes]
    valores_a = [snap_a.scores_por_categoria.get(c, 0.0) for c in categorias_presentes]
    valores_b = [snap_b.scores_por_categoria.get(c, 0.0) for c in categorias_presentes]
    fig.add_trace(go.Bar(name=f"A: {snap_a.rotulo}", x=labels_x, y=valores_a, marker_color="#94a3b8"))
    fig.add_trace(go.Bar(name=f"B: {snap_b.rotulo}", x=labels_x, y=valores_b, marker_color="#1d4ed8"))
    fig.update_layout(
        barmode="group",
        yaxis={"range": [0, 100], "title": "Score (%)"},
        height=380,
        margin={"t": 30, "b": 60, "l": 40, "r": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    linhas_delta: list[dict[str, object]] = []
    for cat in categorias_presentes:
        va = snap_a.scores_por_categoria.get(cat, 0.0)
        vb = snap_b.scores_por_categoria.get(cat, 0.0)
        delta = vb - va
        if delta > 0.5:
            tendencia = "📈 melhorou"
        elif delta < -0.5:
            tendencia = "📉 piorou"
        else:
            tendencia = "➡️ estável"
        linhas_delta.append({
            "Categoria": categorias_label.get(cat, cat),
            f"A — {snap_a.rotulo}": round(va, 1),
            f"B — {snap_b.rotulo}": round(vb, 1),
            "Δ (pp)": round(delta, 1),
            "Tendência": tendencia,
        })

    df_delta = pd.DataFrame(linhas_delta).sort_values("Δ (pp)", ascending=False)
    st.dataframe(df_delta, use_container_width=True, hide_index=True)

    melhorou = sum(1 for linha in linhas_delta if isinstance(linha["Δ (pp)"], (int, float)) and float(linha["Δ (pp)"]) > 0.5)
    piorou = sum(1 for linha in linhas_delta if isinstance(linha["Δ (pp)"], (int, float)) and float(linha["Δ (pp)"]) < -0.5)
    estavel = len(linhas_delta) - melhorou - piorou
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.success(f"📈 {melhorou} categoria(s) melhoraram")
    col_s2.warning(f"➡️ {estavel} categoria(s) estáveis")
    col_s3.error(f"📉 {piorou} categoria(s) pioraram")

    dias = _dias_entre(snap_a.criado_em, snap_b.criado_em)
    if dias is not None and dias != 0:
        delta_dia = delta_geral / max(abs(dias), 1)
        st.caption(
            f"⏱️ Intervalo entre snapshots: {dias} dia(s). "
            f"Variação média: {delta_dia:+.2f} pp/dia."
        )

    norma_nome, titulo_cat = _NORMA_LABELS.get(modulo, (modulo, "Categoria"))
    st.download_button(
        "📄 Baixar PDF comparativo (A vs B)",
        data=gerar_pdf_comparativo(
            norma=norma_nome,
            titulo_categoria=titulo_cat,
            categorias_label=categorias_label,
            snap_a=snap_a,
            snap_b=snap_b,
            organizacao=organizacao,
        ),
        file_name=f"relatorio_comparativo_{modulo}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def _secoes(modulo: str) -> dict[str, str]:
    if modulo == "iso27701":
        from modulos.iso27701.controles import CATEGORIAS
        return CATEGORIAS
    return {}


def _dias_entre(iso_a: str, iso_b: str) -> int | None:
    from datetime import datetime
    try:
        da = datetime.fromisoformat(iso_a)
        db = datetime.fromisoformat(iso_b)
    except (TypeError, ValueError):
        return None
    return (db - da).days
