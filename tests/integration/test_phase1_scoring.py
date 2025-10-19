#!/usr/bin/env python3
"""Test Phase 1 scoring system."""

import asyncio
from inspect_ai.model import ChatMessageUser, ChatMessageAssistant
from inspect_ai.scorer import Target

from medallion_bench.scoring import (
    TechnicalScorer,
    MethodologyScorer,
    IterativeScorer,
    BankrollScorer,
    CoherenceScorer,
    VarianceScorer
)


class MockState:
    """Mock evaluation state for testing scorers."""

    def __init__(self, output_text):
        self.output = MockOutput(output_text)
        self.metadata = {"round": 1}


class MockOutput:
    """Mock output object."""

    def __init__(self, completion_text):
        self.completion = completion_text


async def main():
    """Test all scorers."""
    print("=" * 60)
    print("Phase 1 Scoring System Test")
    print("=" * 60)

    # Create mock state with typical agent output
    mock_output = """
    I'll start by loading and exploring the Numerai tournament data.

    First, let me load the training dataset to understand the features and targets.
    I'll then train an XGBoost model using the top features identified in my EDA.

    After training, I'll evaluate the model performance on the validation set.
    The model should be trained with proper cross-validation to avoid overfitting.

    Once I have a validated model, I'll make predictions on the tournament data.
    """

    state = MockState(mock_output)
    target = Target("Complete the tournament round successfully")

    print("\n" + "=" * 60)
    print("Scorer Results")
    print("=" * 60)

    # Test Technical Scorer
    print("\n1. Technical Scorer")
    technical_scorer = TechnicalScorer()
    technical_score = await technical_scorer.score(state, target)
    print(f"   Score: {technical_score.value:.2f}")
    print(f"   Details: {technical_score.metadata['details']}")

    # Test Methodology Scorer
    print("\n2. Methodology Scorer")
    methodology_scorer = MethodologyScorer()
    methodology_score = await methodology_scorer.score(state, target)
    print(f"   Score: {methodology_score.value:.2f}")
    print(f"   Details: {methodology_score.metadata['details']}")

    # Test Iterative Scorer
    print("\n3. Iterative Scorer")
    iterative_scorer = IterativeScorer()
    iterative_score = await iterative_scorer.score(state, target)
    print(f"   Score: {iterative_score.value:.2f}")
    print(f"   Details: {iterative_score.metadata['details']}")

    # Test Bankroll Scorer
    print("\n4. Bankroll Scorer")
    bankroll_scorer = BankrollScorer()
    bankroll_score = await bankroll_scorer.score(state, target)
    print(f"   Score: {bankroll_score.value:.2f}")
    print(f"   Details: {bankroll_score.metadata['details']}")

    # Test Coherence Scorer (Phase 4)
    print("\n5. Coherence Scorer")
    coherence_scorer = CoherenceScorer()
    coherence_score = await coherence_scorer.score(state, target)
    print(f"   Score: {coherence_score.value:.2f}")
    print(f"   Details: {coherence_score.metadata['details']}")

    # Test Variance Scorer (Phase 4)
    print("\n6. Variance Scorer")
    variance_scorer = VarianceScorer()
    variance_score = await variance_scorer.score(state, target)
    print(f"   Score: {variance_score.value:.2f}")
    print(f"   Details: {variance_score.metadata['details']}")

    # Calculate composite score (Phase 1 weighting)
    print("\n" + "=" * 60)
    print("Composite Score Calculation (Phase 1 Weights)")
    print("=" * 60)

    weights = {
        "technical": 0.35,
        "methodology": 0.35,
        "iterative": 0.30,
    }
    bankroll_weight = 0.3

    core_score = (
        technical_score.value * weights["technical"] +
        methodology_score.value * weights["methodology"] +
        iterative_score.value * weights["iterative"]
    )

    composite = 0.7 * core_score + 0.3 * bankroll_score.value

    print(f"\nCore dimensions (70%):")
    print(f"  Technical ({weights['technical']*100:.0f}%): {technical_score.value:.2f}")
    print(f"  Methodology ({weights['methodology']*100:.0f}%): {methodology_score.value:.2f}")
    print(f"  Iterative ({weights['iterative']*100:.0f}%): {iterative_score.value:.2f}")
    print(f"  → Core score: {core_score:.2f}")

    print(f"\nBankroll (30%): {bankroll_score.value:.2f}")

    print(f"\n{'='*60}")
    print(f"Final Composite Score: {composite:.2f}")
    print(f"{'='*60}")

    print("\n" + "=" * 60)
    print("✓ Phase 1 scoring test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
