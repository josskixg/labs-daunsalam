"""
Auto-generate app/.streamlit/secrets.toml dari Google service account JSON.

Usage:
    python app/tests/setup_gsheets.py path/to/credentials.json [SPREADSHEET_URL]

Atau interaktif (akan ditanya):
    python app/tests/setup_gsheets.py path/to/credentials.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECRETS_PATH = ROOT / "app" / ".streamlit" / "secrets.toml"


def escape_toml_string(s: str) -> str:
    """Escape string untuk TOML basic string (double-quoted)."""
    # TOML basic string: harus escape backslash & double-quote
    # \n di sumber sudah literal (2 karakter: \ + n) — kita biarkan saja
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def generate_secrets(
    json_path: Path,
    spreadsheet_url: str,
    worksheet: str = "DPPH",
    auth_passcode: str | None = None,
) -> str:
    """Build isi secrets.toml dari JSON service account."""
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Validasi field wajib
    required = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"JSON tidak lengkap, missing: {missing}")

    # private_key di JSON: string dengan \n LITERAL (sudah escape).
    # Setelah json.loads, jadi string dengan \n REAL (newline asli).
    # Untuk TOML, kita perlu \n LITERAL kembali.
    pk = (
        data["private_key"]
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )

    lines = [
        "# ============================================================",
        "# secrets.toml - auto-generated dari service account JSON",
        "# JANGAN commit file ini ke git (sudah di-.gitignore)",
        "# ============================================================",
        "",
        "[connections.gsheets]",
        f'spreadsheet = "{spreadsheet_url}"',
        f'worksheet  = "{worksheet}"',
        "",
        f'type = "{data["type"]}"',
        f'project_id = "{data["project_id"]}"',
        f'private_key_id = "{data["private_key_id"]}"',
        f'private_key = "{pk}"',
        f'client_email = "{data["client_email"]}"',
        f'client_id = "{data["client_id"]}"',
        f'auth_uri = "{data["auth_uri"]}"',
        f'token_uri = "{data["token_uri"]}"',
        f'auth_provider_x509_cert_url = "{data["auth_provider_x509_cert_url"]}"',
        f'client_x509_cert_url = "{data["client_x509_cert_url"]}"',
    ]

    # Universe domain (Google API v3+)
    if "universe_domain" in data:
        lines.append(f'universe_domain = "{data["universe_domain"]}"')

    # Auth opsional
    if auth_passcode:
        lines.extend(
            [
                "",
                "[auth]",
                "enabled = true",
                f'passcode = "{auth_passcode}"',
                'label    = "Peneliti"',
            ]
        )

    lines.append("")  # trailing newline
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    json_path = Path(argv[1]).expanduser().resolve()
    if not json_path.exists():
        print(f"ERROR: File tidak ditemukan: {json_path}")
        return 1

    print(f"Reading: {json_path}")

    # Spreadsheet URL
    if len(argv) >= 3:
        url = argv[2]
    else:
        print("\nPaste URL Google Sheet lo (yg sudah di-share ke service account):")
        print("Format: https://docs.google.com/spreadsheets/d/XXXXXXXX/edit")
        url = input("> ").strip()
    if not url.startswith("https://docs.google.com/spreadsheets/"):
        print(f"WARNING: URL tidak tampak seperti Google Sheets URL: {url!r}")

    # Worksheet (default DPPH)
    worksheet = "DPPH"
    if len(argv) >= 4:
        worksheet = argv[3]

    # Auth passcode (opsional)
    print("\n(Opsional) Set passcode untuk gate tombol Simpan/Hapus.")
    print("Kosongkan kalau tidak mau pakai auth.")
    passcode = input("Passcode auth (Enter untuk skip): ").strip() or None

    # Read service account email untuk reminder share
    data = json.loads(json_path.read_text(encoding="utf-8"))
    sa_email = data.get("client_email", "(unknown)")

    # Generate
    content = generate_secrets(
        json_path, url, worksheet=worksheet, auth_passcode=passcode
    )

    # Backup existing
    if SECRETS_PATH.exists():
        backup = SECRETS_PATH.with_suffix(".toml.bak")
        backup.write_text(SECRETS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"\nBackup secrets.toml lama -> {backup.name}")

    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote: {SECRETS_PATH}")
    print(f"  Size: {SECRETS_PATH.stat().st_size:,} bytes")
    print(f"  Lines: {len(content.splitlines())}")

    print("\n" + "=" * 60)
    print("CHECKLIST SEBELUM RESTART STREAMLIT:")
    print("=" * 60)
    print(f"[ ] Sheet sudah di-share ke EDITOR untuk:")
    print(f"    {sa_email}")
    print(f"[ ] Tab di sheet bernama persis: DPPH, UAE, TPC")
    print(f"[ ] Google Sheets API + Drive API aktif di project")
    print(f"    https://console.cloud.google.com/apis/dashboard")
    print()
    print("Restart streamlit:")
    print("    streamlit run app/Home.py")
    print()
    print("Banner Home harus berubah jadi:")
    print('    "Backend: Google Sheets · terhubung"')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
