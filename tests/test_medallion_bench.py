"""Basic tests for MedallionBench task definition."""

import pytest
from inspect_ai import Task

from medallion_bench import medallion_bench


def test_medallion_bench_task_creation():
    """Test that MedallionBench task can be created."""
    task = medallion_bench()
    assert isinstance(task, Task)
    assert task.metadata["phase"] == 1
    assert task.metadata["rounds"] == 10
    assert task.metadata["seed"] == 42


def test_medallion_bench_different_phases():
    """Test MedallionBench with different phases."""
    for phase in [1, 2, 3, 4]:
        task = medallion_bench(phase=phase)
        assert task.metadata["phase"] == phase


def test_medallion_bench_different_rounds():
    """Test MedallionBench with different round counts."""
    for rounds in [5, 10, 20, 40]:
        task = medallion_bench(rounds=rounds)
        assert task.metadata["rounds"] == rounds


def test_medallion_bench_custom_seed():
    """Test MedallionBench with custom seed."""
    task = medallion_bench(seed=123)
    assert task.metadata["seed"] == 123