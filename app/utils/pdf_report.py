"""
Generator PDF report per percobaan DPPH (untuk lampiran tesis).

Pakai reportlab (pure Python, gak butuh dependency native).
Chart di-render lewat plotly + kaleido sebagai PNG.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

from .calculations import classify_ic50, fit_linear


# ----------------------------------------------------------------------
def _kurva_png(df: pd.DataFrame) -> bytes | None:
    """Render kurva regresi sebagai PNG via plotly+kaleido. Return None kalau gagal."""
    try:
        import plotly.graph_objects as go
    except Exception:
        return None

    sub = df.dropna(subset=["inhib_mean"]).sort_values("konsentrasi")
    reg = fit_linear(sub["konsentrasi"], sub["inhib_mean"])
    if pd.isna(reg.slope):
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=reg.x,
            y=reg.y,
            mode="markers+text",
            text=[f"{v:.1f}" for v in reg.y],
            textposition="top center",
            error_y=dict(type="data", array=sub["inhib_sd"].values),
            name="% inhibisi rata-rata",
            marker=dict(size=10, color="#2E7D32"),
        )
    )
    xs = np.linspace(0, sub["konsentrasi"].max() * 1.1, 50)
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=reg.predict(xs),
            mode="lines",
            name=reg.equation,
            line=dict(color="#1B5E20"),
        )
    )
    fig.add_hline(y=50, line_dash="dot")
    fig.add_vline(
        x=reg.ic50, line_dash="dot", annotation_text=f"IC50 = {reg.ic50:.2f} ppm"
    )
    fig.update_layout(
        xaxis_title="Konsentrasi (ppm)",
        yaxis_title="% Inhibisi",
        width=760,
        height=440,
        margin=dict(l=60, r=20, t=30, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
    )
    fig.update_xaxes(gridcolor="#E0E0E0")
    fig.update_yaxes(gridcolor="#E0E0E0")
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None


# ----------------------------------------------------------------------
def _df_to_table(
    df: pd.DataFrame, col_widths_cm: list[float] | None = None, round_floats: int = 4
) -> Table:
    """Convert DataFrame ke reportlab Table dengan style hijau."""
    df_disp = df.copy()
    for col in df_disp.columns:
        df_disp[col] = df_disp[col].apply(
            lambda v: round(v, round_floats)
            if isinstance(v, float) and not pd.isna(v)
            else v
        )
    data = [list(df_disp.columns)] + df_disp.fillna("-").astype(str).values.tolist()

    widths = [w * cm for w in col_widths_cm] if col_widths_cm else None
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0BEC5")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F1F8E9")],
                ),
            ]
        )
    )
    return t


# ----------------------------------------------------------------------
def build_report(
    experiment_df: pd.DataFrame,
    footer: str = "Tesis Panji Setya Amitra (7789240009) - UNTIRTA",
) -> bytes:
    """
    Build PDF report dari 1 percobaan DPPH.

    experiment_df: rows (1 percobaan, multi-konsentrasi) yang sudah ada
                   experiment_id, tanggal, ic50_ppm, abs_*, inhib_*, dst.

    Return: bytes PDF.
    """
    df = experiment_df.copy().sort_values("konsentrasi").reset_index(drop=True)
    meta = df.iloc[0]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Laporan DPPH - {meta.get('experiment_id', '')}",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#1B5E20"),
        fontSize=16,
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#2E7D32"),
        fontSize=12,
        spaceBefore=12,
    )
    body = styles["BodyText"]
    small = ParagraphStyle(
        "Small", parent=body, fontSize=8.5, textColor=colors.HexColor("#555555")
    )

    story = []

    # ---------- Header ----------
    story.append(Paragraph("Laporan Uji Aktivitas Antioksidan Metode DPPH", h1))
    story.append(
        Paragraph(
            "Platform Digital Evaluasi Antioksidan Daun Salam (UAE)",
            small,
        )
    )
    story.append(Spacer(1, 8))

    # ---------- Metadata ----------
    ic50 = float(meta.get("ic50_ppm", float("nan")))
    r2 = float(meta.get("r_squared", float("nan")))
    meta_table = pd.DataFrame(
        [
            ["Experiment ID", str(meta.get("experiment_id", "-"))],
            ["Tanggal", str(meta.get("tanggal", "-"))],
            ["Sampel", str(meta.get("sampel", "-"))],
            ["Metode ekstraksi", str(meta.get("metode_ekstraksi", "-"))],
            ["Waktu inkubasi", f"{int(meta.get('waktu_inkubasi_menit', 0))} menit"],
            ["IC50", f"{ic50:.2f} ppm" if pd.notna(ic50) else "-"],
            ["Kategori", classify_ic50(ic50)],
            ["R-squared", f"{r2:.4f}" if pd.notna(r2) else "-"],
            ["Persamaan regresi", str(meta.get("persamaan_regresi", "-"))],
            ["Catatan", str(meta.get("catatan") or "-")],
            ["Dibuat", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ],
        columns=["Field", "Nilai"],
    )
    story.append(Paragraph("Metadata Percobaan", h2))
    story.append(_df_to_table(meta_table, col_widths_cm=[5, 11]))

    # ---------- Tabel data ----------
    story.append(Paragraph("Data Absorbansi & % Inhibisi", h2))
    cols = [
        "konsentrasi",
        "abs_1",
        "abs_2",
        "abs_3",
        "abs_mean",
        "inhib_1",
        "inhib_2",
        "inhib_3",
        "inhib_mean",
        "inhib_sd",
    ]
    tdf = df[[c for c in cols if c in df.columns]].copy()
    tdf.columns = [
        "Konsen.\n(ppm)",
        "Abs 1",
        "Abs 2",
        "Abs 3",
        "Abs\nmean",
        "Inh 1\n(%)",
        "Inh 2\n(%)",
        "Inh 3\n(%)",
        "Inh mean\n(%)",
        "SD",
    ]
    story.append(_df_to_table(tdf, col_widths_cm=[1.6] * len(tdf.columns)))

    # ---------- Kurva regresi ----------
    story.append(Paragraph("Kurva Regresi Linear", h2))
    png = _kurva_png(df)
    if png:
        story.append(Image(io.BytesIO(png), width=16 * cm, height=9.3 * cm))
    else:
        story.append(
            Paragraph(
                "<i>Chart tidak dapat dirender (kaleido tidak tersedia). "
                "Install dengan: pip install kaleido</i>",
                small,
            )
        )

    # ---------- Kesimpulan ----------
    story.append(Paragraph("Kesimpulan", h2))
    if pd.notna(ic50):
        story.append(
            Paragraph(
                f"Sampel <b>{meta.get('sampel', '-')}</b> menunjukkan nilai "
                f"<b>IC50 = {ic50:.2f} ppm</b> dengan kategori "
                f"<b>{classify_ic50(ic50)}</b> (Molyneux, 2004) pada waktu inkubasi "
                f"{int(meta.get('waktu_inkubasi_menit', 0))} menit. "
                f"Persamaan regresi {meta.get('persamaan_regresi', '-')} "
                f"memberikan nilai R-squared = {r2:.4f}.",
                body,
            )
        )

    # ---------- Footer ----------
    story.append(Spacer(1, 24))
    story.append(Paragraph(footer, small))
    story.append(
        Paragraph(
            "Dihasilkan otomatis oleh Platform Digital Evaluasi Antioksidan",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()
