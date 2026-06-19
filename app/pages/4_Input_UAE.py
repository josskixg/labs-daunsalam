"""
Placeholder: input parameter ekstraksi UAE (Ultrasound-Assisted Extraction).
Skema kolom sudah disiapkan di utils/sheets.py UAE_COLUMNS.
"""

from datetime import date

import pandas as pd
import streamlit as st

from utils import storage, auth
from utils.cache import read_uae, clear_caches
from utils.ui import setup_page, page_header

setup_page("Input UAE", icon="microscope")
page_header(
    "Input Parameter Ekstraksi (UAE)",
    "Modul placeholder. Siap dipakai untuk mencatat parameter ekstraksi UAE.",
)
auth.login_widget()
auth.logout_widget()

with st.form("uae"):
    c1, c2, c3 = st.columns(3)
    tanggal = c1.date_input("Tanggal", date.today())
    kode = c2.text_input("Kode sampel", "UAE-001")
    pelarut = c3.selectbox(
        "Jenis pelarut",
        ["Metanol", "Etanol 70%", "Etanol 96%", "Air"],
    )

    c4, c5, c6 = st.columns(3)
    massa = c4.number_input("Massa simplisia (g)", value=10.0, min_value=0.0, step=0.1)
    volume = c5.number_input(
        "Volume pelarut (mL)", value=100.0, min_value=0.0, step=1.0
    )
    rasio = c6.text_input("Rasio simplisia:pelarut", value="1:10")

    c7, c8, c9 = st.columns(3)
    amplitudo = c7.slider("Amplitudo (%)", 0, 100, 60)
    frekuensi = c8.number_input("Frekuensi (kHz)", value=20.0, step=1.0)
    suhu = c9.number_input("Suhu (C)", value=40.0, step=1.0)

    c10, c11 = st.columns(2)
    waktu = c10.number_input("Waktu sonikasi (menit)", value=30, min_value=1)
    siklus = c11.text_input("Siklus on/off (detik)", value="5/3")

    massa_eks = st.number_input("Massa ekstrak hasil (g)", value=0.0, step=0.01)
    catatan = st.text_input("Catatan", "")

    can_save = auth.require_auth("menyimpan data UAE")
    submitted = st.form_submit_button(
        "Simpan",
        type="primary",
        use_container_width=True,
        disabled=not can_save,
    )
    if submitted and can_save:
        rendemen = (massa_eks / massa * 100) if massa > 0 else 0.0
        row = pd.DataFrame(
            [
                {
                    "tanggal": tanggal.isoformat(),
                    "kode_sampel": kode,
                    "massa_simplisia_g": massa,
                    "volume_pelarut_ml": volume,
                    "jenis_pelarut": pelarut,
                    "rasio_pelarut": rasio,
                    "amplitudo_persen": amplitudo,
                    "frekuensi_khz": frekuensi,
                    "suhu_c": suhu,
                    "waktu_sonikasi_menit": waktu,
                    "siklus_on_off": siklus,
                    "massa_ekstrak_g": massa_eks,
                    "rendemen_persen": rendemen,
                    "catatan": catatan,
                }
            ]
        )
        try:
            storage.append_uae(row)
            clear_caches()
            st.success(f"Tersimpan. Rendemen: {rendemen:.2f}%")
        except Exception as e:
            st.error(f"Gagal: {e}")

st.divider()
st.subheader("Data UAE tersimpan")
df = read_uae()
if df.empty:
    st.caption("Belum ada data.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)
