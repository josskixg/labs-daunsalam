"""
Input absorbansi DPPH untuk 1 percobaan, hitung otomatis,
preview hasil, simpan ke storage (Google Sheets atau CSV).
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

from utils import storage, auth
from utils.cache import clear_caches
from utils.calculations import process_experiment, classify_ic50
from utils.ui import setup_page, page_header

setup_page("Input DPPH", icon="memo")
page_header("Input Data DPPH", f"Backend: {storage.backend_name()}")

auth.login_widget()
auth.logout_widget()

# -------------------- Metadata --------------------
with st.container(border=True):
    st.subheader("1. Metadata Percobaan")
    m1, m2, m3 = st.columns(3)
    tanggal = m1.date_input("Tanggal", value=date.today())
    sampel = m2.text_input("Sampel", value="Daun Salam Ekstrak Etanol")
    metode = m3.selectbox(
        "Metode ekstraksi",
        ["UAE", "Maserasi", "Soxhlet", "MAE", "Lainnya"],
        index=0,
    )
    waktu_inkubasi = st.select_slider(
        "Waktu inkubasi (menit)",
        options=[5, 6, 7, 8, 9, 10, 15, 20, 30],
        value=5,
    )
    catatan = st.text_input(
        "Catatan (opsional)", placeholder="mis. UAE 30 menit, etanol 70%"
    )

# -------------------- Input absorbansi --------------------
with st.container(border=True):
    st.subheader("2. Absorbansi (3 replikasi)")
    st.caption(
        "Konsentrasi 0 ppm = blanko (DPPH + pelarut). Setiap konsentrasi diukur 3 kali."
    )

    default_df = pd.DataFrame(
        {
            "konsentrasi": [0, 20, 40, 60, 80, 100],
            "abs_1": [0.667, 0.469, 0.399, 0.268, 0.141, 0.051],
            "abs_2": [0.669, 0.464, 0.398, 0.267, 0.142, 0.053],
            "abs_3": [0.671, 0.465, 0.392, 0.267, 0.142, 0.055],
        }
    )

    df_input = st.data_editor(
        default_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "konsentrasi": st.column_config.NumberColumn(
                "Konsentrasi (ppm)",
                min_value=0,
                step=1,
            ),
            "abs_1": st.column_config.NumberColumn("Abs 1", format="%.4f"),
            "abs_2": st.column_config.NumberColumn("Abs 2", format="%.4f"),
            "abs_3": st.column_config.NumberColumn("Abs 3", format="%.4f"),
        },
        key="abs_editor",
    )

# -------------------- Preview hasil --------------------
preview_clicked = st.button("Hitung Preview", type="secondary")

if preview_clicked or st.session_state.get("preview_done"):
    st.session_state["preview_done"] = True
    try:
        df_proc, reg = process_experiment(df_input)
    except Exception as e:
        st.error(f"Gagal menghitung: {e}")
        st.stop()

    with st.container(border=True):
        st.subheader("3. Preview Hasil")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("IC50", f"{reg.ic50:.2f} ppm")
        c2.metric("R-squared", f"{reg.r_squared:.4f}")
        c3.metric("Slope (a)", f"{reg.slope:.4f}")
        c4.metric("Kategori", classify_ic50(reg.ic50))

        st.markdown(f"**Persamaan regresi:** `{reg.equation}`")

        st.dataframe(
            df_proc[
                [
                    "konsentrasi",
                    "abs_mean",
                    "inhib_1",
                    "inhib_2",
                    "inhib_3",
                    "inhib_mean",
                    "inhib_sd",
                ]
            ].round(4),
            use_container_width=True,
            hide_index=True,
        )

        # Lazy import plotly biar cold start cepat
        import plotly.graph_objects as go
        import numpy as np

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=reg.x,
                y=reg.y,
                mode="markers",
                name="% inhibisi rata-rata",
                error_y=dict(
                    type="data",
                    array=df_proc.dropna(subset=["inhib_mean"])["inhib_sd"].values,
                ),
                marker=dict(size=10, color="#2E7D32"),
            )
        )
        if not pd.isna(reg.slope):
            xs = np.linspace(0, max(reg.x) * 1.1, 50)
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=reg.predict(xs),
                    mode="lines",
                    name=f"y = {reg.slope:.3f}x + {reg.intercept:.3f}",
                    line=dict(color="#1B5E20"),
                )
            )
            fig.add_hline(y=50, line_dash="dot", annotation_text="50%")
            fig.add_vline(
                x=reg.ic50,
                line_dash="dot",
                annotation_text=f"IC50={reg.ic50:.2f}",
            )
        fig.update_layout(
            xaxis_title="Konsentrasi (ppm)",
            yaxis_title="% Inhibisi",
            height=420,
            margin=dict(t=20, b=40, l=40, r=20),
            autosize=True,
        )
        st.plotly_chart(fig, use_container_width=True)

    # -------------------- Simpan --------------------
    st.divider()
    can_save = auth.require_auth("menyimpan data DPPH")
    if st.button(
        f"Simpan ke {storage.backend_name()}", type="primary", disabled=not can_save
    ):
        exp_id = (
            f"EXP_{tanggal.isoformat()}_{int(waktu_inkubasi)}min_"
            f"{datetime.now().strftime('%H%M%S')}"
        )

        rows = df_proc.copy()
        rows["experiment_id"] = exp_id
        rows["tanggal"] = tanggal.isoformat()
        rows["sampel"] = sampel
        rows["metode_ekstraksi"] = metode
        rows["waktu_inkubasi_menit"] = int(waktu_inkubasi)
        rows["ic50_ppm"] = reg.ic50
        rows["r_squared"] = reg.r_squared
        rows["persamaan_regresi"] = reg.equation
        rows["catatan"] = catatan
        rows["created_at"] = datetime.now().isoformat(timespec="seconds")

        try:
            storage.append_dpph(rows)
            clear_caches()
            st.success(f"Tersimpan. Experiment ID: `{exp_id}`")
            st.balloons()
            st.session_state["preview_done"] = False
        except Exception as e:
            st.error(f"Gagal menyimpan: {e}")
