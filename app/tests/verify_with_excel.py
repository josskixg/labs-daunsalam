"""
Verifikasi: jalankan calculations.py terhadap data sumber, bandingkan
dengan angka rujukan (sheet riset asli yang menggunakan metode pairwise
blanko).

Toleransi: 1e-3 untuk inhib %, 1e-2 untuk IC50 (rounding error wajar).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
from utils.calculations import process_experiment, classify_ic50

# Data input mentah (Abs 1, Abs 2, Abs 3) per waktu inkubasi
SETS = {
    5: pd.DataFrame(
        {
            "konsentrasi": [0, 20, 40, 60, 80, 100],
            "abs_1": [0.667, 0.469, 0.399, 0.268, 0.141, 0.051],
            "abs_2": [0.669, 0.464, 0.398, 0.267, 0.142, 0.053],
            "abs_3": [0.671, 0.465, 0.392, 0.267, 0.142, 0.055],
        }
    ),
    6: pd.DataFrame(
        {
            "konsentrasi": [0, 20, 40, 60, 80, 100],
            "abs_1": [0.679, 0.489, 0.428, 0.379, 0.231, 0.112],
            "abs_2": [0.677, 0.492, 0.431, 0.371, 0.233, 0.115],
            "abs_3": [0.675, 0.495, 0.423, 0.373, 0.236, 0.117],
        }
    ),
}

# Nilai rujukan dari sheet riset (metode pairwise) untuk grup 5 menit
# konsentrasi 20 ppm: % Inhib = [29.685, 30.643, 30.700], rata-rata 30.343
EXPECTED = {
    (5, 20): {"inhib_1": 29.6852, "inhib_2": 30.6428, "inhib_3": 30.7004},
    (5, 100): {"inhib_1": 92.3538, "inhib_2": 92.0777, "inhib_3": 91.8033},
    (6, 20): {"inhib_1": 27.9823, "inhib_2": 27.3264, "inhib_3": 26.6667},
}


def main() -> int:
    failures = 0
    for waktu, df_in in SETS.items():
        proc, reg = process_experiment(df_in, blanko_method="pairwise")
        print(f"\n{'=' * 70}")
        print(f"  Waktu inkubasi {waktu} menit (metode: pairwise)")
        print(f"{'=' * 70}")
        print(
            proc[
                [
                    "konsentrasi",
                    "abs_mean",
                    "inhib_1",
                    "inhib_2",
                    "inhib_3",
                    "inhib_mean",
                    "inhib_sd",
                ]
            ]
            .round(4)
            .to_string(index=False)
        )
        print(f"\n  Persamaan : {reg.equation}")
        print(f"  R-squared : {reg.r_squared:.4f}")
        print(f"  IC50      : {reg.ic50:.3f} ppm  ({classify_ic50(reg.ic50)})")

        # Cross-check expected values
        for (w, k), expected in EXPECTED.items():
            if w != waktu:
                continue
            row = proc[proc["konsentrasi"] == k].iloc[0]
            for col, exp_val in expected.items():
                got = float(row[col])
                ok = abs(got - exp_val) < 1e-3
                marker = "OK" if ok else "FAIL"
                print(
                    f"  CHECK [{marker}] waktu={w} mnt, konsentrasi={k} ppm, "
                    f"{col}: expected={exp_val:.4f}, got={got:.4f}"
                )
                if not ok:
                    failures += 1

    print(f"\n{'=' * 70}")
    if failures == 0:
        print("  ALL CHECKS PASSED — perhitungan match data rujukan.")
        return 0
    print(f"  {failures} check(s) FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
