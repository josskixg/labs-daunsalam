# Diagram & Visual Reference

Kumpulan diagram Mermaid untuk dokumentasi platform.
GitHub & VS Code dapat me-render Mermaid secara native; tidak perlu tooling tambahan.

## Daftar Diagram

1. [Alur Kerja Riset (User Journey)](#1-alur-kerja-riset-user-journey)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Decision Tree Backend](#3-decision-tree-backend-storage)
4. [Sequence: Input Data DPPH](#4-sequence-input-data-dpph)
5. [Sequence: Setup Google Sheets](#5-sequence-setup-google-sheets)
6. [Flow Auth Login](#6-flow-auth-login)
7. [Pipeline Perhitungan DPPH](#7-pipeline-perhitungan-dpph)
8. [Anti Cold-Start Mechanism](#8-anti-cold-start-mechanism)
9. [Struktur Folder](#9-struktur-folder)
10. [Roadmap Modul](#10-roadmap-modul)

---

## 1. Alur Kerja Riset (User Journey)

```mermaid
flowchart LR
    A[Lab: Pengukuran<br/>Absorbansi DPPH<br/>via Spektrofotometer] --> B[Buka Aplikasi<br/>Streamlit]
    B --> C{Login?}
    C -->|Auth aktif| D[Masukkan Passcode]
    C -->|Auth nonaktif| E
    D --> E[Halaman<br/>Input DPPH]
    E --> F[Isi metadata:<br/>tanggal, sampel,<br/>waktu inkubasi]
    F --> G[Input absorbansi<br/>3 replikasi x<br/>6 konsentrasi]
    G --> H[Klik Hitung<br/>Preview]
    H --> I[Aplikasi hitung<br/>otomatis: %inhibisi,<br/>SD, regresi, IC50]
    I --> J[Klik Simpan]
    J --> K[(Google Sheets<br/>worksheet DPPH)]
    K --> L[Visualisasi]
    K --> M[Analisis ANOVA]
    K --> N[Export PDF]
    L --> O[Insight tesis]
    M --> O
    N --> P[Lampiran<br/>tesis]

    style K fill:#34A853,stroke:#1B5E20,color:#fff
    style A fill:#F1F8E9,stroke:#2E7D32
    style O fill:#FFF59D,stroke:#F57F17
    style P fill:#FFF59D,stroke:#F57F17
```

---

## 2. Arsitektur Sistem

```mermaid
flowchart TB
    subgraph Browser["Browser / Mobile"]
        UI[Streamlit UI]
    end

    subgraph App["Streamlit App (Python)"]
        H[Home.py]
        P1[Input DPPH]
        P2[Visualisasi]
        P3[Riwayat]
        P4[Input UAE]
        P5[Input TPC]
        P6[ANOVA]

        subgraph Utils["utils/"]
            CALC[calculations.py<br/>%inhibisi, IC50,<br/>ANOVA, Tukey]
            STO[storage.py<br/>facade]
            SHE[sheets.py<br/>gsheets wrapper]
            LOC[local_store.py<br/>CSV fallback]
            CACHE[cache.py<br/>@st.cache_data]
            UI_H[ui.py<br/>responsive CSS]
            AUTH[auth.py<br/>passcode gate]
            PDF[pdf_report.py<br/>reportlab]
        end
    end

    subgraph Backend["Backend (auto-pilih)"]
        GS[(Google Sheets<br/>via service account)]
        FS[(CSV lokal<br/>app/data/)]
    end

    UI <-->|HTTP| H
    H --> P1 & P2 & P3 & P4 & P5 & P6
    P1 & P3 & P4 & P5 --> AUTH
    P1 & P2 & P3 & P4 & P5 & P6 --> CACHE
    CACHE --> STO
    STO -->|secrets ada| SHE
    STO -->|fallback| LOC
    SHE --> GS
    LOC --> FS
    P1 & P2 --> CALC
    P6 --> CALC
    P2 --> PDF
    H & P1 & P2 & P3 & P4 & P5 & P6 --> UI_H

    style GS fill:#34A853,stroke:#1B5E20,color:#fff
    style FS fill:#FFB300,stroke:#E65100,color:#fff
    style AUTH fill:#FF7043,stroke:#BF360C,color:#fff
```

---

## 3. Decision Tree Backend Storage

```mermaid
flowchart TD
    Start([App startup]) --> Q1{secrets.toml<br/>punya<br/>connections.gsheets?}
    Q1 -->|Tidak| LOCAL[Pakai CSV Lokal<br/>app/data/*.csv]
    Q1 -->|Ya| Q2{User toggle<br/>'Mode lokal'?}
    Q2 -->|Ya| LOCAL
    Q2 -->|Tidak| GS[Pakai Google Sheets]
    GS --> ST{Connection OK?}
    ST -->|Ya| OK([Backend: Google Sheets])
    ST -->|Tidak| ERR[Show error,<br/>fallback ke CSV]
    LOCAL --> OKL([Backend: CSV Lokal])
    ERR --> OKL

    style GS fill:#34A853,stroke:#1B5E20,color:#fff
    style LOCAL fill:#FFB300,stroke:#E65100,color:#fff
    style OK fill:#C8E6C9,stroke:#1B5E20
    style OKL fill:#FFE0B2,stroke:#E65100
```

---

## 4. Sequence: Input Data DPPH

```mermaid
sequenceDiagram
    autonumber
    actor User as Peneliti
    participant UI as Streamlit UI<br/>(Input DPPH)
    participant Auth as utils/auth.py
    participant Calc as utils/calculations.py
    participant Cache as utils/cache.py
    participant Storage as utils/storage.py
    participant GS as Google Sheets

    User->>UI: Buka halaman Input DPPH
    UI->>Auth: require_auth()
    alt Auth aktif & belum login
        Auth-->>UI: Disable tombol Simpan
        User->>UI: Masukkan passcode
        UI->>Auth: verify (hmac.compare_digest)
        Auth-->>UI: session_state.auth_ok = True
    end
    User->>UI: Isi metadata + absorbansi
    User->>UI: Klik "Hitung Preview"
    UI->>Calc: process_experiment(df, "pairwise")
    Calc-->>UI: df_proc + RegressionResult
    UI->>UI: Render tabel + chart Plotly
    User->>UI: Klik "Simpan"
    UI->>Storage: append_dpph(rows)
    Storage->>GS: conn.update(worksheet="DPPH", data)
    GS-->>Storage: 200 OK
    Storage->>Cache: clear_caches()
    Storage-->>UI: success
    UI-->>User: "Tersimpan, EXP_ID = ..."
```

---

## 5. Sequence: Setup Google Sheets

```mermaid
sequenceDiagram
    actor User
    participant Sheets as Google Sheets
    participant GCP as Google Cloud Console
    participant SA as Service Account
    participant App as Streamlit App

    User->>Sheets: Buat spreadsheet baru
    User->>Sheets: Import template_gsheet.xlsx<br/>(File > Import > Replace)
    Note over Sheets: 4 tab: PETUNJUK,<br/>DPPH, UAE, TPC

    User->>GCP: Buat project baru
    User->>GCP: Enable Google Sheets API<br/>+ Google Drive API
    User->>GCP: Create Service Account
    GCP->>SA: streamlit-bot@project.iam...
    User->>GCP: Download JSON key
    GCP-->>User: credentials.json

    User->>Sheets: Share sheet ke<br/>SA email (Editor)

    User->>App: Edit secrets.toml<br/>(paste isi JSON ke<br/>[connections.gsheets])
    User->>App: streamlit run Home.py
    App->>Sheets: read via service account
    Sheets-->>App: data
    App-->>User: "Backend: Google Sheets ✓"
```

---

## 6. Flow Auth Login

```mermaid
flowchart TD
    Start([User akses page]) --> A{[auth] section di<br/>secrets.toml &<br/>enabled=true?}
    A -->|Tidak| FREE[Auth dimatikan,<br/>semua bisa input]
    A -->|Ya| B{session_state<br/>auth_ok = True?}
    B -->|Ya| LOGGED[User sudah login,<br/>tampilkan Logout button]
    B -->|Tidak| LOGIN[Tampilkan form login<br/>di sidebar]
    LOGIN --> INP[User isi passcode]
    INP --> CHK{hmac.compare_digest<br/>cocok?}
    CHK -->|Ya| SET[set session_state<br/>auth_ok = True]
    CHK -->|Tidak| ERR[Tampilkan<br/>'Passcode salah']
    ERR --> LOGIN
    SET --> LOGGED
    FREE --> RENDER([Render page +<br/>tombol Simpan aktif])
    LOGGED --> RENDER
    LOGIN --> RENDERD([Render page +<br/>tombol Simpan DISABLED])

    style FREE fill:#FFE0B2,stroke:#E65100
    style LOGGED fill:#C8E6C9,stroke:#1B5E20
    style RENDERD fill:#FFCDD2,stroke:#B71C1C
```

---

## 7. Pipeline Perhitungan DPPH

```mermaid
flowchart LR
    Input[df_raw:<br/>konsentrasi,<br/>abs_1, abs_2, abs_3] --> A[Sort by konsentrasi]
    A --> B[Hitung abs_mean<br/>per row]
    B --> C{Konsentrasi == 0<br/>blanko?}
    C -->|Ya| D[inhib_* = NaN]
    C -->|Tidak| E[Pairwise inhibisi:<br/>inhib_i = abs_b_i - abs_s_i / abs_b_i x 100]
    E --> F[Hitung inhib_mean<br/>+ inhib_sd ddof=1]
    D --> G[Concat ke df_proc]
    F --> G
    G --> H[Linear regression<br/>scipy.stats.linregress]
    H --> I[a = slope<br/>b = intercept<br/>R² = rvalue²]
    I --> J[IC50 = 50 - b / a]
    J --> K[classify_ic50<br/>Molyneux 2004]
    K --> Output[df_proc + RegressionResult<br/>+ IC50 + kategori]

    style Input fill:#E3F2FD,stroke:#0D47A1
    style Output fill:#C8E6C9,stroke:#1B5E20
    style E fill:#FFF59D,stroke:#F57F17
    style J fill:#FFF59D,stroke:#F57F17
```

---

## 8. Anti Cold-Start Mechanism

```mermaid
flowchart TB
    subgraph Layer1["Layer 1: Caching"]
        A1[Read DPPH/UAE/TPC] --> A2[@st.cache_data<br/>ttl=60s]
        A2 --> A3[Cache hit:<br/>< 50ms]
        A2 --> A4[Cache miss:<br/>baca gsheets]
    end

    subgraph Layer2["Layer 2: Config"]
        B1[runOnSave=false]
        B2[fileWatcherType=none]
        B3[fastReruns=true]
        B4[Lazy import Plotly]
    end

    subgraph Layer3["Layer 3: Keep-Alive"]
        C1[GitHub Actions cron] -->|tiap 6 jam| C2[ping /_stcore/health]
        C2 --> C3{Status 200?}
        C3 -->|Ya| C4[App tetap warm]
        C3 -->|Tidak| C5[Wake up app]
    end

    Cold[Cold start: 30-60s] --> Warm
    Warm[App warm < 1s] --> User([User akses cepat])

    Layer1 -.-> Warm
    Layer2 -.-> Warm
    Layer3 -.-> Warm

    style Cold fill:#FFCDD2,stroke:#B71C1C
    style Warm fill:#C8E6C9,stroke:#1B5E20
```

---

## 9. Struktur Folder

```mermaid
flowchart LR
    Root[Repo Root] --> App[app/]
    Root --> GH[.github/workflows/]
    Root --> Docs[docs/]
    Root --> Tpl[template_gsheet.xlsx]
    Root --> Rd[README.md]
    Root --> Pd[PANDUAN.md]

    App --> Home[Home.py]
    App --> Pages[pages/]
    App --> Util[utils/]
    App --> Tests[tests/]
    App --> Conf[.streamlit/]
    App --> Req[requirements.txt]
    App --> KA[keep_alive.py]

    Pages --> P1[1_Input_DPPH.py]
    Pages --> P2[2_Visualisasi_DPPH.py]
    Pages --> P3[3_Riwayat_Data.py]
    Pages --> P4[4_Input_UAE.py]
    Pages --> P5[5_Input_TPC.py]
    Pages --> P6[6_Analisis_ANOVA.py]

    Util --> U1[calculations.py]
    Util --> U2[sheets.py]
    Util --> U3[local_store.py]
    Util --> U4[storage.py]
    Util --> U5[cache.py]
    Util --> U6[ui.py]
    Util --> U7[auth.py]
    Util --> U8[pdf_report.py]

    GH --> KAY[keep-alive.yml]
    Conf --> CT[config.toml]
    Conf --> ST[secrets.toml.example]
```

---

## 10. Roadmap Modul

```mermaid
gantt
    title Roadmap Pengembangan Platform
    dateFormat YYYY-MM-DD
    axisFormat %b %Y

    section MVP (Done)
    Modul DPPH                  :done, 2026-01-01, 2026-01-15
    Hybrid storage              :done, 2026-01-10, 2026-01-15
    Visualisasi + chart         :done, 2026-01-12, 2026-01-15
    ANOVA + Tukey HSD           :done, 2026-01-13, 2026-01-15
    PDF report                  :done, 2026-01-14, 2026-01-15
    Auth login                  :done, 2026-01-14, 2026-01-15

    section Fase 2
    Modul UAE lengkap (RSM)     :active, 2026-02-01, 30d
    Modul TPC lengkap           :2026-02-15, 30d
    Import Excel batch          :2026-03-01, 14d

    section Fase 3
    Multi-user dengan role      :2026-03-15, 21d
    Audit trail                 :2026-04-01, 14d
    Dashboard publik (read-only):2026-04-15, 14d
```

---

> Tip: untuk preview Mermaid lokal di VS Code, install ekstensi
> [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid).
