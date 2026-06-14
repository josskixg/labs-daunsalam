"""
Auth sederhana berbasis passcode untuk gate write operations.

Konfigurasi (opsional) di .streamlit/secrets.toml:

    [auth]
    enabled = true
    passcode = "ganti-passcode-rahasia-lo"
    label    = "Peneliti"

Kalau [auth] tidak ada -> auth dimatikan (default), semua bisa input.
"""

from __future__ import annotations

import hmac
import streamlit as st


def is_enabled() -> bool:
    try:
        return bool(st.secrets.get("auth", {}).get("enabled", False))
    except Exception:
        return False


def _correct_passcode(entered: str) -> bool:
    try:
        expected = str(st.secrets.get("auth", {}).get("passcode", ""))
    except Exception:
        expected = ""
    if not expected:
        return False
    return hmac.compare_digest(entered.encode(), expected.encode())


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_ok"))


def login_widget(location: str = "sidebar") -> None:
    """Render kotak login. Auto skip kalau auth dimatikan / sudah login."""
    if not is_enabled():
        return
    if is_logged_in():
        return

    container = st.sidebar if location == "sidebar" else st
    container.markdown("### Login")
    container.caption("Masukkan passcode untuk mengaktifkan input data.")

    with container.form("auth_form", clear_on_submit=False):
        pc = st.text_input("Passcode", type="password", key="auth_pc")
        if st.form_submit_button("Masuk", type="primary", use_container_width=True):
            if _correct_passcode(pc):
                st.session_state["auth_ok"] = True
                st.session_state["auth_label"] = st.secrets.get("auth", {}).get(
                    "label", "Peneliti"
                )
                st.rerun()
            else:
                container.error("Passcode salah.")


def require_auth(action: str = "menyimpan data") -> bool:
    """
    Return True jika user diizinkan write. Kalau tidak, render warning.
    """
    if not is_enabled():
        return True
    if is_logged_in():
        return True
    st.warning(f"Login diperlukan untuk {action}. Buka sidebar dan masukkan passcode.")
    return False


def logout_widget() -> None:
    if not is_enabled() or not is_logged_in():
        return
    label = st.session_state.get("auth_label", "Peneliti")
    st.sidebar.success(f"Login sebagai: **{label}**")
    if st.sidebar.button("Logout", use_container_width=True):
        for k in ("auth_ok", "auth_label", "auth_pc"):
            st.session_state.pop(k, None)
        st.rerun()
