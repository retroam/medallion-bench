"""MedallionBench scoring framework."""

from typing import Any, Dict, List, Optional

from inspect_ai.scorer import Score, Scorer, Target, scorer
from inspect_ai.model import ChatMessageAssistant

from .scoring import (
    BankrollScorer,
    CoherenceScorer,
    IterativeScorer,
    MethodologyScorer,
    TechnicalScorer,
    VarianceScorer,
)


@scorer(metrics=["technical", "methodology", "iterative", "bankroll", "coherence"])
def medallion_scorer(phase: int = 1) -> Scorer:
    """MedallionBench composite scorer.
    
    Combines multiple scoring dimensions based on evaluation phase:
    - Phase 1-2: Technical + Methodology + Iterative + Bankroll
    - Phase 3: Above + Research synthesis
    - Phase 4: Above + Coherence + Variance
    
    Args:
        phase: Which evaluation phase determines scoring components
        
    Returns:
        Scorer: Configured composite scorer
    """
    
    async def score(state, target: Target) -> Score:
        """Score a MedallionBench evaluation state."""
        scores = {}
        
        # Phase 1-2: Core scoring dimensions
        if phase >= 1:
            technical_scorer = TechnicalScorer()
            methodology_scorer = MethodologyScorer()
            iterative_scorer = IterativeScorer()
            bankroll_scorer = BankrollScorer()
            
            scores["technical"] = await technical_scorer.score(state, target)
            scores["methodology"] = await methodology_scorer.score(state, target)
            scores["iterative"] = await iterative_scorer.score(state, target)
            scores["bankroll"] = await bankroll_scorer.score(state, target)
        
        # Phase 4: Long-horizon coherence
        if phase >= 4:
            coherence_scorer = CoherenceScorer()
            variance_scorer = VarianceScorer()
            
            scores["coherence"] = await coherence_scorer.score(state, target)
            scores["variance"] = await variance_scorer.score(state, target)
        
        # Calculate composite score
        composite_score = _calculate_composite_score(scores, phase)
        
        return Score(
            value=composite_score,
            metadata={
                "phase": phase,
                "component_scores": scores,
                "round": state.metadata.get("round", 0),
            },
        )
    
    return score


def _calculate_composite_score(scores: Dict[str, Score], phase: int) -> float:
    """Calculate weighted composite score based on phase."""
    if phase <= 2:
        # Phase 1-2: Equal weighting of core dimensions
        weights = {
            "technical": 0.35,
            "methodology": 0.35,
            "iterative": 0.30,
        }
        bankroll_weight = 0.3  # Applied separately
        
        core_score = sum(
            scores[dim].value * weight
            for dim, weight in weights.items()
            if dim in scores
        )
        
        bankroll_score = scores.get("bankroll", Score(value=0.0)).value
        
        return 0.7 * core_score + 0.3 * bankroll_score
    
    elif phase == 3:
        # Phase 3: Add research synthesis weight
        weights = {
            "technical": 0.25,
            "methodology": 0.25,
            "iterative": 0.20,
            "bankroll": 0.30,
        }
        
        return sum(
            scores[dim].value * weight
            for dim, weight in weights.items()
            if dim in scores
        )
    
    elif phase >= 4:
        # Phase 4: Include coherence and variance
        weights = {
            "technical": 0.20,
            "methodology": 0.20,
            "iterative": 0.15,
            "bankroll": 0.25,
            "coherence": 0.15,
            "variance": 0.05,
        }
        
        return sum(
            scores[dim].value * weight
            for dim, weight in weights.items()
            if dim in scores
        )
    
    return 0.0