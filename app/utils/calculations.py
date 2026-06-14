"""
Perhitungan aktivitas antioksidan metode DPPH.

Rumus utama (acuan: Molyneux 2004; Brand-Williams 1995):

    % Inhibisi = ((Abs_blanko - Abs_sampel) / Abs_blanko) * 100

IC50 dihitung dari regresi linear:

    y = a*x + b   ->   IC50 = (50 - b) / a

dengan x = konsentrasi (ppm), y = % inhibisi rata-rata.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


# ----------------------------------------------------------------------
# Hitungan dasar
# ----------------------------------------------------------------------
def percent_inhibition(abs_blanko: float, abs_sampel: float) -> float:
    """Return % inhibisi DPPH untuk 1 pasang absorbansi."""
    if abs_blanko in (0, None) or pd.isna(abs_blanko):
        return float("nan")
    return ((abs_blanko - abs_sampel) / abs_blanko) * 100.0


def inhibition_row(abs_blanko_mean: float, abs_replicates: Iterable[float]) -> dict:
    """
    Hitung % inhibisi per replikasi + rata-rata + SD untuk 1 konsentrasi.

    Returns dict:
        inhib_1, inhib_2, inhib_3, inhib_mean, inhib_sd
    """
    inhibs = [percent_inhibition(abs_blanko_mean, a) for a in abs_replicates]
    arr = np.array(inhibs, dtype=float)
    return {
        **{f"inhib_{i + 1}": v for i, v in enumerate(inhibs)},
        "inhib_mean": float(np.nanmean(arr)) if arr.size else float("nan"),
        "inhib_sd": float(np.nanstd(arr, ddof=1))
        if np.sum(~np.isnan(arr)) > 1
        else 0.0,
    }


# ----------------------------------------------------------------------
# Regresi linear & IC50
# ----------------------------------------------------------------------
@dataclass
class RegressionResult:
    slope: float  # a
    intercept: float  # b
    r_squared: float
    ic50: float  # ppm
    equation: str  # "y = a x + b"
    x: np.ndarray  # konsentrasi
    y: np.ndarray  # % inhibisi rata-rata

    def predict(self, x: np.ndarray | float) -> np.ndarray:
        return self.slope * np.asarray(x) + self.intercept


def fit_linear(
    concentrations: Iterable[float], inhibitions: Iterable[float]
) -> RegressionResult:
    """
    Fit regresi linear y = a*x + b dan hitung IC50.

    Konsentrasi 0 (blanko) diabaikan otomatis karena % inhibisi-nya 0/NaN
    dan biasanya tidak dipakai untuk regresi.
    """
    x = np.asarray(list(concentrations), dtype=float)
    y = np.asarray(list(inhibitions), dtype=float)

    mask = (~np.isnan(x)) & (~np.isnan(y)) & (x > 0)
    x_fit, y_fit = x[mask], y[mask]

    if x_fit.size < 2:
        return RegressionResult(
            slope=float("nan"),
            intercept=float("nan"),
            r_squared=float("nan"),
            ic50=float("nan"),
            equation="data tidak cukup",
            x=x_fit,
            y=y_fit,
        )

    res = stats.linregress(x_fit, y_fit)
    a, b = float(res.slope), float(res.intercept)
    r2 = float(res.rvalue) ** 2
    ic50 = (50.0 - b) / a if a != 0 else float("nan")
    eq = f"y = {a:.4f} x + {b:.4f}"
    return RegressionResult(
        slope=a,
        intercept=b,
        r_squared=r2,
        ic50=ic50,
        equation=eq,
        x=x_fit,
        y=y_fit,
    )


# ----------------------------------------------------------------------
# Klasifikasi aktivitas antioksidan (Molyneux 2004; Blois 1958)
# ----------------------------------------------------------------------
def classify_ic50(ic50: float) -> str:
    """Kategori kekuatan antioksidan berdasarkan IC50 (ppm)."""
    if ic50 is None or np.isnan(ic50):
        return "—"
    if ic50 < 50:
        return "Sangat kuat"
    if ic50 < 100:
        return "Kuat"
    if ic50 < 150:
        return "Sedang"
    if ic50 < 200:
        return "Lemah"
    return "Sangat lemah"


# ----------------------------------------------------------------------
# Pipeline lengkap untuk 1 percobaan
# ----------------------------------------------------------------------
def process_experiment(
    df_raw: pd.DataFrame,
    blanko_method: str = "pairwise",
) -> tuple[pd.DataFrame, RegressionResult]:
    """
    Input df_raw kolom wajib:
        konsentrasi, abs_1, abs_2, abs_3
    (konsentrasi 0 = blanko)

    Parameters
    ----------
    blanko_method : {"pairwise", "mean"}
        - "pairwise" (DEFAULT) : abs_blanko_i dipasangkan dengan abs_sampel_i,
          jadi inhib_1 = (abs_b1 - abs_s1)/abs_b1 * 100. Sesuai praktik
          lab umum dan output Panji.xlsx.
        - "mean" : semua replikasi sampel dibandingkan ke rata-rata blanko.

    Return:
        df_proc : tabel ber-kolom konsentrasi, abs_mean, inhib_1..3,
                  inhib_mean, inhib_sd
        reg     : RegressionResult
    """
    df = df_raw.copy().sort_values("konsentrasi").reset_index(drop=True)

    df["abs_mean"] = df[["abs_1", "abs_2", "abs_3"]].mean(axis=1)

    blanko_row = df[df["konsentrasi"] == 0]
    if blanko_row.empty:
        raise ValueError("Data blanko (konsentrasi 0) tidak ditemukan.")

    abs_blanko_reps = (
        blanko_row[["abs_1", "abs_2", "abs_3"]].values.flatten().astype(float)
    )
    abs_blanko_mean = float(np.mean(abs_blanko_reps))

    if blanko_method not in {"pairwise", "mean"}:
        raise ValueError(
            f"blanko_method harus 'pairwise' atau 'mean', got {blanko_method!r}"
        )

    rows = []
    for _, r in df.iterrows():
        if r["konsentrasi"] == 0:
            rows.append(
                {
                    "inhib_1": np.nan,
                    "inhib_2": np.nan,
                    "inhib_3": np.nan,
                    "inhib_mean": np.nan,
                    "inhib_sd": np.nan,
                }
            )
            continue

        sampel_reps = [r["abs_1"], r["abs_2"], r["abs_3"]]
        if blanko_method == "pairwise":
            inhibs = [
                percent_inhibition(abs_blanko_reps[i], sampel_reps[i]) for i in range(3)
            ]
            arr = np.array(inhibs, dtype=float)
            rows.append(
                {
                    "inhib_1": inhibs[0],
                    "inhib_2": inhibs[1],
                    "inhib_3": inhibs[2],
                    "inhib_mean": float(np.nanmean(arr)),
                    "inhib_sd": (
                        float(np.nanstd(arr, ddof=1))
                        if np.sum(~np.isnan(arr)) > 1
                        else 0.0
                    ),
                }
            )
        else:  # "mean"
            rows.append(inhibition_row(abs_blanko_mean, sampel_reps))

    df_inh = pd.DataFrame(rows)
    df_proc = pd.concat([df.reset_index(drop=True), df_inh], axis=1)

    reg = fit_linear(df_proc["konsentrasi"], df_proc["inhib_mean"])
    return df_proc, reg


# ----------------------------------------------------------------------
# ANOVA + Tukey HSD
# ----------------------------------------------------------------------
@dataclass
class AnovaResult:
    f_stat: float
    p_value: float
    df_between: int
    df_within: int
    significant_at_005: bool
    interpretation: str
    groups: dict[str, np.ndarray] = _field(default_factory=dict)
    n_groups: int = 0
    n_total: int = 0


def one_way_anova(
    groups: dict[str, Iterable[float]], alpha: float = 0.05
) -> AnovaResult:
    """
    Uji ANOVA satu arah.

    Parameters
    ----------
    groups : dict[label, iterable_of_values]
        Mis. {"5 menit": [...], "6 menit": [...]}
    alpha  : float, default 0.05
    """
    cleaned = {
        k: np.asarray([v for v in vals if not pd.isna(v)], dtype=float)
        for k, vals in groups.items()
    }
    cleaned = {k: v for k, v in cleaned.items() if v.size >= 2}

    if len(cleaned) < 2:
        return AnovaResult(
            f_stat=float("nan"),
            p_value=float("nan"),
            df_between=0,
            df_within=0,
            significant_at_005=False,
            interpretation="Butuh minimal 2 grup dengan masing-masing >= 2 data.",
            groups=cleaned,
            n_groups=len(cleaned),
            n_total=sum(v.size for v in cleaned.values()),
        )

    arrays = list(cleaned.values())
    f, p = stats.f_oneway(*arrays)
    n_total = sum(v.size for v in arrays)
    df_b = len(arrays) - 1
    df_w = n_total - len(arrays)

    sig = bool(p < alpha)
    if sig:
        interp = (
            f"Terdapat perbedaan yang signifikan secara statistik antar "
            f"grup (p = {p:.4f} < {alpha}). Lanjut ke uji post-hoc Tukey HSD "
            f"untuk mengetahui pasangan grup mana yang berbeda."
        )
    else:
        interp = (
            f"Tidak terdapat perbedaan signifikan antar grup "
            f"(p = {p:.4f} >= {alpha}). Variasi yang teramati kemungkinan "
            f"karena random noise."
        )

    return AnovaResult(
        f_stat=float(f),
        p_value=float(p),
        df_between=int(df_b),
        df_within=int(df_w),
        significant_at_005=sig,
        interpretation=interp,
        groups=cleaned,
        n_groups=len(cleaned),
        n_total=int(n_total),
    )


def tukey_hsd(groups: dict[str, Iterable[float]], alpha: float = 0.05) -> pd.DataFrame:
    """
    Tukey HSD post-hoc test (statsmodels).

    Returns DataFrame dengan kolom:
        group1, group2, mean_diff, p_adj, ci_lower, ci_upper, reject
    """
    from statsmodels.stats.multicomp import pairwise_tukeyhsd

    rows = []
    for label, vals in groups.items():
        for v in vals:
            if not pd.isna(v):
                rows.append({"group": str(label), "value": float(v)})
    if len(rows) < 4:
        return pd.DataFrame(
            columns=[
                "group1",
                "group2",
                "mean_diff",
                "p_adj",
                "ci_lower",
                "ci_upper",
                "reject",
            ]
        )

    long = pd.DataFrame(rows)
    res = pairwise_tukeyhsd(long["value"], long["group"], alpha=alpha)
    out = pd.DataFrame(
        data=res._results_table.data[1:],
        columns=res._results_table.data[0],
    )
    out = out.rename(
        columns={
            "group1": "group1",
            "group2": "group2",
            "meandiff": "mean_diff",
            "p-adj": "p_adj",
            "lower": "ci_lower",
            "upper": "ci_upper",
            "reject": "reject",
        }
    )
    return out


def descriptive_stats(groups: dict[str, Iterable[float]]) -> pd.DataFrame:
    """Statistik deskriptif per grup: n, mean, sd, min, max, sem."""
    rows = []
    for label, vals in groups.items():
        arr = np.asarray([v for v in vals if not pd.isna(v)], dtype=float)
        if arr.size == 0:
            continue
        rows.append(
            {
                "grup": label,
                "n": int(arr.size),
                "mean": float(np.mean(arr)),
                "sd": float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
                "sem": float(stats.sem(arr)) if arr.size > 1 else 0.0,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }
        )
    return pd.DataFrame(rows)
