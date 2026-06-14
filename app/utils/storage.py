"""
Storage facade — auto-pilih Google Sheets atau CSV lokal.

Cara kerja:
  - Kalau secrets.toml [connections.gsheets] ada -> pakai Google Sheets
  - Kalau belum -> jatuh ke CSV lokal di app/data/
  - User bisa paksa lokal lewat env var atau session_state['force_local'] = True
"""

from __future__ import annotations

from datetime import datetime
import os
import streamlit as st
import pandas as pd

from .sheets import DPPH_COLUMNS, UAE_COLUMNS, TPC_COLUMNS


def _gsheets_available() -> bool:
    """Cek tanpa raise — apakah secrets [connections.gsheets] terdefinisi?"""
    if st.session_state.get("force_local") or os.environ.get("FORCE_LOCAL_STORE"):
        return False
    try:
        return "gsheets" in st.secrets.get("connections", {})
    except Exception:
        return False


def backend_name() -> str:
    return "Google Sheets" if _gsheets_available() else "CSV Lokal"


# ----------- DPPH -----------
def read_dpph() -> pd.DataFrame:
    if _gsheets_available():
        from . import sheets

        return sheets.read_dpph()
    from . import local_store

    df = local_store.read_worksheet("DPPH")
    if df.empty:
        return pd.DataFrame(columns=DPPH_COLUMNS)
    for c in DPPH_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[DPPH_COLUMNS]


def append_dpph(rows: pd.DataFrame) -> None:
    if "created_at" not in rows.columns or rows["created_at"].isna().all():
        rows["created_at"] = datetime.now().isoformat(timespec="seconds")
    if _gsheets_available():
        from . import sheets

        sheets.append_dpph_experiment(rows)
    else:
        from . import local_store

        local_store.append_rows("DPPH", rows, DPPH_COLUMNS)


def overwrite_dpph(df: pd.DataFrame) -> None:
    if _gsheets_available():
        from . import sheets

        sheets.write_worksheet("DPPH", df)
    else:
        from . import local_store

        local_store.write_worksheet("DPPH", df)


def delete_dpph_experiment(experiment_id: str) -> int:
    df = read_dpph()
    before = len(df)
    df = df[df["experiment_id"] != experiment_id]
    overwrite_dpph(df)
    return before - len(df)


# ----------- UAE / TPC (placeholder) -----------
def read_uae() -> pd.DataFrame:
    return _generic_read("UAE", UAE_COLUMNS)


def append_uae(rows: pd.DataFrame) -> None:
    _generic_append("UAE", rows, UAE_COLUMNS)


def read_tpc() -> pd.DataFrame:
    return _generic_read("TPC", TPC_COLUMNS)


def append_tpc(rows: pd.DataFrame) -> None:
    _generic_append("TPC", rows, TPC_COLUMNS)


def _generic_read(ws: str, cols: list[str]) -> pd.DataFrame:
    if _gsheets_available():
        from . import sheets

        df = sheets.read_worksheet(ws)
    else:
        from . import local_store

        df = local_store.read_worksheet(ws)
    if df.empty:
        return pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


def _generic_append(ws: str, rows: pd.DataFrame, cols: list[str]) -> None:
    if "created_at" not in rows.columns or rows["created_at"].isna().all():
        rows["created_at"] = datetime.now().isoformat(timespec="seconds")
    if _gsheets_available():
        from . import sheets

        sheets.append_rows(ws, rows, cols)
    else:
        from . import local_store

        local_store.append_rows(ws, rows, cols)
