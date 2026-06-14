"""
Fallback CSV lokal — dipakai otomatis kalau secrets.toml belum di-setup.
Biar lo bisa coba app dulu tanpa Google Sheets.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)


def _path(worksheet: str) -> Path:
    return DATA_DIR / f"{worksheet}.csv"


def read_worksheet(worksheet: str) -> pd.DataFrame:
    p = _path(worksheet)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def write_worksheet(worksheet: str, df: pd.DataFrame) -> None:
    df.to_csv(_path(worksheet), index=False)


def append_rows(worksheet: str, new_rows: pd.DataFrame, columns: list[str]) -> None:
    existing = read_worksheet(worksheet)
    for c in columns:
        if c not in new_rows.columns:
            new_rows[c] = None
    new_rows = new_rows[columns]
    if existing.empty:
        combined = new_rows
    else:
        for c in columns:
            if c not in existing.columns:
                existing[c] = None
        existing = existing[columns]
        combined = pd.concat([existing, new_rows], ignore_index=True)
    write_worksheet(worksheet, combined)
