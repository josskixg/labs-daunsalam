"""
Analisis ANOVA satu arah + post-hoc Tukey HSD untuk membandingkan
metrik antar grup (mis. waktu inkubasi).

Berguna buat sub-bab "Uji Beda Nyata" di tesis.
"""

import pandas as pd
import streamlit as st

from utils.cache import read_dpph
from utils.calculations import one_way_anova, tukey_hsd, descriptive_stats
from utils.ui import setup_page, page_header

setup_page("Analisis ANOVA", icon="bar_chart")
page_header(
    "Uji Beda Nyata (ANOVA + Tukey HSD)",
    "Membandingkan metrik antar grup secara statistik (alpha = 0.05).",
)

with st.spinner("Memuat data..."):
    df = read_dpph()

if df.empty:
    st.warning("Belum ada data DPPH untuk dianalisis.")
    st.stop()

# Coerce numerik
for c in [
    "waktu_inkubasi_menit",
    "konsentrasi",
    "ic50_ppm",
    "inhib_1",
    "inhib_2",
    "inhib_3",
    "inhib_mean",
]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# -------------------- Konfigurasi analisis --------------------
with st.container(border=True):
    st.subheader("1. Konfigurasi Analisis")

    c1, c2 = st.columns(2)
    metric = c1.selectbox(
        "Metrik yang dibandingkan",
        [
            "IC50 (ppm) - per percobaan",
            "% Inhibisi pada konsentrasi tertentu - per replikasi",
        ],
    )
    grouping = c2.selectbox(
        "Variabel pengelompok",
        ["Waktu inkubasi (menit)", "Metode ekstraksi", "Sampel"],
    )
    alpha = st.slider("Alpha (tingkat signifikansi)", 0.01, 0.10, 0.05, 0.01)

    konsen_pilih = None
    if "konsentrasi tertentu" in metric:
        konsentrasi_opts = sorted(df["konsentrasi"].dropna().unique().tolist())
        konsentrasi_opts = [k for k in konsentrasi_opts if k > 0]
        if not konsentrasi_opts:
            st.error("Tidak ada data konsentrasi non-blanko.")
            st.stop()
        konsen_pilih = st.selectbox("Konsentrasi (ppm)", konsentrasi_opts)

# -------------------- Bangun grup data --------------------
group_col_map = {
    "Waktu inkubasi (menit)": "waktu_inkubasi_menit",
    "Metode ekstraksi": "metode_ekstraksi",
    "Sampel": "sampel",
}
gcol = group_col_map[grouping]

if metric.startswith("IC50"):
    base = (
        df.dropna(subset=["experiment_id", gcol, "ic50_ppm"])
        .groupby("experiment_id", as_index=False)
        .agg(group=(gcol, "first"), value=("ic50_ppm", "first"))
    )
    metric_label = "IC50 (ppm)"
else:
    sub = df[df["konsentrasi"] == konsen_pilih].dropna(subset=[gcol])
    long_rows = []
    for _, r in sub.iterrows():
        for col in ("inhib_1", "inhib_2", "inhib_3"):
            if col in r and pd.notna(r[col]):
                long_rows.append({"group": r[gcol], "value": float(r[col])})
    base = pd.DataFrame(long_rows)
    metric_label = f"% Inhibisi @ {konsen_pilih} ppm"

if base.empty or base["group"].nunique() < 2:
    st.warning(
        "Butuh minimal 2 grup berbeda dengan masing-masing >=2 data. "
        "Tambah lebih banyak percobaan dengan variasi pada variabel pengelompok."
    )
    st.stop()

groups = {
    str(g): base[base["group"] == g]["value"].values
    for g in sorted(base["group"].unique())
}

# -------------------- Statistik deskriptif --------------------
st.subheader("2. Statistik Deskriptif per Grup")
desc = descriptive_stats(groups)
st.dataframe(desc.round(4), use_container_width=True, hide_index=True)

# Boxplot
import plotly.express as px

fig_box = px.box(
    base,
    x="group",
    y="value",
    points="all",
    color="group",
    labels={"group": grouping, "value": metric_label},
)
fig_box.update_layout(showlegend=False, height=420, autosize=True)
st.plotly_chart(fig_box, use_container_width=True)

# -------------------- ANOVA --------------------
st.divider()
st.subheader("3. Hasil ANOVA Satu Arah")

result = one_way_anova(groups, alpha=alpha)

c1, c2, c3, c4 = st.columns(4)
c1.metric("F-statistic", f"{result.f_stat:.4f}" if pd.notna(result.f_stat) else "-")
c2.metric("p-value", f"{result.p_value:.4f}" if pd.notna(result.p_value) else "-")
c3.metric("df between", result.df_between)
c4.metric("df within", result.df_within)

if result.significant_at_005:
    st.success(result.interpretation)
else:
    st.info(result.interpretation)

st.caption(
    f"Total observasi: {result.n_total} dari {result.n_groups} grup. "
    f"H0: rata-rata semua grup sama. H1: minimal 1 grup berbeda."
)

# -------------------- Post-hoc --------------------
st.divider()
st.subheader("4. Post-hoc Tukey HSD")
st.caption(
    "Membandingkan setiap pasangan grup. "
    "`reject=True` artinya pasangan berbeda nyata pada alpha yang dipilih."
)

tukey = tukey_hsd(groups, alpha=alpha)
if tukey.empty:
    st.info("Data tidak cukup untuk Tukey HSD.")
else:
    fmt = tukey.copy()
    for col in ("mean_diff", "p_adj", "ci_lower", "ci_upper"):
        if col in fmt.columns:
            fmt[col] = pd.to_numeric(fmt[col], errors="coerce").round(4)
    st.dataframe(fmt, use_container_width=True, hide_index=True)

    # Highlight pairs yang berbeda nyata
    sig_pairs = tukey[tukey["reject"] == True]
    if not sig_pairs.empty:
        items = [
            f"- **{r['group1']} vs {r['group2']}** "
            f"(mean diff = {float(r['mean_diff']):.3f}, p = {float(r['p_adj']):.4f})"
            for _, r in sig_pairs.iterrows()
        ]
        st.success(
            "Pasangan grup yang **berbeda nyata** secara statistik:\n\n"
            + "\n".join(items)
        )
    else:
        st.info("Tidak ada pasangan grup yang berbeda nyata.")

# -------------------- Download --------------------
st.divider()
out = pd.concat(
    [
        desc.assign(jenis="deskriptif"),
        pd.DataFrame(
            [
                {
                    "jenis": "anova",
                    "F": result.f_stat,
                    "p": result.p_value,
                    "df_b": result.df_between,
                    "df_w": result.df_within,
                }
            ]
        ),
        tukey.assign(jenis="tukey") if not tukey.empty else pd.DataFrame(),
    ],
    ignore_index=True,
)

st.download_button(
    "Download hasil analisis (CSV)",
    data=out.to_csv(index=False).encode("utf-8"),
    file_name=f"anova_{metric_label.replace(' ', '_')}.csv",
    mime="text/csv",
    use_container_width=True,
)
