"""P25 tests: verde total, regressão pega e limiar pré-registrado."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p25_eval.suite import (
    GOLDEN_DOUBLE,
    GOLDEN_SHOUT,
    RegressionBlocked,
    gate,
    pass_rate,
    run_suite,
    target_double,
    target_shout,
)


def broken_double(n: int) -> int:
    """Mutante: soma 1 em vez de dobrar (regressão simulada)."""
    return n + 1


def test_clean_suite_passes_gate_at_full_rate():
    # Given: fns corretas e limiar máximo
    double_results = run_suite(GOLDEN_DOUBLE, target_double)
    shout_results = run_suite(GOLDEN_SHOUT, target_shout)
    # When: gate em 1.0
    # Then: 100% e sem bloqueio
    assert gate(double_results, 1.0) == 1.0
    assert gate(shout_results, 1.0) == 1.0


def test_broken_fn_fails_named_cases_and_blocks():
    # Given: mutante no lugar da fn correta
    results = run_suite(GOLDEN_DOUBLE, broken_double)
    # When/Then: falhas nomeadas e gate bloqueia
    assert pass_rate(results) < 1.0
    failed = [r["id"] for r in results if not r["passed"]]
    assert "double-pos" in failed
    with pytest.raises(RegressionBlocked, match="double-pos"):
        gate(results, 1.0)


def test_threshold_boundary_is_inclusive():
    # Given: taxa exata 0.5 (identidade acerta o zero, erra o 21)
    results = run_suite(GOLDEN_DOUBLE[:2], lambda n: n)
    assert pass_rate(results) == 0.5
    # When/Then: igual passa, acima bloqueia (limiar pré-registrado)
    assert gate(results, 0.5) == 0.5
    with pytest.raises(RegressionBlocked, match="rate 0.50 < 0.60"):
        gate(results, 0.6)
