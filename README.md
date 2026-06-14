<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# Platform Digital Evaluasi Antioksidan Daun Salam

**Aplikasi Streamlit untuk input, perhitungan otomatis, analisis statistik,**
**dan visualisasi uji aktivitas antioksidan metode DPPH**
**dengan backend Google Sheets.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Sheets](https://img.shields.io/badge/Backend-Google%20Sheets-34A853?logo=googlesheets&logoColor=white)](https://www.google.com/sheets/about/)
[![Plotly](https://img.shields.io/badge/Charts-Plotly-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![ReportLab](https://img.shields.io/badge/PDF-ReportLab-CC0000)](https://www.reportlab.com/)
[![License](https://img.shields.io/badge/License-Academic-blue)](#)

[**Mulai Cepat**](#mulai-cepat) ·
[**Setup Google Sheets**](#setup-google-sheets) ·
[**Fitur**](#fitur-utama) ·
[**Diagram**](docs/DIAGRAMS.md) ·
[**Panduan Pengguna**](PANDUAN.md)

</div>

---

## Pengantar

Platform digital untuk mengelola, menganalisis, dan melaporkan hasil
pengujian aktivitas antioksidan metode **DPPH** (1,1-diphenyl-2-picrylhydrazyl).
Dirancang khusus untuk skenario riset skala laboratorium dengan data tabular
yang relatif kecil sehingga **Google Sheets** menjadi pilihan backend yang
ideal: gratis, multi-device, dan dapat diaudit langsung di browser.

### Mengapa Platform Ini

| Tantangan Riset | Solusi Platform |
|---|---|
| Hitungan manual % inhibisi & IC50 dari Excel rawan typo | Input mentah → otomatis hitung dengan rumus tervalidasi |
| Replikasi data antar laptop & lab | Google Sheets sebagai single source of truth |
| Pembimbing minta uji beda nyata (ANOVA + Tukey) | Modul terintegrasi dengan interpretasi otomatis |
| Lampiran tesis butuh laporan rapi per percobaan | Generator PDF satu klik |
| Akses dari HP saat di lab | Layout responsif, sidebar otomatis collapse |
| Streamlit Cloud auto-sleep setelah 7 hari | GitHub Actions ping setiap 6 jam |

---

## Daftar Isi

1. [Fitur Utama](#fitur-utama)
2. [Mulai Cepat](#mulai-cepat)
3. [Setup Google Sheets](#setup-google-sheets)
4. [Auth Login](#auth-login)
5. [Modul ANOVA + Tukey HSD](#modul-anova--tukey-hsd)
6. [Export PDF Report](#export-pdf-report)
7. [Deploy ke Streamlit Community Cloud](#deploy-ke-streamlit-community-cloud)
8. [Anti Cold-Start](#anti-cold-start)
9. [Responsive (Mobile-Friendly)](#responsive-mobile-friendly)
10. [Rumus & Validasi Saintifik](#rumus--validasi-saintifik)
11. [Struktur Folder](#struktur-folder)
12. [Diagram & Visual Reference](docs/DIAGRAMS.md)
13. [Troubleshooting](#troubleshooting)
14. [Roadmap](#roadmap)

---

## Fitur Utama

| Modul | Deskripsi |
|---|---|
| **Input cerdas DPPH** | Form 3 replikasi × 6 konsentrasi, otomatis hitung % inhibisi (metode pairwise blanko), mean, SD, regresi linear, IC50, dan kategori antioksidan |
| **Visualisasi interaktif** | Kurva regresi dengan annotation IC50 + garis 50%, bar chart dengan error bar SD, line chart perbandingan IC50 antar grup |
| **Statistik tesis** | ANOVA satu arah + post-hoc Tukey HSD untuk uji beda nyata antar waktu inkubasi, metode ekstraksi, atau sampel |
| **PDF report** | Generator laporan PDF per percobaan (A4, 2 halaman): metadata, tabel data, kurva regresi high-res, kesimpulan siap kutip |
| **Auth login** | Passcode sederhana via `secrets.toml` untuk gate write operations (timing-attack safe via `hmac.compare_digest`) |
| **CRUD lengkap** | Lihat, edit massal, dan hapus per percobaan langsung dari worksheet |
| **Hybrid storage** | Auto-pilih: Google Sheets jika `secrets.toml` ter-set, fallback ke CSV lokal untuk development |
| **Multi-modul** | DPPH (utama) + UAE (parameter ekstraksi) + TPC (total fenolik) sebagai placeholder siap-isi |
| **Responsive** | Layout otomatis stack di mobile, sidebar collapse, grafik scroll horizontal |
| **Performance** | Cache 60 detik untuk read, lazy import Plotly, fastReruns, file-watcher off di production |
| **Anti cold-start** | Workflow GitHub Actions ping app tiap 6 jam |
| **Template siap pakai** | File `template_gsheet.xlsx` di root repo bisa langsung di-import ke Google Sheets |

---

## Mulai Cepat

```powershell
# Clone & masuk folder app
cd app

# Buat virtualenv
python -m venv .venv
.venv\Scripts\Activate.ps1   # PowerShell
# atau: source .venv/bin/activate     (Linux/macOS)

# Install dependencies
pip install -r requirements.txt

# Jalankan
streamlit run Home.py
```

Buka <http://localhost:8501>. Tanpa konfigurasi, app jalan dalam **mode CSV
lokal** (data ke `app/data/*.csv`). Untuk pindah ke Google Sheets, ikuti
section [Setup Google Sheets](#setup-google-sheets) di bawah.

> Untuk panduan langkah demi langkah versi non-teknis, baca [PANDUAN.md](PANDUAN.md).

### Alur Kerja Riset

```mermaid
flowchart LR
    A[Lab: Spektrofotometer] --> B[Streamlit: Input DPPH]
    B --> C[Auto-hitung<br/>%inhibisi & IC50]
    C --> D[(Google Sheets)]
    D --> E[Visualisasi]
    D --> F[ANOVA]
    D --> G[PDF Report]

    style D fill:#34A853,color:#fff
```

Diagram lengkap (8 jenis): [docs/DIAGRAMS.md](docs/DIAGRAMS.md).

---

## Setup Google Sheets

Total ~10 menit, satu kali setup. Hasil akhir: aplikasi terhubung ke
spreadsheet yang dapat diakses multi-device.

```mermaid
flowchart LR
    A[1. Upload<br/>template] --> B[2. Buat<br/>Service Account] --> C[3. Share<br/>sheet] --> D[4. Edit<br/>secrets.toml] --> E[5. Verify]
    style E fill:#34A853,color:#fff
```

### Langkah 1 — Upload Template

`template_gsheet.xlsx` di root repo berisi **5 tab** siap pakai:

| Tab | Isi | Wajib? |
|---|---|:---:|
| `PETUNJUK` | Panduan + flowchart alur visual | Boleh dihapus |
| `KALKULATOR` | Kalkulator self-contained dengan formula GSheet (edit absorbansi → IC50 auto-update) | Boleh dihapus, atau dipakai untuk quick-check |
| `DPPH` | Database long-format untuk aplikasi | **WAJIB** |
| `UAE` | Parameter ekstraksi (placeholder) | **WAJIB** |
| `TPC` | Total fenolik (placeholder) | **WAJIB** |

**Cara upload:**

1. Buka <https://sheets.google.com> → klik **Blank** (icon `+` plus warna-warni)
2. Menu **File → Import**
3. Pilih tab **Upload** → drag-drop file `template_gsheet.xlsx`
4. Di dialog "Import file": pilih **Replace spreadsheet** → klik **Import data**
5. Tunggu 5–10 detik. Spreadsheet langsung terisi 5 tab.
6. Rename spreadsheet (default "Untitled") jadi mis. `Tesis - Data Antioksidan`
7. Salin URL spreadsheet — bagian `https://docs.google.com/spreadsheets/d/`**`SPREADSHEET_ID`**`/edit/...`. Catat `SPREADSHEET_ID`.

> **Tips KALKULATOR:** kalau lo cuma mau quick-check IC50 tanpa buka aplikasi,
> buka tab `KALKULATOR`. Edit cell **kuning** (absorbansi & metadata),
> hasil di cell **hijau/kuning-tua** (IC50, kategori, regresi) auto-update.
> Cocok buat asisten lab yang gak suka buka Streamlit.

### Langkah 2 — Service Account di Google Cloud

> **Apa itu Service Account?** Akun robot khusus untuk app — punya email
> sendiri (contoh: `streamlit-bot@xxx.iam.gserviceaccount.com`), bisa diberi
> akses spesifik ke Google Sheet. Aman karena tidak butuh password user.

```mermaid
sequenceDiagram
    actor U as Lo
    participant GCP as Google Cloud Console
    participant SA as Service Account
    U->>GCP: 1. Create Project
    U->>GCP: 2. Enable Sheets API + Drive API
    U->>GCP: 3. Create Service Account "streamlit-bot"
    U->>GCP: 4. Add Key (JSON)
    GCP-->>U: credentials.json (download)
    Note over U: Simpan file JSON,<br/>jangan upload ke GitHub
```

**Step by step (5 menit):**

| # | Aksi | Lokasi |
|---|---|---|
| 1 | Buka **<https://console.cloud.google.com>** | Browser |
| 2 | Klik dropdown project (atas-kiri, dekat logo Google Cloud) → **NEW PROJECT** | Top bar |
| 3 | Project name: `tesis-platform` (atau bebas) → **CREATE** | Modal |
| 4 | Pastikan project aktif (cek di top bar — nama project harus muncul) | Top bar |
| 5 | Hamburger menu (☰) → **APIs & Services → Library** | Sidebar |
| 6 | Search **"Google Sheets API"** → klik hasilnya → **ENABLE** | Page |
| 7 | Klik panah back → search **"Google Drive API"** → klik → **ENABLE** | Page |
| 8 | Hamburger menu → **APIs & Services → Credentials** | Sidebar |
| 9 | Klik **+ CREATE CREDENTIALS** (atas) → pilih **Service account** | Top bar |
| 10 | Service account name: `streamlit-bot` → **CREATE AND CONTINUE** | Form |
| 11 | Skip "Grant this service account access" → **CONTINUE → DONE** | Form |
| 12 | Di tabel "Service Accounts", klik email service account yang baru dibuat | Table |
| 13 | Tab **KEYS** → **ADD KEY → Create new key → JSON → CREATE** | Tab |
| 14 | File `xxx-yyy-zzz.json` ter-download otomatis | Browser download |

> ⚠️ **Hati-hati:**
> - File JSON ini = kunci akses ke sheet. **Jangan upload ke GitHub publik**.
> - Sudah otomatis di-`.gitignore` di repo ini (`*.json`).
> - Kalau lo lupa simpan, tinggal generate ulang di langkah 13.

### Langkah 3 — Share Sheet ke Service Account

Service account harus diberi izin untuk akses sheet lo.

1. Buka file JSON yang barusan di-download (pakai Notepad/VS Code)
2. Cari nilai `"client_email"` — copy email-nya, mis:
   `streamlit-bot@tesis-platform.iam.gserviceaccount.com`
3. Buka spreadsheet Google Sheet (yang dari Langkah 1)
4. Klik tombol **Share** (kanan atas, biru)
5. Paste email service account → **Set akses: Editor** (bukan Viewer)
6. **Uncheck** "Notify people" (gak perlu kirim email)
7. Klik **Share**

> **Cek sukses:** klik dropdown share lagi — service account email harus muncul
> dengan label "Editor".

### Langkah 4 — Konfigurasi `secrets.toml`

Buat file dari template:

```powershell
cd app
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
notepad .streamlit\secrets.toml
```

Pemetaan field JSON → `secrets.toml`:

| Field di file JSON | Pasangkan ke `secrets.toml` |
|---|---|
| `"type"` | `type = "service_account"` |
| `"project_id"` | `project_id = "..."` |
| `"private_key_id"` | `private_key_id = "..."` |
| `"private_key"` | `private_key = "-----BEGIN ... -----END PRIVATE KEY-----\n"` |
| `"client_email"` | `client_email = "..."` |
| `"client_id"` | `client_id = "..."` |
| `"auth_uri"` | `auth_uri = "..."` |
| `"token_uri"` | `token_uri = "..."` |
| `"auth_provider_x509_cert_url"` | sama |
| `"client_x509_cert_url"` | sama |

Plus tambahan **untuk spreadsheet**:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
worksheet  = "DPPH"

type = "service_account"
project_id = "tesis-platform"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-bot@tesis-platform.iam.gserviceaccount.com"
client_id = "1234567890..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-bot%40tesis-platform.iam.gserviceaccount.com"
```

> **Penting tentang `private_key`:**
>
> Field ini paling sering bikin error. Aturan:
> - Salin **persis** dari JSON termasuk karakter `\n` (backslash + n)
> - Tetap dalam **satu baris** dengan tanda kutip ganda `"..."`
> - **Jangan** ganti `\n` dengan baris baru asli (tekan Enter)
> - **Jangan** pakai single quote `'...'`
>
> Contoh **benar**:
> ```toml
> private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
> ```
> Contoh **salah** (akan error):
> ```toml
> private_key = """
> -----BEGIN PRIVATE KEY-----
> MIIE...
> -----END PRIVATE KEY-----
> """
> ```

### Langkah 5 — Verifikasi

```powershell
streamlit run Home.py
```

Banner di Home harus berubah jadi: **"Backend penyimpanan: Google Sheets (terhubung)"**.

---

## Auth Login

Gate write operation (input/edit/hapus) dengan passcode sederhana.

```toml
# .streamlit/secrets.toml
[auth]
enabled = true
passcode = "ganti-passcode-rahasia-lo"
label    = "Peneliti"
```

Behaviour:

- Halaman **view** (Home, Visualisasi, ANOVA) tetap dapat diakses tanpa login
- Tombol **Simpan / Hapus** disabled sampai passcode benar
- Form login muncul di sidebar, validasi pakai `hmac.compare_digest`
- Hapus section `[auth]` atau set `enabled = false` untuk menonaktifkan

```mermaid
flowchart LR
    A[User] --> B{auth aktif?}
    B -->|Tidak| F[Bisa input bebas]
    B -->|Ya| C{Sudah login?}
    C -->|Ya| F
    C -->|Tidak| D[Form passcode]
    D --> E{Cocok?}
    E -->|Ya| F
    E -->|Tidak| D
    style F fill:#C8E6C9
```

---

## Modul ANOVA + Tukey HSD

Halaman **Analisis ANOVA** (`pages/6_Analisis_ANOVA.py`) untuk uji beda
nyata secara statistik (umumnya diminta pembimbing tesis).

| Metrik | Variabel pengelompok |
|---|---|
| IC50 (ppm) per percobaan | Waktu inkubasi (menit) |
| % Inhibisi pada konsentrasi tertentu (per replikasi) | Metode ekstraksi |
| | Sampel |

Pipeline:

1. **Statistik deskriptif per grup** — n, mean, SD, SEM, min, max
2. **Boxplot** dengan strip plot semua titik
3. **ANOVA satu arah** (`scipy.stats.f_oneway`) — F-statistic, p-value, df, interpretasi otomatis
4. **Post-hoc Tukey HSD** (`statsmodels.stats.multicomp.pairwise_tukeyhsd`) — pasangan mana yang berbeda nyata
5. **Download CSV** hasil lengkap (deskriptif + ANOVA + Tukey)

Contoh interpretasi (auto-generate):

> Terdapat perbedaan yang signifikan secara statistik antar grup
> (p = 0.0003 < 0.05). Lanjut ke uji post-hoc Tukey HSD untuk
> mengetahui pasangan grup mana yang berbeda.

---

## Export PDF Report

Generator PDF per percobaan untuk **lampiran tesis** atau dokumentasi internal.

**Trigger:** halaman Visualisasi DPPH → pilih `experiment_id` → **Generate Laporan PDF** → **Download**.

Isi (A4, 2 halaman):

1. Header — judul, identitas riset
2. Metadata table — experiment_id, tanggal, sampel, metode, waktu inkubasi, IC50, kategori, R-squared, persamaan, catatan
3. Data table — 10 kolom (konsentrasi, abs 1/2/3, abs mean, % inhibisi 1/2/3, mean, SD)
4. Kurva regresi — high-res PNG via Plotly + Kaleido
5. Kesimpulan — kalimat siap kutip
6. Footer

---

## Deploy ke Streamlit Community Cloud

```mermaid
flowchart LR
    A[Push ke GitHub] --> B[share.streamlit.io]
    B --> C[New app]
    C --> D[Pilih repo + branch]
    D --> E[Main file: app/Home.py]
    E --> F[Advanced: paste secrets.toml]
    F --> G[Deploy]
    G --> H[Live URL]
    style G fill:#34A853,color:#fff
```

1. Push repo ke GitHub. Pastikan `secrets.toml` **TIDAK** ke-push (sudah di `.gitignore`).
2. Buka <https://share.streamlit.io> → **New app**
3. Konfigurasi:
   - Repository: `username/repo`
   - Branch: `main`
   - Main file path: `app/Home.py`
4. **Advanced settings → Secrets**: paste isi `secrets.toml`
5. Deploy. Build pertama 1–3 menit.

---

## Anti Cold-Start

Streamlit Community Cloud men-sleep app yang tidak diakses ~7 hari. Akses
pertama setelah sleep butuh 30–60 detik. Tiga lapis pertahanan:

```mermaid
flowchart TB
    subgraph L1[Layer 1: Caching]
        A1[Read DPPH/UAE/TPC] --> A2[@st.cache_data ttl=60s]
    end
    subgraph L2[Layer 2: Config]
        B1[runOnSave=false]
        B2[fileWatcherType=none]
        B3[fastReruns=true]
        B4[Lazy import Plotly]
    end
    subgraph L3[Layer 3: Keep-Alive]
        C1[GitHub Actions cron] -->|6 jam| C2[ping /_stcore/health]
    end
    L1 --> Warm
    L2 --> Warm
    L3 --> Warm
    Warm[App selalu warm]
    style Warm fill:#C8E6C9
```

**Aktifkan keep-alive (1 menit):**

1. Push repo ke GitHub
2. **Settings → Secrets → Actions → New repository secret**:
   - Name: `STREAMLIT_APP_URL`
   - Value: `https://your-app.streamlit.app`
3. Selesai. Workflow ping otomatis tiap 6 jam (lihat tab **Actions**).

**Test manual:**

```powershell
python app\keep_alive.py https://your-app.streamlit.app
# [WARM] https://... (0.42s) HTTP 200: ok
```

---

## Responsive (Mobile-Friendly)

Tested viewport: **360px** (HP kecil), **768px** (tablet), **1280px+** (desktop).

| Behaviour | Implementasi |
|---|---|
| Kolom auto-stack di < 640px | Custom CSS di `utils/ui.py` |
| Sidebar collapse otomatis | `initial_sidebar_state="auto"` |
| Tabel & chart full-width | `use_container_width=True` |
| Plotly scroll horizontal | CSS `overflow-x: auto` |
| Button full-width di mobile | CSS `width: 100%` saat layar kecil |
| Layout default `wide` | Hemat ruang di desktop |

---

## Rumus & Validasi Saintifik

```text
Metode pairwise (default, sesuai praktik lab umum):
    inhib_i = (Abs_blanko_i - Abs_sampel_i) / Abs_blanko_i × 100

Regresi linear:
    y = a · x + b      (x = ppm, y = % inhibisi rata-rata)

IC50:
    IC50 = (50 - b) / a   ppm
```

**Klasifikasi (Molyneux 2004; Blois 1958):**

| IC50 (ppm) | Kategori |
|---:|---|
| < 50 | Sangat kuat |
| 50 – 100 | Kuat |
| 100 – 150 | Sedang |
| 150 – 200 | Lemah |
| > 200 | Sangat lemah |

**Validasi terhadap data referensi (lab spreadsheet):**

| Metrik | Aplikasi | Referensi | Match |
|---|---:|---:|:---:|
| inhib_1 @ 5 mnt, 20 ppm | 29.6852 | 29.6852 | ✓ |
| inhib_2 @ 5 mnt, 20 ppm | 30.6428 | 30.6428 | ✓ |
| inhib_3 @ 5 mnt, 20 ppm | 30.7004 | 30.7004 | ✓ |
| **IC50 @ 5 mnt** | **47.114 ppm** | 47.11 ppm | ✓ |
| R-squared | 0.9913 | 0.9913 | ✓ |

Verifikasi ulang kapan saja:

```powershell
python app\tests\verify_with_excel.py
```

---

## Struktur Folder

```text
.
├── app/
│   ├── Home.py                      # Landing + dashboard
│   ├── pages/
│   │   ├── 1_Input_DPPH.py
│   │   ├── 2_Visualisasi_DPPH.py    # + tombol export PDF
│   │   ├── 3_Riwayat_Data.py
│   │   ├── 4_Input_UAE.py
│   │   ├── 5_Input_TPC.py
│   │   └── 6_Analisis_ANOVA.py
│   ├── utils/
│   │   ├── calculations.py          # %inhibisi, regresi, IC50, ANOVA, Tukey
│   │   ├── sheets.py                # Wrapper Google Sheets
│   │   ├── local_store.py           # Wrapper CSV (fallback)
│   │   ├── storage.py               # Facade auto-pilih backend
│   │   ├── cache.py                 # @st.cache_data layer
│   │   ├── ui.py                    # Responsive CSS + page setup
│   │   ├── auth.py                  # Passcode auth gate
│   │   └── pdf_report.py            # Generator PDF
│   ├── tests/
│   │   ├── verify_with_excel.py     # Validasi calc vs data referensi
│   │   └── build_template.py        # Generate template_gsheet.xlsx
│   ├── data/                        # Auto-created CSV fallback
│   ├── .streamlit/
│   │   ├── config.toml
│   │   └── secrets.toml.example
│   ├── keep_alive.py
│   └── requirements.txt
├── .github/workflows/
│   └── keep-alive.yml
├── docs/
│   └── DIAGRAMS.md                  # 10 diagram Mermaid
├── template_gsheet.xlsx             # Template upload Google Sheets
├── PANDUAN.md                       # Panduan untuk orang awam
└── README.md                        # File ini
```

---

## Troubleshooting

<details>
<summary><b>Banner masih "CSV Lokal" padahal sudah isi <code>secrets.toml</code></b></summary>

- Pastikan path: `app/.streamlit/secrets.toml` (bukan di root repo)
- Section header persis `[connections.gsheets]` (huruf kecil)
- Restart `streamlit run Home.py`
- Toggle "Mode lokal (CSV)" di Home — pastikan tidak aktif

</details>

<details>
<summary><b>Error <code>APIError: invalid_grant</code> atau <code>403 Forbidden</code></b></summary>

- Lupa share Google Sheet ke email service account → ulang Langkah 3
- Pastikan akses **Editor** (bukan Viewer/Commenter)
- Pastikan **Google Sheets API** & **Google Drive API** sudah enabled

</details>

<details>
<summary><b>Error <code>private_key</code> malformed</b></summary>

- Saat menyalin dari JSON, pertahankan karakter `\n` literal (jangan ganti dengan baris baru)
- Pastikan dikutip ganda `"..."`, bukan single quote
- Di Streamlit Cloud "Secrets", tempel format TOML asli (sama dengan file lokal)

</details>

<details>
<summary><b>Worksheet tab tidak ditemukan</b></summary>

- Tab harus bernama persis `DPPH`, `UAE`, `TPC` (case-sensitive)
- Tab default `Sheet1` tidak dipakai

</details>

<details>
<summary><b>App lambat di akses pertama (cold start)</b></summary>

- Normal kalau app baru deploy ulang atau lebih dari 7 hari tidak diakses
- Aktifkan keep-alive workflow (lihat [Anti Cold-Start](#anti-cold-start))
- Setelah cold start pertama, akses berikutnya instan karena cache 60 detik

</details>

<details>
<summary><b>Mobile: chart Plotly terpotong</b></summary>

- Geser horizontal di area chart (overflow-x: auto)
- Atau rotate HP ke landscape

</details>

<details>
<summary><b>Data hilang setelah refresh di Streamlit Cloud</b></summary>

- Mode CSV Lokal di Streamlit Cloud tidak persisten (filesystem ephemeral)
- Pindah ke Google Sheets

</details>

<details>
<summary><b>PDF tidak ada chart-nya</b></summary>

- Pastikan `kaleido` ter-install: `pip install kaleido`
- Restart streamlit

</details>

---

## Roadmap

```mermaid
gantt
    title Roadmap Pengembangan
    dateFormat YYYY-MM-DD
    section MVP (Done)
    DPPH + Hybrid storage     :done, 2026-01-01, 2026-01-15
    ANOVA + PDF + Auth        :done, 2026-01-13, 2026-01-15
    section Fase 2
    Modul UAE lengkap (RSM)   :2026-02-01, 30d
    Modul TPC lengkap         :2026-02-15, 30d
    Import Excel batch        :2026-03-01, 14d
    section Fase 3
    Multi-user + role         :2026-03-15, 21d
    Audit trail               :2026-04-01, 14d
    Dashboard publik          :2026-04-15, 14d
```

---

## Lisensi & Atribusi

Platform akademik untuk keperluan tesis Magister Studi Lingkungan UNTIRTA.
Library third-party tunduk pada lisensi masing-masing.

**Stack utama:**
[Streamlit](https://streamlit.io/) ·
[pandas](https://pandas.pydata.org/) ·
[scipy](https://scipy.org/) ·
[statsmodels](https://www.statsmodels.org/) ·
[Plotly](https://plotly.com/python/) ·
[ReportLab](https://www.reportlab.com/) ·
[gspread](https://docs.gspread.org/) via [streamlit-gsheets-connection](https://github.com/streamlit/gsheets-connection)

---

<div align="center">

**Made for Magister Studi Lingkungan, Pascasarjana UNTIRTA**

[Mulai Cepat](#mulai-cepat) ·
[Diagram](docs/DIAGRAMS.md) ·
[Panduan Awam](PANDUAN.md)

</div>
