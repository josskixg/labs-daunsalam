"""
Cache layer untuk read operations.

Strategi:
- Read DPPH/UAE/TPC di-cache 60 detik via st.cache_data
- Setiap kali append/overwrite, panggil clear_caches() biar UI fresh
- Biar tidak race-condition: cache key include 'force_local' state
"""

from __future__ import annotations
import streamlit as st
import pandas as pd

from . import storage as _storage


@st.cache_data(ttl=60, show_spinner=False)
def cached_read_dpph(_backend: str) -> pd.DataFrame:
    """`_backend` ikut jadi cache key biar pindah backend nge-bust cache."""
    return _storage.read_dpph()


@st.cache_data(ttl=60, show_spinner=False)
def cached_read_uae(_backend: str) -> pd.DataFrame:
    return _storage.read_uae()


@st.cache_data(ttl=60, show_spinner=False)
def cached_read_tpc(_backend: str) -> pd.DataFrame:
    return _storage.read_tpc()


def read_dpph() -> pd.DataFrame:
    return cached_read_dpph(_storage.backend_name())


def read_uae() -> pd.DataFrame:
    return cached_read_uae(_storage.backend_name())


def read_tpc() -> pd.DataFrame:
    return cached_read_tpc(_storage.backend_name())


def clear_caches() -> None:
    """Hapus semua cache read setelah write/delete."""
    cached_read_dpph.clear()
    cached_read_uae.clear()
    cached_read_tpc.clear()
