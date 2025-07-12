"""Tests for MedallionBench scoring components."""

import pytest
from inspect_ai.scorer import Score

from medallion_bench.scoring import (
    TechnicalScorer,
    MethodologyScorer,
    IterativeScorer,
    BankrollScorer,
    CoherenceScorer,
    VarianceScorer,
)


@pytest.fixture
def mock_state():
    """Create a mock evaluation state for testing."""
    class MockState:
        def __init__(self):
            self.metadata = {"round": 1}
    return MockState()


@pytest.fixture
def mock_target():
    """Create a mock target for testing."""
    return "test target"


@pytest.mark.asyncio
async def test_technical_scorer(mock_state, mock_target):
    """Test TechnicalScorer."""
    scorer = TechnicalScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "technical"
    assert "details" in score.metadata


@pytest.mark.asyncio
async def test_methodology_scorer(mock_state, mock_target):
    """Test MethodologyScorer."""
    scorer = MethodologyScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "methodology"
    assert "details" in score.metadata


@pytest.mark.asyncio
async def test_iterative_scorer(mock_state, mock_target):
    """Test IterativeScorer."""
    scorer = IterativeScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "iterative"
    assert "details" in score.metadata


@pytest.mark.asyncio
async def test_bankroll_scorer(mock_state, mock_target):
    """Test BankrollScorer."""
    scorer = BankrollScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "bankroll"
    assert "details" in score.metadata


@pytest.mark.asyncio
async def test_coherence_scorer(mock_state, mock_target):
    """Test CoherenceScorer."""
    scorer = CoherenceScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "coherence"
    assert "details" in score.metadata


@pytest.mark.asyncio
async def test_variance_scorer(mock_state, mock_target):
    """Test VarianceScorer."""
    scorer = VarianceScorer()
    score = await scorer.score(mock_state, mock_target)
    
    assert isinstance(score, Score)
    assert 0 <= score.value <= 1
    assert score.metadata["component"] == "variance"
    assert "details" in score.metadata