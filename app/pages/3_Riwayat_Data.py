"""
Lihat / hapus / edit massal data DPPH.
"""

import streamlit as st

from utils import storage, auth
from utils.cache import read_dpph, clear_caches
from utils.ui import setup_page, page_header

setup_page("Riwayat Data", icon="card_index_dividers")
page_header("Riwayat & Manajemen Data", f"Backend: {storage.backend_name()}")

auth.login_widget()
auth.logout_widget()

df = read_dpph()
if df.empty:
    st.info("Belum ada data.")
    st.stop()

st.subheader("Daftar percobaan")
exp_ids = sorted(df["experiment_id"].dropna().unique().tolist(), reverse=True)
st.write(f"Total percobaan: **{len(exp_ids)}** | Total baris: **{len(df)}**")

# -------------------- Edit massal --------------------
st.markdown("### Edit massal (langsung overwrite worksheet)")
st.caption("Klik sel untuk edit. Tambah/hapus baris dari ikon di kanan atas tabel.")
edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="bulk_editor",
)

can_write = auth.require_auth("mengubah/hapus data")

cc1, cc2 = st.columns([1, 5])
with cc1:
    if st.button(
        "Simpan perubahan",
        type="primary",
        use_container_width=True,
        disabled=not can_write,
    ):
        try:
            storage.overwrite_dpph(edited)
            clear_caches()
            st.success("Tersimpan.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal: {e}")

# -------------------- Hapus per experiment --------------------
st.divider()
st.markdown("### Hapus 1 percobaan")
st.caption("Akan menghapus semua baris dengan experiment_id yang sama.")
target = st.selectbox("Pilih experiment_id", options=exp_ids)
if st.button("Hapus", type="secondary", disabled=not can_write):
    n = storage.delete_dpph_experiment(target)
    clear_caches()
    st.success(f"Terhapus {n} baris untuk `{target}`")
    st.rerun()
