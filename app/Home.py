"""
Home — Platform Digital Evaluasi Antioksidan Daun Salam (UAE).
Tesis: Panji Setya Amitra (NIM 7789240009), UNTIRTA.
"""

import pandas as pd
import streamlit as st

from utils import storage, auth
from utils.cache import read_dpph
from utils.calculations import classify_ic50
from utils.ui import setup_page, page_header

setup_page("Antioksidan Daun Salam", icon="leaf")

# Auth widgets di sidebar (auto-skip kalau auth tidak diaktifkan)
auth.login_widget()
auth.logout_widget()

page_header(
    "Platform Digital Evaluasi Antioksidan Daun Salam",
    "Ekstraksi Berwawasan Lingkungan dengan Ultrasound-Assisted Extraction (UAE) "
    "dan Evaluasi Aktivitas Antioksidan Metode DPPH",
)

# -------------------- Backend status (compact) --------------------
backend = storage.backend_name()
_status_col, _toggle_col = st.columns([4, 1])
with _status_col:
    if backend == "Google Sheets":
        st.success(f"Backend: **{backend}** · terhubung")
    # Kalau CSV lokal: tidak tampilkan banner besar.
    # Status detail dipindah ke expander "Status Sistem" di bawah.
with _toggle_col:
    force_local = st.toggle(
        "Mode lokal",
        value=st.session_state.get("force_local", False),
        help="Paksa pakai CSV lokal walau secrets.toml sudah di-set.",
        label_visibility="collapsed" if backend == "Google Sheets" else "visible",
    )
    st.session_state["force_local"] = force_local

# -------------------- Ringkasan dashboard --------------------
st.subheader("Ringkasan Data DPPH")

with st.spinner("Memuat data..."):
    df = read_dpph()

if df.empty:
    st.warning(
        "Belum ada data tersimpan. Buka halaman **Input DPPH** "
        "untuk memasukkan percobaan pertama."
    )
else:
    df["ic50_ppm"] = pd.to_numeric(df["ic50_ppm"], errors="coerce")
    df["waktu_inkubasi_menit"] = pd.to_numeric(
        df["waktu_inkubasi_menit"], errors="coerce"
    )

    summary = (
        df.dropna(subset=["experiment_id"])
        .groupby("experiment_id", as_index=False)
        .agg(
            tanggal=("tanggal", "first"),
            sampel=("sampel", "first"),
            metode=("metode_ekstraksi", "first"),
            waktu_menit=("waktu_inkubasi_menit", "first"),
            ic50=("ic50_ppm", "first"),
            r2=("r_squared", "first"),
        )
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total percobaan", len(summary))
    c2.metric(
        "IC50 terbaik",
        f"{summary['ic50'].min():.2f} ppm" if not summary.empty else "-",
    )
    c3.metric(
        "IC50 rata-rata",
        f"{summary['ic50'].mean():.2f} ppm" if not summary.empty else "-",
    )
    if not summary.empty:
        best = summary.loc[summary["ic50"].idxmin()]
        c4.metric("Waktu inkubasi terbaik", f"{int(best['waktu_menit'])} menit")
        st.success(
            f"Percobaan terbaik: `{best['experiment_id']}` "
            f"(IC50 = {best['ic50']:.2f} ppm — {classify_ic50(best['ic50'])})"
        )

    st.dataframe(
        summary.sort_values("ic50").reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

# -------------------- Quick links --------------------
st.divider()
st.subheader("Mulai")
st.markdown(
    """
- **Input DPPH** — masukkan absorbansi pengujian baru
- **Visualisasi DPPH** — kurva regresi & perbandingan waktu inkubasi
- **Riwayat Data** — kelola (edit/hapus) data tersimpan
- **Input UAE** *(placeholder)* — parameter ekstraksi
- **Input TPC** *(placeholder)* — total fenolik
    """
)

# -------------------- Tentang Penelitian --------------------
with st.expander("Tentang penelitian", expanded=False):
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #F1F8E9 0%, #E8F5E9 100%);
            border-left: 4px solid #2E7D32;
            border-radius: 8px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        ">
        <div style="font-size: 0.78rem; font-weight: 600; color: #2E7D32;
                    letter-spacing: 0.08em; text-transform: uppercase;
                    margin-bottom: 0.4rem;">Judul Tesis</div>
        <div style="font-size: 1.05rem; color: #1B5E20; font-weight: 500;
                    line-height: 1.55;">
            Ekstraksi Berwawasan Lingkungan Daun Salam dengan Metode
            Ultrasound Assisted Extraction (UAE) dan Evaluasi Potensi
            Antioksidan dalam Platform Digital
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.markdown(
            """
            **Peneliti**
            Panji Setya Amitra
            NIM 7789240009

            **Program Studi**
            Magister Studi Lingkungan
            Pascasarjana UNTIRTA
            """
        )
    with info_col2:
        st.markdown(
            """
            **Pembimbing 1**
            Prof. Dr. Alimuddin, S.T., M.M., M.T.

            **Pembimbing 2**
            Prof. Dr.-Ing. Anton Irawan, M.T.
            """
        )

    st.divider()

    st.markdown(
        """
        **Tentang platform ini**

        Platform ini merupakan *deliverable* digital tesis untuk mengelola
        siklus riset uji antioksidan secara terintegrasi:

        - **DPPH** — input data, perhitungan IC50 otomatis, visualisasi
        - **UAE** — pencatatan parameter ekstraksi (placeholder)
        - **TPC** — pengukuran total fenolik (placeholder)
        - **ANOVA + Tukey HSD** — uji beda nyata antar grup
        - **Export PDF** — laporan siap untuk lampiran tesis
        """
    )

# -------------------- Status sistem (kecil, di bawah) --------------------
with st.expander("Status sistem", expanded=False):
    st.caption(f"**Backend penyimpanan**: {backend}")
    if backend == "CSV Lokal":
        st.caption(
            "Mode CSV lokal aktif. Data disimpan ke `app/data/*.csv`. "
            "Untuk multi-device & persistensi, konfigurasikan Google Sheets "
            "via `app/.streamlit/secrets.toml`."
        )
    else:
        st.caption("Terhubung ke Google Sheets. Data sinkron multi-device.")
