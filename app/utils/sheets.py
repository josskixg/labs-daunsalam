"""
Wrapper Google Sheets pakai streamlit-gsheets-connection.

Konvensi worksheet:
    DPPH : data uji DPPH (long format, 1 row = 1 konsentrasi per percobaan)
    UAE  : parameter ekstraksi UAE (placeholder)
    TPC  : total fenolik (placeholder)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st


# Kolom kanonik tabel DPPH (long format)
DPPH_COLUMNS = [
    "experiment_id",  # ID percobaan, mis. "EXP_2026-01-15_5min_001"
    "tanggal",  # YYYY-MM-DD
    "sampel",  # mis. "Daun Salam Ekstrak Etanol"
    "metode_ekstraksi",  # UAE / Maserasi / dll
    "waktu_inkubasi_menit",  # 5, 6, 7, 8, 9
    "konsentrasi",  # ppm
    "abs_1",
    "abs_2",
    "abs_3",
    "abs_mean",
    "inhib_1",
    "inhib_2",
    "inhib_3",
    "inhib_mean",
    "inhib_sd",
    "ic50_ppm",  # diisi sama untuk semua row dalam 1 percobaan
    "r_squared",
    "persamaan_regresi",
    "catatan",
    "created_at",
]

UAE_COLUMNS = [
    "tanggal",
    "kode_sampel",
    "massa_simplisia_g",
    "volume_pelarut_ml",
    "jenis_pelarut",
    "rasio_pelarut",
    "amplitudo_persen",
    "frekuensi_khz",
    "suhu_c",
    "waktu_sonikasi_menit",
    "siklus_on_off",
    "massa_ekstrak_g",
    "rendemen_persen",
    "catatan",
    "created_at",
]

TPC_COLUMNS = [
    "tanggal",
    "kode_sampel",
    "konsentrasi_ppm",
    "abs_1",
    "abs_2",
    "abs_3",
    "abs_mean",
    "tpc_mg_gae_per_g",
    "catatan",
    "created_at",
]


def _connect():
    """Lazy import biar app gak crash kalau lib belum terpasang."""
    from streamlit_gsheets import GSheetsConnection

    return st.connection("gsheets", type=GSheetsConnection)


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Pastikan df punya semua kolom & urutannya kanonik."""
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]


# -----------------------------------------------------------------
# READ
# -----------------------------------------------------------------
def read_worksheet(worksheet: str, ttl: int = 5) -> pd.DataFrame:
    """Baca worksheet ke DataFrame. ttl detik untuk cache."""
    conn = _connect()
    df = conn.read(worksheet=worksheet, ttl=ttl)
    if df is None:
        return pd.DataFrame()
    # Drop baris kosong total
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def read_dpph() -> pd.DataFrame:
    df = read_worksheet("DPPH")
    if df.empty:
        return pd.DataFrame(columns=DPPH_COLUMNS)
    return _ensure_columns(df, DPPH_COLUMNS)


# -----------------------------------------------------------------
# WRITE / APPEND / UPDATE
# -----------------------------------------------------------------
def write_worksheet(worksheet: str, df: pd.DataFrame) -> None:
    """OVERWRITE seluruh isi worksheet — pakai untuk update/delete."""
    conn = _connect()
    conn.update(worksheet=worksheet, data=df)


def append_rows(worksheet: str, new_rows: pd.DataFrame, columns: list[str]) -> None:
    """Append rows ke worksheet (baca dulu, concat, lalu overwrite)."""
    existing = read_worksheet(worksheet, ttl=0)
    new_rows = _ensure_columns(new_rows.copy(), columns)
    if existing.empty:
        combined = new_rows
    else:
        existing = _ensure_columns(existing, columns)
        combined = pd.concat([existing, new_rows], ignore_index=True)
    write_worksheet(worksheet, combined)


def append_dpph_experiment(rows_long: pd.DataFrame) -> None:
    """Append seluruh row 1 percobaan DPPH (sudah long format)."""
    if "created_at" not in rows_long or rows_long["created_at"].isna().all():
        rows_long["created_at"] = datetime.now().isoformat(timespec="seconds")
    append_rows("DPPH", rows_long, DPPH_COLUMNS)


def delete_experiment(experiment_id: str) -> int:
    """Hapus semua row dengan experiment_id tertentu. Return jumlah row dihapus."""
    df = read_dpph()
    before = len(df)
    df = df[df["experiment_id"] != experiment_id]
    write_worksheet("DPPH", df)
    return before - len(df)


# -----------------------------------------------------------------
# Util: cek koneksi
# -----------------------------------------------------------------
def health_check() -> tuple[bool, str]:
    """Return (ok, message). Aman dipanggil di Home page."""
    try:
        _ = read_worksheet("DPPH", ttl=0)
        return True, "Terhubung ke Google Sheets ✔"
    except Exception as e:
        return False, f"Gagal koneksi: {e}"
