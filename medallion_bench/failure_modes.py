"""Failure mode simulations used in MedallionBench phase 2.

The real Numerai tournament is notorious for its regime shifts, burn periods,
and feature drift.  Phase 2 of the implementation guide calls for utilities
that can reproduce these conditions so that agents are stress-tested beyond
the happy-path scenarios covered in phase 1.  This module implements three
light-weight simulators:

* :class:`RegimeManager`   – applies correlation multipliers and volatility
* :class:`BurnPeriodSimulator` – injects prolonged negative performance
* :class:`FeatureDrift`    – rewrites feature-importance maps over time

The focus is determinism: every helper is seeded so that tests and scripted
evaluations remain reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, MutableMapping, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class Regime:
    """Metadata that describes a specific market regime."""

    name: str
    corr_multiplier: float
    volatility: float


class RegimeManager:
    """Simulate Numerai-style market regime changes.

    Parameters
    ----------
    regime_schedule:
        Optional list describing which regime applies to which rounds.  Each
        entry is a tuple ``(start_round, end_round, regime_name)`` where
        ``end_round`` may be ``None`` to mark an open-ended regime.
    seed:
        Seed used to produce deterministic volatility noise.  The noise is
        derived from ``round_num`` which means each round has the same
        adjustment regardless of the order in which it is queried.
    """

    _DEFAULT_REGIMES: Dict[str, Regime] = {
        "bull_market": Regime("bull_market", corr_multiplier=1.2, volatility=0.02),
        "bear_market": Regime("bear_market", corr_multiplier=0.8, volatility=0.04),
        "regime_change": Regime(
            "regime_change", corr_multiplier=-0.5, volatility=0.08
        ),
        "neutral": Regime("neutral", corr_multiplier=1.0, volatility=0.03),
    }

    _DEFAULT_SCHEDULE: List[Tuple[int, Optional[int], str]] = [
        (200, 239, "bull_market"),
        (240, 249, "neutral"),
        (250, 252, "regime_change"),
        (253, 279, "bear_market"),
        (280, None, "neutral"),
    ]

    def __init__(
        self,
        regime_schedule: Optional[Iterable[Tuple[int, Optional[int], str]]] = None,
        seed: int = 42,
    ) -> None:
        self.regimes = dict(self._DEFAULT_REGIMES)
        self.regime_schedule = (
            list(regime_schedule) if regime_schedule is not None else list(self._DEFAULT_SCHEDULE)
        )
        if not self.regime_schedule:
            raise ValueError("regime_schedule must contain at least one regime span")

        for _, _, name in self.regime_schedule:
            if name not in self.regimes:
                raise ValueError(f"Unknown regime '{name}' in schedule")

        self.seed = int(seed)

    # ------------------------------------------------------------------
    def current_regime(self, round_num: int) -> Regime:
        """Return the :class:`Regime` active for ``round_num``."""

        for start, end, name in self.regime_schedule:
            if round_num < start:
                continue
            if end is None or round_num <= end:
                return self.regimes[name]
        # Fallback to the last regime if the round exceeds all entries.
        _, _, name = self.regime_schedule[-1]
        return self.regimes[name]

    # ------------------------------------------------------------------
    def apply_regime_effects(self, base_correlation: float, round_num: int) -> float:
        """Apply the active regime multiplier and volatility noise.

        The resulting correlation is clipped to ``[-1.0, 1.0]`` so that
        downstream consumers cannot accidentally receive impossible values.
        """

        regime = self.current_regime(round_num)
        multiplier = regime.corr_multiplier
        volatility = regime.volatility

        rng = np.random.default_rng(self.seed + round_num * 7919)
        noise = float(rng.normal(0.0, volatility))

        adjusted = base_correlation * multiplier + noise
        return float(np.clip(adjusted, -1.0, 1.0))


class BurnPeriodSimulator:
    """Inject prolonged draw-downs that mimic Numerai burn periods."""

    def __init__(
        self,
        burn_periods: Optional[Iterable[Tuple[int, int]]] = None,
        severity: float = 0.08,
        floor: float = -0.02,
    ) -> None:
        self.burn_periods = (
            list(burn_periods)
            if burn_periods is not None
            else [(210, 215), (287, 294)]
        )
        self.severity = float(severity)
        self.floor = float(floor)

    # ------------------------------------------------------------------
    def inject_burn(self, round_num: int, base_correlation: float) -> float:
        """Return a correlation adjusted for burn periods."""

        for start, end in self.burn_periods:
            if start <= round_num <= end:
                reduced = base_correlation - self.severity
                return float(max(reduced, self.floor))
        return float(base_correlation)


class FeatureDrift:
    """Simulate evolving feature importance throughout the tournament."""

    def __init__(
        self,
        drift_schedule: Optional[Dict[int, str]] = None,
    ) -> None:
        self.drift_schedule = (
            dict(drift_schedule)
            if drift_schedule is not None
            else {
                220: "neutralize_top_10_features",
                260: "inverse_importance_weights",
                300: "introduce_new_feature_set",
            }
        )

    # ------------------------------------------------------------------
    def apply_drift(self, round_num: int, feature_importances: Dict[str, float]) -> Dict[str, float]:
        """Apply the configured drift for ``round_num`` if scheduled."""

        if round_num not in self.drift_schedule:
            return dict(feature_importances)

        drift_type = self.drift_schedule[round_num]
        return self.apply_drift_type(feature_importances, drift_type)

    # ------------------------------------------------------------------
    def apply_drift_type(
        self,
        feature_importances: Dict[str, float],
        drift_type: str,
    ) -> Dict[str, float]:
        """Apply one of the supported drift transformations."""

        if not feature_importances:
            return {}

        if drift_type == "neutralize_top_10_features":
            return self._neutralize_top_features(feature_importances)
        if drift_type == "inverse_importance_weights":
            return self._invert_importances(feature_importances)
        if drift_type == "introduce_new_feature_set":
            return self._introduce_new_features(feature_importances)

        raise ValueError(f"Unsupported drift type '{drift_type}'")

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(weights: MutableMapping[str, float], target_sum: float) -> Dict[str, float]:
        total = float(sum(weights.values()))
        if total == 0:
            return {key: 0.0 for key in weights}
        scale = target_sum / total
        return {key: value * scale for key, value in weights.items()}

    # ------------------------------------------------------------------
    def _neutralize_top_features(self, feature_importances: Dict[str, float]) -> Dict[str, float]:
        total = float(sum(feature_importances.values()))
        sorted_features = sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)
        top_n = min(10, len(sorted_features))
        if top_n == 0:
            return dict(feature_importances)

        neutralized = dict(feature_importances)
        remaining_values = [value for _, value in sorted_features[top_n:]]
        baseline = float(np.mean(remaining_values)) if remaining_values else float(total / len(sorted_features))

        for feature, _ in sorted_features[:top_n]:
            neutralized[feature] = baseline

        return self._normalize(neutralized, total)

    # ------------------------------------------------------------------
    def _invert_importances(self, feature_importances: Dict[str, float]) -> Dict[str, float]:
        total = float(sum(feature_importances.values()))
        sorted_features = sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)
        n = len(sorted_features)
        if n <= 1:
            return dict(feature_importances)

        raw_scores = {feature: float(index + 1) for index, (feature, _) in enumerate(sorted_features)}
        return self._normalize(raw_scores, total)

    # ------------------------------------------------------------------
    def _introduce_new_features(self, feature_importances: Dict[str, float]) -> Dict[str, float]:
        total = float(sum(feature_importances.values()))
        if not feature_importances:
            return {}

        updated = {key: value * 0.75 for key, value in feature_importances.items()}
        new_total = total - sum(updated.values())
        if new_total <= 0:
            # Nothing left for new features; fall back to normalization.
            return self._normalize(updated, total)

        new_feature_count = max(1, len(feature_importances) // 5)
        share = new_total / new_feature_count

        next_index = 0
        while len(updated) < len(feature_importances) + new_feature_count:
            candidate = f"new_feature_{next_index:02d}"
            if candidate not in updated:
                updated[candidate] = share
            next_index += 1

        return self._normalize(updated, total)


__all__ = [
    "RegimeManager",
    "BurnPeriodSimulator",
    "FeatureDrift",
]

