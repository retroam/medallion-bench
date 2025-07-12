"""Tests for MedallionBench dataset functionality."""

import pytest
from inspect_ai.dataset import Dataset

from medallion_bench.dataset import numerai_dataset, _get_data_config


def test_numerai_dataset_creation():
    """Test that Numerai dataset can be created."""
    dataset = numerai_dataset()
    assert isinstance(dataset, Dataset)
    assert len(dataset.samples) == 10  # default rounds


def test_numerai_dataset_different_rounds():
    """Test Numerai dataset with different round counts."""
    for rounds in [5, 15, 25]:
        dataset = numerai_dataset(rounds=rounds)
        assert len(dataset.samples) == rounds


def test_numerai_dataset_different_phases():
    """Test Numerai dataset with different phases."""
    for phase in [1, 2, 3, 4]:
        dataset = numerai_dataset(phase=phase)
        assert all(sample.metadata["phase"] == phase for sample in dataset.samples)


def test_data_config_phase_1():
    """Test data configuration for Phase 1."""
    config = _get_data_config(round_num=5, phase=1)
    assert config["training_data"] is True
    assert config["validation_data"] is True
    assert config["feature_metadata"] is False
    assert config["tournament_data"] is False


def test_data_config_phase_2():
    """Test data configuration for Phase 2."""
    config = _get_data_config(round_num=15, phase=2)
    assert config["training_data"] is True
    assert config["validation_data"] is True
    assert config["feature_metadata"] is True
    assert config["tournament_data"] is False


def test_data_config_phase_3():
    """Test data configuration for Phase 3."""
    config = _get_data_config(round_num=23, phase=3)
    assert config["training_data"] is True
    assert config["validation_data"] is True
    assert config["feature_metadata"] is True
    assert config["tournament_data"] is True
    assert config["meta_model_info"] is True


def test_data_config_phase_4():
    """Test data configuration for Phase 4."""
    config = _get_data_config(round_num=30, phase=4)
    assert config["training_data"] is True
    assert config["validation_data"] is True
    assert config["feature_metadata"] is True
    assert config["tournament_data"] is True
    assert config["meta_model_info"] is True
    assert config["historical_tournaments"] is True
    assert config["regime_labels"] is True


def test_sample_metadata():
    """Test that dataset samples have correct metadata."""
    dataset = numerai_dataset(rounds=3, phase=2, seed=123)
    
    for i, sample in enumerate(dataset.samples):
        assert sample.metadata["round"] == i + 1
        assert sample.metadata["phase"] == 2
        assert sample.metadata["seed"] == 123
        assert "data_config" in sample.metadata