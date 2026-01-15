"""Unit tests for phase 2 failure mode simulators."""

from __future__ import annotations

import math

import numpy as np
import pytest

from medallion_bench.failure_modes import (
    BurnPeriodSimulator,
    FeatureDrift,
    RegimeManager,
)


def test_regime_manager_applies_multiplier_and_noise():
    schedule = [
        (200, 240, "neutral"),
        (241, 245, "bull_market"),
        (246, 248, "bear_market"),
        (249, 252, "regime_change"),
        (253, None, "neutral"),
    ]
    manager = RegimeManager(regime_schedule=schedule, seed=7)

    base_corr = 0.12
    round_num = 250

    expected_noise = float(np.random.default_rng(7 + round_num * 7919).normal(0.0, 0.08))
    expected = np.clip(base_corr * -0.5 + expected_noise, -1.0, 1.0)

    adjusted = manager.apply_regime_effects(base_corr, round_num)

    assert math.isclose(adjusted, expected, rel_tol=1e-9, abs_tol=1e-9)
    assert manager.current_regime(round_num).name == "regime_change"


@pytest.mark.parametrize(
    "round_num, base_corr, expected",
    [
        (211, 0.05, -0.02),
        (288, 0.05, -0.02),
        (211, 0.2, 0.12),
        (305, 0.05, 0.05),
    ],
)
def test_burn_period_simulator(round_num, base_corr, expected):
    simulator = BurnPeriodSimulator(severity=0.08, floor=-0.02)

    result = simulator.inject_burn(round_num, base_corr)
    assert result == pytest.approx(expected)


def test_feature_drift_neutralises_top_features():
    importances = {f"feature_{i:02d}": 1.0 - 0.02 * i for i in range(15)}
    drift = FeatureDrift({220: "neutralize_top_10_features"})

    adjusted = drift.apply_drift(220, importances)

    # Top features should be roughly equal to the baseline and ordering flattened.
    values = [adjusted[f"feature_{i:02d}"] for i in range(5)]
    assert max(values) - min(values) < 1e-9
    assert pytest.approx(sum(adjusted.values()), rel=1e-9) == sum(importances.values())


def test_feature_drift_inverts_importance_weights():
    importances = {"a": 0.6, "b": 0.3, "c": 0.1}
    drift = FeatureDrift({260: "inverse_importance_weights"})

    adjusted = drift.apply_drift(260, importances)

    assert adjusted["a"] < adjusted["b"] < adjusted["c"]
    assert pytest.approx(sum(adjusted.values()), rel=1e-9) == sum(importances.values())


def test_feature_drift_introduces_new_features():
    importances = {"a": 0.5, "b": 0.3, "c": 0.2}
    drift = FeatureDrift({300: "introduce_new_feature_set"})

    adjusted = drift.apply_drift(300, importances)

    new_features = {key: value for key, value in adjusted.items() if key.startswith("new_feature_")}
    assert new_features, "Expected new features to be introduced"
    assert len(new_features) == max(1, len(importances) // 5)
    assert pytest.approx(sum(adjusted.values()), rel=1e-9) == sum(importances.values())
