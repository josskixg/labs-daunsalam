"""
Keep-alive pinger untuk Streamlit Community Cloud.

Streamlit Cloud menidurkan app setelah ~7 hari tidak ada traffic
(dan kadang lebih cepat). Script ini ping endpoint /_stcore/health
biar app tetap warm.

Cara pakai:
1. Lokal:
       python keep_alive.py https://your-app.streamlit.app
2. GitHub Actions (lihat .github/workflows/keep-alive.yml)

Exit code 0 jika app warm, 1 jika down/cold.
"""

from __future__ import annotations

import sys
import time
import urllib.request
import urllib.error


def ping(url: str, timeout: float = 30.0) -> tuple[bool, float, str]:
    """Return (ok, elapsed_seconds, message)."""
    target = url.rstrip("/") + "/_stcore/health"
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(target, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace").strip()
            ok = r.status == 200 and "ok" in body.lower()
            return ok, time.perf_counter() - start, f"HTTP {r.status}: {body[:80]}"
    except urllib.error.HTTPError as e:
        return False, time.perf_counter() - start, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, time.perf_counter() - start, f"{type(e).__name__}: {e}"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python keep_alive.py <streamlit-app-url> [<url2> ...]")
        return 2

    failed = 0
    for url in argv[1:]:
        ok, elapsed, msg = ping(url)
        status = "WARM" if ok else "COLD/DOWN"
        print(f"[{status}] {url} ({elapsed:.2f}s) {msg}")
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
