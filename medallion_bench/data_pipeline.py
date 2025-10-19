"""Historical Numerai data pipeline utilities for MedallionBench.

This module implements a lightweight data pipeline that mirrors the behaviour of the
official Numerai tournament downloads while remaining fully self contained for the
unit tests that ship with MedallionBench.  The implementation focuses on:

* Progressive disclosure of training/validation/tournament splits per round
* Deterministic synthetic data generation (to avoid >1GB downloads during tests)
* Transparent caching so repeated accesses are fast and side-effect free

The real benchmark can swap this implementation with one that pulls the actual
Numerai parquet files.  The public API is intentionally small so the replacement
only needs to honour :meth:`get_round_data` and :meth:`get_hidden_targets`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

try:  # pragma: no cover - optional dependency
    import numerapi  # type: ignore
except Exception:  # pragma: no cover - numerapi is optional for tests
    numerapi = None


_DEFAULT_FEATURES = [f"feature_{i:03d}" for i in range(10)]


@dataclass(frozen=True)
class RoundMetadata:
    """Metadata associated with a cached tournament round."""

    round: int
    training_eras: List[int]
    validation_eras: List[int]
    feature_columns: List[str]
    tournament_rows: int
    cache_path: Path


class NumeraiDataPipeline:
    """Handle historical data lookups for the simulated tournament.

    The implementation intentionally keeps a numerapi client around so that the
    production benchmark can upgrade the synthetic data with the real Numerai
    dataset.  For unit tests we fall back to synthetic data generation that is
    deterministic (seeded) and cached on disk.
    """

    def __init__(self, cache_dir: str | Path = "./numerai_cache", base_seed: int = 7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_seed = int(base_seed)
        self.numerapi_client = None

        if numerapi is not None:  # pragma: no cover - network path disabled in tests
            try:
                self.numerapi_client = numerapi.NumerAPI()
            except Exception:
                # The Numerai API is optional during testing; failures simply disable it.
                self.numerapi_client = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def get_round_data(self, round_num: int) -> Dict[str, Any]:
        """Return the data available to an agent for a specific round.

        Args:
            round_num: Tournament round identifier (must be >= 1).

        Returns:
            Dictionary with ``training``/``validation``/``tournament`` data frames
            and ``metadata`` describing the splits.
        """

        if round_num < 1:
            raise ValueError("round_num must be >= 1")

        cache_file = self._cache_file(round_num)

        if cache_file.exists():
            cached: Dict[str, Any] = pd.read_pickle(cache_file)
        else:
            cached = self._generate_round_payload(round_num)
            pd.to_pickle(cached, cache_file)

        # Return defensive copies so callers cannot mutate the cached payload.
        payload = cached["data"]
        return {
            "training": payload["training"].copy(deep=True),
            "validation": payload["validation"].copy(deep=True),
            "tournament": payload["tournament"].copy(deep=True),
            "metadata": payload["metadata"].copy(),
        }

    def get_hidden_targets(self, round_num: int) -> pd.DataFrame:
        """Return the hidden targets for the specified round.

        The returned DataFrame contains the ``id`` column matching the tournament
        frame plus the ``target`` that is kept secret from the agent.
        """

        cache_file = self._cache_file(round_num)
        if not cache_file.exists():
            # Generate data if it was never requested before.
            self.get_round_data(round_num)

        cached: Dict[str, Any] = pd.read_pickle(cache_file)
        hidden = cached["hidden_targets"]
        return hidden.copy(deep=True)

    def clear_cache(self) -> None:
        """Remove all cached round files."""

        for file in self.cache_dir.glob("round_*.pkl"):
            file.unlink()

    # ------------------------------------------------------------------
    # Synthetic data generation helpers
    # ------------------------------------------------------------------
    def _cache_file(self, round_num: int) -> Path:
        return self.cache_dir / f"round_{round_num}.pkl"

    def _generate_round_payload(self, round_num: int) -> Dict[str, Any]:
        rng = np.random.default_rng(self.base_seed + round_num)
        feature_columns = list(_DEFAULT_FEATURES)

        training_eras = list(range(max(1, round_num - 40), max(1, round_num - 3)))
        validation_eras = list(range(max(1, round_num - 3), round_num))

        training = self._build_frame(
            rng,
            training_eras,
            rows_per_era=20,
            feature_columns=feature_columns,
            include_target=True,
        )
        validation = self._build_frame(
            rng,
            validation_eras,
            rows_per_era=10,
            feature_columns=feature_columns,
            include_target=True,
        )
        tournament = self._build_frame(
            rng,
            eras=[round_num],
            rows_per_era=15,
            feature_columns=feature_columns,
            include_target=False,
        )

        hidden_targets = self._build_hidden_targets(rng, tournament)

        metadata = RoundMetadata(
            round=round_num,
            training_eras=training_eras,
            validation_eras=validation_eras,
            feature_columns=feature_columns,
            tournament_rows=len(tournament),
            cache_path=self._cache_file(round_num),
        )

        return {
            "data": {
                "training": training,
                "validation": validation,
                "tournament": tournament,
                "metadata": metadata.__dict__,
            },
            "hidden_targets": hidden_targets,
        }

    def _build_frame(
        self,
        rng: np.random.Generator,
        eras: Iterable[int],
        rows_per_era: int,
        feature_columns: List[str],
        include_target: bool,
    ) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for era in eras:
            for row_idx in range(rows_per_era):
                feature_values = rng.normal(loc=0, scale=1, size=len(feature_columns))
                row: Dict[str, Any] = {
                    "id": f"era{era}_row{row_idx}",
                    "era": era,
                }
                row.update(dict(zip(feature_columns, feature_values)))
                if include_target:
                    row["target"] = float(rng.uniform(0, 1))
                rows.append(row)

        if not rows:
            columns = ["id", "era", *feature_columns]
            if include_target:
                columns.append("target")
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(rows)

    def _build_hidden_targets(
        self, rng: np.random.Generator, tournament: pd.DataFrame
    ) -> pd.DataFrame:
        if tournament.empty:
            return pd.DataFrame(columns=["id", "target"])

        baseline = np.linspace(0.2, 0.8, len(tournament), endpoint=False)
        noise = rng.normal(loc=0, scale=0.01, size=len(tournament))
        targets = baseline + noise
        return pd.DataFrame(
            {
                "id": tournament["id"].to_list(),
                "target": targets,
            }
        )


__all__ = ["NumeraiDataPipeline", "RoundMetadata"]

