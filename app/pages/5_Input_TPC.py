"""Placeholder: Total Phenolic Content (Folin-Ciocalteu)."""

from datetime import date

import pandas as pd
import streamlit as st

from utils import storage, auth
from utils.cache import read_tpc, clear_caches
from utils.ui import setup_page, page_header

setup_page("Input TPC", icon="test_tube")
page_header(
    "Input Total Fenolik (TPC)",
    "Modul placeholder. Pengukuran Folin-Ciocalteu, hasil dalam mg GAE / g ekstrak.",
)
auth.login_widget()
auth.logout_widget()

with st.form("tpc"):
    c1, c2, c3 = st.columns(3)
    tanggal = c1.date_input("Tanggal", date.today())
    kode = c2.text_input("Kode sampel", "TPC-001")
    konsentrasi = c3.number_input("Konsentrasi sampel (ppm)", value=100.0)

    a1, a2, a3 = st.columns(3)
    abs1 = a1.number_input("Abs 1", value=0.0, step=0.001, format="%.4f")
    abs2 = a2.number_input("Abs 2", value=0.0, step=0.001, format="%.4f")
    abs3 = a3.number_input("Abs 3", value=0.0, step=0.001, format="%.4f")

    tpc = st.number_input(
        "TPC (mg GAE/g)", value=0.0, step=0.01, help="Hasil dari kurva standar GAE"
    )
    catatan = st.text_input("Catatan", "")

    can_save = auth.require_auth("menyimpan data TPC")
    if (
        st.form_submit_button(
            "Simpan",
            type="primary",
            use_container_width=True,
            disabled=not can_save,
        )
        and can_save
    ):
        row = pd.DataFrame(
            [
                {
                    "tanggal": tanggal.isoformat(),
                    "kode_sampel": kode,
                    "konsentrasi_ppm": konsentrasi,
                    "abs_1": abs1,
                    "abs_2": abs2,
                    "abs_3": abs3,
                    "abs_mean": (abs1 + abs2 + abs3) / 3,
                    "tpc_mg_gae_per_g": tpc,
                    "catatan": catatan,
                }
            ]
        )
        try:
            storage.append_tpc(row)
            clear_caches()
            st.success("Tersimpan.")
        except Exception as e:
            st.error(f"Gagal: {e}")

st.divider()
df = read_tpc()
if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
