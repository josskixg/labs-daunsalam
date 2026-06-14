"""
Helper UI: responsive layout, page setup standar, CSS injection.

Strategi mobile (<= 768px):
- Sidebar: biarkan Streamlit native handle (auto-collapsed di mobile)
- TIDAK override width/min-width sidebar (kalau di-override jadi nutupin konten)
- Konten utama: padding lebih ringkas, kolom auto-stack
- Heading lebih kecil, button full-width
- Plotly chart bisa scroll horizontal
"""

from __future__ import annotations
import streamlit as st


_RESPONSIVE_CSS = """
<style>
/* ============================================================
   GLOBAL TWEAKS (semua viewport)
   ============================================================ */
div[data-testid="stPlotlyChart"] {
  overflow-x: auto;
}

div[data-testid="stContainer"] > div:has(> [data-testid="stContainerBorder"]) {
  border-radius: 12px;
}

/* ============================================================
   MOBILE BREAKPOINT (<= 768px)
   PENTING: tidak override width/min-width sidebar.
   Streamlit native sudah handle (sidebar default collapsed di mobile).
   ============================================================ */
@media (max-width: 768px) {

  /* Block container: padding-top SANGAT besar supaya heading tidak
     ketutupan header bar (height ~60px).
     Pakai specificity TINGGI: body + multiple attribute selectors
     untuk menang dari Emotion CSS Streamlit (.st-emotion-cache-xxx) */
  body section[data-testid="stMain"] div[data-testid="stMainBlockContainer"],
  body section[data-testid="stMain"] div.block-container,
  body div[data-testid="stMainBlockContainer"].block-container {
    padding-top: 5.5rem !important;
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
  }

  /* Heading utama: gap dari padding-top */
  body h1:first-of-type {
    margin-top: 0.5rem !important;
    padding-top: 0 !important;
  }

  /* Header bar Streamlit: solid background + border supaya jelas batasnya */
  body header[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.98) !important;
    border-bottom: 1px solid #E0E0E0 !important;
  }

  /* Kolom auto-stack vertikal */
  div[data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
    gap: 0.5rem !important;
  }
  div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    width: 100% !important;
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }

  /* Metric compact */
  div[data-testid="stMetric"] {
    padding: 0.4rem 0.6rem !important;
  }
  div[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    line-height: 1.2 !important;
  }
  div[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
  }

  /* Headings lebih ringkas */
  h1 { font-size: 1.5rem !important; line-height: 1.25 !important; }
  h2 { font-size: 1.25rem !important; }
  h3 { font-size: 1.1rem !important; }

  /* Button full-width */
  .stButton > button,
  .stDownloadButton > button,
  .stFormSubmitButton > button {
    width: 100% !important;
  }

  /* Tombol hamburger sidebar lebih besar (tap-friendly) */
  button[data-testid="stSidebarCollapseButton"],
  button[data-testid="collapsedControl"] {
    width: 44px !important;
    height: 44px !important;
  }

  /* Header (toolbar) tetap di atas sidebar saat sidebar terbuka */
  header[data-testid="stHeader"] {
    z-index: 1000 !important;
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(8px);
  }

  /* Tabel data-editor & dataframe scroll horizontal kalau lebar */
  div[data-testid="stDataFrame"],
  div[data-testid="stDataEditor"] {
    overflow-x: auto;
  }

  /* Sidebar shadow lebih jelas saat terbuka di mobile (visual cue) */
  section[data-testid="stSidebar"][aria-expanded="true"] {
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.18) !important;
  }
}


/* ============================================================
   TABLET (769px - 1024px)
   ============================================================ */
@media (min-width: 769px) and (max-width: 1024px) {
  .block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
  }
}
</style>
"""


def setup_page(title: str, icon: str = "leaf", layout: str = "wide") -> None:
    """
    Standar page config + responsive CSS.

    initial_sidebar_state='auto' artinya:
    - Desktop (>= 768px): sidebar EXPANDED otomatis
    - Mobile (< 768px): sidebar COLLAPSED otomatis

    Streamlit menentukan ini via media query saat first load.
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon if icon else None,
        layout=layout,
        initial_sidebar_state="auto",
        menu_items={
            "Get Help": None,
            "Report a bug": None,
            "About": (
                "Platform Digital Evaluasi Antioksidan Daun Salam — "
                "Tesis Panji Setya Amitra (UNTIRTA)."
            ),
        },
    )
    st.markdown(_RESPONSIVE_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str | None = None) -> None:
    """Header konsisten antar page."""
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def metric_grid(items: list[tuple[str, str]], cols_desktop: int = 4) -> None:
    """
    Render baris metric yang otomatis stack di mobile via CSS.
    items = [(label, value), ...]
    """
    cols = st.columns(min(cols_desktop, len(items)))
    for i, (label, value) in enumerate(items):
        with cols[i % len(cols)]:
            st.metric(label, value)
