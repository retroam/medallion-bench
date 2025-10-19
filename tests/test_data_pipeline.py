"""Tests for the NumeraiDataPipeline synthetic implementation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from medallion_bench.data_pipeline import NumeraiDataPipeline


def test_round_data_structure(tmp_path: Path) -> None:
    pipeline = NumeraiDataPipeline(cache_dir=tmp_path)
    round_data = pipeline.get_round_data(210)

    assert set(round_data) == {"training", "validation", "tournament", "metadata"}
    assert "target" in round_data["training"].columns
    assert "target" not in round_data["tournament"].columns

    hidden = pipeline.get_hidden_targets(210)
    merged = round_data["tournament"].merge(hidden, on="id", how="inner")
    assert len(merged) == len(round_data["tournament"])


def test_pipeline_caching_is_defensive(tmp_path: Path) -> None:
    pipeline = NumeraiDataPipeline(cache_dir=tmp_path)
    first = pipeline.get_round_data(215)

    # Mutate the returned frame; this should not leak into the cache
    first["tournament"].loc[:, "feature_000"] = 999

    second = pipeline.get_round_data(215)
    assert not (second["tournament"]["feature_000"] == 999).all()


def test_pipeline_seed_changes(tmp_path: Path) -> None:
    pipeline_a = NumeraiDataPipeline(cache_dir=tmp_path / "a", base_seed=1)
    pipeline_b = NumeraiDataPipeline(cache_dir=tmp_path / "b", base_seed=123)

    data_a = pipeline_a.get_round_data(205)
    data_b = pipeline_b.get_round_data(205)

    assert not data_a["training"].equals(data_b["training"])


def test_hidden_targets_empty_round(tmp_path: Path) -> None:
    pipeline = NumeraiDataPipeline(cache_dir=tmp_path)
    empty_round = pipeline.get_round_data(1)

    assert empty_round["training"].empty
    assert empty_round["validation"].empty

    hidden = pipeline.get_hidden_targets(1)
    assert isinstance(hidden, pd.DataFrame)
    assert list(hidden.columns) == ["id", "target"]
