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

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import warnings

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
    mode: str = "synthetic"


class NumeraiDataUnavailable(RuntimeError):
    """Raised when Numerai datasets cannot be accessed locally."""


class NumeraiDataPipeline:
    """Handle historical data lookups for the simulated tournament.

    The implementation intentionally keeps a numerapi client around so that the
    production benchmark can upgrade the synthetic data with the real Numerai
    dataset.  For unit tests we fall back to synthetic data generation that is
    deterministic (seeded) and cached on disk.  The ``data_mode`` parameter
    controls whether the pipeline prefers synthetic data, real Numerai downloads,
    or automatically picks the best available option.
    """

    def __init__(
        self,
        cache_dir: str | Path = "./numerai_cache",
        base_seed: int = 7,
        data_mode: str = "auto",
        allow_synthetic_fallback: bool = True,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.round_cache_dir = self.cache_dir / "rounds"
        self.round_cache_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_cache_dir = self.cache_dir / "datasets"
        self.dataset_cache_dir.mkdir(parents=True, exist_ok=True)

        self.base_seed = int(base_seed)
        self.numerapi_client: Optional["numerapi.NumerAPI"] = None

        self.data_mode = data_mode.lower()
        if self.data_mode not in {"auto", "synthetic", "numerai"}:
            raise ValueError("data_mode must be 'auto', 'synthetic', or 'numerai'")
        self.allow_synthetic_fallback = bool(allow_synthetic_fallback)

        self._round_mode: Dict[int, str] = {}
        self._historical_data: Optional[pd.DataFrame] = None
        self._feature_columns_real: Optional[List[str]] = None
        self._target_column: Optional[str] = None
        self._available_eras: List[int] = []
        self._real_data_available: Optional[bool] = None

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

        payload, mode_used = self._load_round_payload(round_num, self._preferred_mode())
        self._round_mode[round_num] = mode_used
        data_payload = payload["data"]
        return {
            "training": data_payload["training"].copy(deep=True),
            "validation": data_payload["validation"].copy(deep=True),
            "tournament": data_payload["tournament"].copy(deep=True),
            "metadata": data_payload["metadata"].copy(),
        }

    def get_hidden_targets(self, round_num: int) -> pd.DataFrame:
        """Return the hidden targets for the specified round.

        The returned DataFrame contains the ``id`` column matching the tournament
        frame plus the ``target`` that is kept secret from the agent.
        """

        mode = self._round_mode.get(round_num)
        if mode is None:
            payload, mode = self._load_round_payload(round_num, self._preferred_mode())
            self._round_mode[round_num] = mode
        else:
            cache_file = self._cache_file(mode, round_num)
            if cache_file.exists():
                payload: Dict[str, Any] = pd.read_pickle(cache_file)
            else:
                payload, mode = self._load_round_payload(round_num, mode)
                self._round_mode[round_num] = mode

        hidden = payload["hidden_targets"]
        return hidden.copy(deep=True)

    def clear_cache(self) -> None:
        """Remove all cached round files."""

        for file in self.round_cache_dir.rglob("round_*.pkl"):
            file.unlink()
        self._round_mode.clear()
        self._real_data_available = None

    # ------------------------------------------------------------------
    # Mode selection and real-data handling helpers
    # ------------------------------------------------------------------
    def _preferred_mode(self) -> str:
        if self.data_mode == "auto":
            if self.numerapi_client is None:
                return "synthetic"
            if self._real_data_available is False and self.allow_synthetic_fallback:
                return "synthetic"
            return "numerai"
        return self.data_mode

    def _load_round_payload(
        self, round_num: int, mode: str
    ) -> Tuple[Dict[str, Any], str]:
        """Load cached round payload or generate it for the requested mode."""

        if mode not in {"synthetic", "numerai"}:
            raise ValueError(f"Unsupported data mode '{mode}'")

        if mode == "numerai" and self._real_data_available is False:
            if self.allow_synthetic_fallback and self.data_mode != "numerai":
                return self._load_round_payload(round_num, "synthetic")
            raise NumeraiDataUnavailable("Real Numerai data is marked unavailable")

        cache_file = self._cache_file(mode, round_num)
        if cache_file.exists():
            cached: Dict[str, Any] = pd.read_pickle(cache_file)
            return cached, mode

        try:
            if mode == "numerai":
                payload = self._build_real_round_payload(round_num, mode)
            else:
                payload = self._generate_round_payload(round_num, mode)
        except NumeraiDataUnavailable as exc:
            self._real_data_available = False
            if mode == "numerai" and self.allow_synthetic_fallback and self.data_mode != "numerai":
                warnings.warn(
                    "Falling back to synthetic Numerai data because real downloads failed: "
                    f"{exc}",
                    RuntimeWarning,
                    stacklevel=3,
                )
                return self._load_round_payload(round_num, "synthetic")
            raise
        else:
            if mode == "numerai":
                self._real_data_available = True

        pd.to_pickle(payload, cache_file)
        return payload, mode

    def _build_real_round_payload(self, round_num: int, mode: str) -> Dict[str, Any]:
        """Construct round payloads using real Numerai datasets."""

        self._ensure_real_data_ready()
        if self._historical_data is None or not self._available_eras:
            raise NumeraiDataUnavailable("Numerai datasets are not loaded")

        training_cutoff = round_num - 4
        training_eras = [era for era in self._available_eras if era <= training_cutoff]
        validation_eras = [
            era for era in self._available_eras if training_cutoff < era < round_num
        ]

        if not training_eras:
            raise NumeraiDataUnavailable(
                f"Insufficient historical data to prepare training split for round {round_num}"
            )

        tournaments = self._historical_data[self._historical_data["era_int"] == round_num]
        if tournaments.empty:
            raise NumeraiDataUnavailable(
                f"No Numerai tournament data available for round {round_num}"
            )

        training_df = self._historical_data[
            self._historical_data["era_int"].isin(training_eras)
        ]
        validation_df = self._historical_data[
            self._historical_data["era_int"].isin(validation_eras)
        ]

        target_column = self._target_column
        if not target_column:
            raise NumeraiDataUnavailable("Target column could not be determined")

        # Prepare hidden targets before stripping them from tournament data.
        hidden_targets = tournaments[["id", target_column]].copy()
        if target_column != "target":
            hidden_targets = hidden_targets.rename(columns={target_column: "target"})

        training_ready = training_df.drop(columns=["era_int"]).copy()
        validation_ready = validation_df.drop(columns=["era_int"]).copy()
        tournament_ready = tournaments.drop(columns=["era_int"]).copy()

        # Remove all target-style columns from tournament data so the agent cannot see them.
        target_like_columns = [
            column for column in tournament_ready.columns if column.startswith("target")
        ]
        for column in target_like_columns:
            if column in tournament_ready.columns:
                tournament_ready.drop(columns=[column], inplace=True)

        metadata = RoundMetadata(
            round=round_num,
            training_eras=training_eras,
            validation_eras=validation_eras,
            feature_columns=self._feature_columns_real or list(_DEFAULT_FEATURES),
            tournament_rows=len(tournament_ready),
            cache_path=self._cache_file(mode, round_num),
            mode=mode,
        )

        return {
            "data": {
                "training": training_ready.reset_index(drop=True),
                "validation": validation_ready.reset_index(drop=True),
                "tournament": tournament_ready.reset_index(drop=True),
                "metadata": asdict(metadata),
            },
            "hidden_targets": hidden_targets.reset_index(drop=True),
        }

    def _ensure_real_data_ready(self) -> None:
        """Lazy-load Numerai datasets and normalise their schema."""

        if self._historical_data is not None:
            return

        if self.numerapi_client is None:
            raise NumeraiDataUnavailable("numerapi library is unavailable")

        try:
            train_path = self._download_dataset_if_needed("v4/train.parquet")
            validation_path = self._download_dataset_if_needed("v4/validation.parquet")
            train_df = self._normalise_numerai_frame(pd.read_parquet(train_path))
            validation_df = self._normalise_numerai_frame(pd.read_parquet(validation_path))
        except Exception as exc:  # pragma: no cover - network path not exercised in tests
            raise NumeraiDataUnavailable(
                "Unable to download or load Numerai parquet datasets"
            ) from exc

        historical = pd.concat([train_df, validation_df], ignore_index=True)
        if "era_int" not in historical.columns:
            raise NumeraiDataUnavailable("Numerai datasets are missing 'era' annotations")

        self._feature_columns_real = [
            column for column in historical.columns if column.startswith("feature_")
        ]
        if not self._feature_columns_real:
            raise NumeraiDataUnavailable("No feature columns detected in Numerai datasets")

        self._available_eras = sorted(int(era) for era in historical["era_int"].unique())
        if not self._available_eras:
            raise NumeraiDataUnavailable("No eras found in Numerai datasets")

        if "target" not in historical.columns:
            target_candidates = [
                column for column in historical.columns if column.startswith("target")
            ]
            if not target_candidates:
                raise NumeraiDataUnavailable("Target columns missing from Numerai datasets")
            canonical_target = target_candidates[0]
            historical = historical.rename(columns={canonical_target: "target"})

        self._target_column = "target"
        self._historical_data = historical

    def _download_dataset_if_needed(self, dataset_name: str) -> Path:
        """Download a Numerai dataset if it does not already exist locally."""

        target_path = self.dataset_cache_dir / dataset_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            return target_path

        if self.numerapi_client is None:
            raise NumeraiDataUnavailable("numerapi client is not initialised")

        self.numerapi_client.download_dataset(dataset_name, str(target_path))
        return target_path

    def _normalise_numerai_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent column naming for Numerai datasets."""

        normalised = frame.copy()
        if "id" not in normalised.columns:
            id_candidates = [col for col in ("row_id", "id") if col in normalised.columns]
            if not id_candidates:
                raise NumeraiDataUnavailable("Unable to identify row id column")
            normalised = normalised.rename(columns={id_candidates[0]: "id"})

        if "era" not in normalised.columns:
            raise NumeraiDataUnavailable("Dataset missing 'era' column")

        normalised["era_int"] = normalised["era"].apply(self._era_to_int)
        normalised = normalised.dropna(subset=["era_int"])
        normalised["era_int"] = normalised["era_int"].astype(int)
        return normalised

    @staticmethod
    def _era_to_int(value: Any) -> Optional[int]:
        """Convert Numerai era identifiers to integer form."""

        if isinstance(value, (int, np.integer)):
            return int(value)

        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            if digits:
                return int(digits)
        return None

    # ------------------------------------------------------------------
    # Synthetic data generation helpers
    # ------------------------------------------------------------------
    def _cache_file(self, mode: str, round_num: int) -> Path:
        mode_dir = self.round_cache_dir / mode
        mode_dir.mkdir(parents=True, exist_ok=True)
        return mode_dir / f"round_{round_num}.pkl"

    def _generate_round_payload(self, round_num: int, mode: str) -> Dict[str, Any]:
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
            cache_path=self._cache_file(mode, round_num),
            mode=mode,
        )

        return {
            "data": {
                "training": training,
                "validation": validation,
                "tournament": tournament,
                "metadata": asdict(metadata),
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
