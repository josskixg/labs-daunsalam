"""
Visualisasi data DPPH yang sudah tersimpan.
"""

import pandas as pd
import streamlit as st

from utils.cache import read_dpph
from utils.calculations import classify_ic50, fit_linear
from utils.ui import setup_page, page_header

setup_page("Visualisasi DPPH", icon="chart_with_upwards_trend")
page_header("Visualisasi Data DPPH")

with st.spinner("Memuat data..."):
    df = read_dpph()

if df.empty:
    st.warning("Belum ada data. Input dulu di halaman Input DPPH.")
    st.stop()

# Coerce tipe
num_cols = [
    "waktu_inkubasi_menit",
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
    "ic50_ppm",
    "r_squared",
]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# -------------------- Sidebar filter --------------------
with st.sidebar:
    st.header("Filter")
    sampel_opts = ["(semua)"] + sorted(df["sampel"].dropna().unique().tolist())
    f_sampel = st.selectbox("Sampel", sampel_opts)
    metode_opts = ["(semua)"] + sorted(
        df["metode_ekstraksi"].dropna().unique().tolist()
    )
    f_metode = st.selectbox("Metode ekstraksi", metode_opts)

    waktu_opts = sorted(
        df["waktu_inkubasi_menit"].dropna().unique().astype(int).tolist()
    )
    f_waktu = st.multiselect("Waktu inkubasi (menit)", waktu_opts, default=waktu_opts)

mask = pd.Series(True, index=df.index)
if f_sampel != "(semua)":
    mask &= df["sampel"] == f_sampel
if f_metode != "(semua)":
    mask &= df["metode_ekstraksi"] == f_metode
if f_waktu:
    mask &= df["waktu_inkubasi_menit"].isin(f_waktu)
dff = df[mask].copy()

if dff.empty:
    st.info("Tidak ada data sesuai filter.")
    st.stop()

# -------------------- Ringkasan --------------------
st.subheader("Ringkasan IC50 per Percobaan")
summary = (
    dff.dropna(subset=["experiment_id"])
    .groupby(
        [
            "experiment_id",
            "tanggal",
            "sampel",
            "metode_ekstraksi",
            "waktu_inkubasi_menit",
        ],
        as_index=False,
    )
    .agg(ic50_ppm=("ic50_ppm", "first"), r_squared=("r_squared", "first"))
    .sort_values("ic50_ppm")
)
summary["kategori"] = summary["ic50_ppm"].apply(classify_ic50)
st.dataframe(summary.reset_index(drop=True), use_container_width=True, hide_index=True)

# -------------------- Detail percobaan --------------------
st.subheader("Detail Percobaan")
exp_id = st.selectbox("Pilih experiment_id", options=summary["experiment_id"].tolist())
sub = (
    dff[dff["experiment_id"] == exp_id]
    .sort_values("konsentrasi")
    .reset_index(drop=True)
)

c1, c2, c3, c4 = st.columns(4)
ic50 = sub["ic50_ppm"].iloc[0]
r2 = sub["r_squared"].iloc[0]
c1.metric("IC50", f"{ic50:.2f} ppm")
c2.metric("R-squared", f"{r2:.4f}" if pd.notna(r2) else "-")
c3.metric("Waktu inkubasi", f"{int(sub['waktu_inkubasi_menit'].iloc[0])} mnt")
c4.metric("Kategori", classify_ic50(ic50))

reg = fit_linear(sub["konsentrasi"], sub["inhib_mean"])

# Lazy import plotly
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

tab1, tab2 = st.tabs(["Kurva regresi", "Bar chart"])

with tab1:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=reg.x,
            y=reg.y,
            mode="markers+text",
            text=[f"{v:.1f}" for v in reg.y],
            textposition="top center",
            error_y=dict(
                type="data",
                array=sub.dropna(subset=["inhib_mean"])["inhib_sd"].values,
            ),
            name="% inhibisi rata-rata",
            marker=dict(size=12, color="#2E7D32"),
        )
    )
    if pd.notna(reg.slope):
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
            x=reg.ic50,
            line_dash="dot",
            annotation_text=f"IC50 = {reg.ic50:.2f} ppm",
        )
    fig.update_layout(
        xaxis_title="Konsentrasi (ppm)",
        yaxis_title="% Inhibisi",
        height=480,
        autosize=True,
        margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    bar_df = sub.dropna(subset=["inhib_mean"])
    fig2 = px.bar(
        bar_df,
        x="konsentrasi",
        y="inhib_mean",
        error_y="inhib_sd",
        labels={"konsentrasi": "Konsentrasi (ppm)", "inhib_mean": "% Inhibisi"},
        color="inhib_mean",
        color_continuous_scale="Greens",
    )
    fig2.update_layout(height=480, coloraxis_showscale=False, autosize=True)
    st.plotly_chart(fig2, use_container_width=True)

# -------------------- Perbandingan antar waktu inkubasi --------------------
st.divider()
st.subheader("Perbandingan IC50 antar Waktu Inkubasi")

if summary["waktu_inkubasi_menit"].nunique() > 1:
    fig3 = px.line(
        summary.sort_values("waktu_inkubasi_menit"),
        x="waktu_inkubasi_menit",
        y="ic50_ppm",
        color="sampel",
        markers=True,
        labels={
            "waktu_inkubasi_menit": "Waktu inkubasi (menit)",
            "ic50_ppm": "IC50 (ppm)",
        },
    )
    fig3.update_layout(height=400, autosize=True)
    st.plotly_chart(fig3, use_container_width=True)

    best = summary.loc[summary["ic50_ppm"].idxmin()]
    st.success(
        f"Waktu inkubasi terbaik: **{int(best['waktu_inkubasi_menit'])} menit** "
        f"(IC50 = {best['ic50_ppm']:.2f} ppm — {classify_ic50(best['ic50_ppm'])})"
    )
else:
    st.info(
        "Tambahkan percobaan dengan waktu inkubasi berbeda untuk melihat perbandingan."
    )

# -------------------- Download --------------------
st.divider()
dl1, dl2 = st.columns(2)

with dl1:
    st.download_button(
        "Download data terfilter (CSV)",
        data=dff.to_csv(index=False).encode("utf-8"),
        file_name="dpph_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dl2:
    # Generate PDF on demand untuk percobaan terpilih
    if st.button("Generate Laporan PDF (percobaan terpilih)", use_container_width=True):
        try:
            from utils.pdf_report import build_report

            with st.spinner("Membuat PDF..."):
                pdf_bytes = build_report(sub)
            st.session_state["last_pdf"] = pdf_bytes
            st.session_state["last_pdf_name"] = f"laporan_{exp_id}.pdf"
        except Exception as e:
            st.error(f"Gagal generate PDF: {e}")

if "last_pdf" in st.session_state:
    st.download_button(
        "Download PDF siap pakai",
        data=st.session_state["last_pdf"],
        file_name=st.session_state.get("last_pdf_name", "laporan.pdf"),
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
