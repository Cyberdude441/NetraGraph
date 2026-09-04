"""Pure deterministic, numerically reproducible statistical divergence algorithms for Drift Observatory.

All functions are guaranteed to be deterministic and numerically reproducible within
floating-point tolerance (+/- 1e-7) for identical inputs, ordering, configuration,
algorithm version, and compatible runtime environments.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from scipy import stats


def clean_numeric_array(data: Union[Sequence[float], np.ndarray]) -> np.ndarray:
    """Filter out None, NaN, and infinite values deterministically."""
    arr = np.asarray(data, dtype=np.float64)
    valid_mask = np.isfinite(arr)
    return arr[valid_mask]


def deterministic_subsample(data: Sequence[Any], max_samples: int = 50000) -> List[Any]:
    """
    Subsamples a sequence using deterministic arithmetic striding if length exceeds limit.
    Guarantees bitwise-identical subset selection regardless of runtime iteration order.
    """
    n = len(data)
    if n <= max_samples:
        return list(data)
    step = n / float(max_samples)
    return [data[int(i * step)] for i in range(max_samples)]


def compute_psi(
    reference: Union[Sequence[float], np.ndarray],
    comparison: Union[Sequence[float], np.ndarray],
    num_bins: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """
    Calculates Population Stability Index (PSI) using reference quantiles and Laplace smoothing.
    
    Formula:
        PSI = Sum_i (P_i - Q_i) * ln(P_i / Q_i)
    where P_i is the proportion in comparison and Q_i is the proportion in reference.
    """
    ref_clean = clean_numeric_array(reference)
    cmp_clean = clean_numeric_array(comparison)

    if len(ref_clean) == 0 or len(cmp_clean) == 0:
        return 0.0

    # If all reference values are identical
    if np.all(ref_clean == ref_clean[0]):
        if np.all(cmp_clean == ref_clean[0]):
            return 0.0
        return 1.0  # Total divergence

    # Compute deterministic quantile bin edges on reference
    percentiles = np.linspace(0, 100, num_bins + 1)
    raw_edges = np.percentile(ref_clean, percentiles)

    # Disambiguate duplicate quantile edges to ensure strict monotonicity
    edges = [raw_edges[0]]
    for i in range(1, len(raw_edges)):
        val = raw_edges[i]
        if val <= edges[-1]:
            val = edges[-1] + 1e-6
        edges.append(val)
    edges = np.array(edges)

    # Extend boundary edges slightly to catch min/max inclusively
    edges[0] -= 1e-6
    edges[-1] += 1e-6

    # Histogram binning
    ref_counts, _ = np.histogram(ref_clean, bins=edges)
    cmp_counts, _ = np.histogram(cmp_clean, bins=edges)

    k = len(ref_counts)
    n_ref = len(ref_clean)
    n_cmp = len(cmp_clean)

    # Laplace smoothing
    q = (ref_counts + epsilon) / (n_ref + k * epsilon)
    p = (cmp_counts + epsilon) / (n_cmp + k * epsilon)

    # Population Stability Index
    psi_val = np.sum((p - q) * np.log(p / q))
    return round(float(max(0.0, psi_val)), 7)


def compute_jsd(
    reference_counts: Union[Dict[str, Union[int, float]], Sequence[float]],
    comparison_counts: Union[Dict[str, Union[int, float]], Sequence[float]],
    epsilon: float = 1e-4,
) -> float:
    """
    Calculates symmetric Jensen-Shannon Divergence (JSD) using base-2 logarithm.
    
    Formula:
        JSD(P || Q) = 0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M)
        where M = 0.5 * (P + Q)
    
    Bounded strictly in [0.0, 1.0].
    """
    if isinstance(reference_counts, dict) and isinstance(comparison_counts, dict):
        all_categories = sorted(set(reference_counts.keys()) | set(comparison_counts.keys()))
        k = len(all_categories)
        if k == 0:
            return 0.0

        ref_total = sum(reference_counts.values())
        cmp_total = sum(comparison_counts.values())

        if ref_total <= 0 and cmp_total <= 0:
            return 0.0

        # Laplace smoothing across union of categories
        p = np.array([(float(reference_counts.get(c, 0)) + epsilon) / (ref_total + k * epsilon) for c in all_categories])
        q = np.array([(float(comparison_counts.get(c, 0)) + epsilon) / (cmp_total + k * epsilon) for c in all_categories])
    else:
        ref_arr = np.asarray(reference_counts, dtype=np.float64)
        cmp_arr = np.asarray(comparison_counts, dtype=np.float64)
        k = max(len(ref_arr), len(cmp_arr))
        if k == 0:
            return 0.0

        p_padded = np.zeros(k)
        p_padded[:len(ref_arr)] = ref_arr
        q_padded = np.zeros(k)
        q_padded[:len(cmp_arr)] = cmp_arr

        p = (p_padded + epsilon) / (np.sum(p_padded) + k * epsilon)
        q = (q_padded + epsilon) / (np.sum(q_padded) + k * epsilon)

    # Mixture distribution
    m = 0.5 * (p + q)

    # KL divergences with base-2 log
    kl_pm = np.sum(p * np.log2(p / m))
    kl_qm = np.sum(q * np.log2(q / m))

    jsd_val = 0.5 * kl_pm + 0.5 * kl_qm
    return round(float(max(0.0, min(1.0, jsd_val))), 7)


def compute_wasserstein(
    reference: Union[Sequence[float], np.ndarray],
    comparison: Union[Sequence[float], np.ndarray],
) -> float:
    """
    Calculates 1D Earth Mover's Distance (Wasserstein-1 distance) between continuous distributions.
    """
    ref_clean = clean_numeric_array(reference)
    cmp_clean = clean_numeric_array(comparison)

    if len(ref_clean) == 0 or len(cmp_clean) == 0:
        return 0.0

    w_dist = stats.wasserstein_distance(ref_clean, cmp_clean)
    return round(float(max(0.0, w_dist)), 7)


def compute_ks_statistic(
    reference: Union[Sequence[float], np.ndarray],
    comparison: Union[Sequence[float], np.ndarray],
) -> float:
    """
    Calculates Kolmogorov-Smirnov 2-sample statistic (maximum vertical distance between empirical CDFs).
    """
    ref_clean = clean_numeric_array(reference)
    cmp_clean = clean_numeric_array(comparison)

    if len(ref_clean) == 0 or len(cmp_clean) == 0:
        return 0.0

    ks_res = stats.ks_2samp(ref_clean, cmp_clean)
    return round(float(max(0.0, min(1.0, ks_res.statistic))), 7)


def compute_missingness_delta(ref_missing_rate: float, cmp_missing_rate: float) -> float:
    """Calculates absolute difference in missingness/null rates."""
    delta = abs(cmp_missing_rate - ref_missing_rate)
    return round(float(max(0.0, min(1.0, delta))), 7)
