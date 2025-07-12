"""Numerai dataset handling for MedallionBench."""

from typing import Any, Dict, List

from inspect_ai.dataset import Dataset, Sample


def numerai_dataset(
    rounds: int = 10,
    phase: int = 1,
    seed: int = 42,
) -> Dataset:
    """Create Numerai tournament dataset for MedallionBench.
    
    Progressive disclosure based on phase:
    - Phase 1 (rounds 1-10): Basic training & validation sample
    - Phase 2 (rounds 11-20): Full training, validation, feature metadata
    - Phase 3 (rounds 21-25): Tournament-era data, meta-model info
    - Phase 4 (rounds 26-40): All historical tournaments & regime labels
    
    Args:
        rounds: Number of tournament rounds to simulate
        phase: Which phase determines data availability
        seed: Random seed for reproducibility
        
    Returns:
        List[Sample]: Configured dataset samples for the evaluation
    """
    samples: List[Sample] = []
    
    for round_num in range(1, rounds + 1):
        # Determine data availability based on phase
        data_config = _get_data_config(round_num, phase)
        
        sample = Sample(
            id=f"round_{round_num}",
            input=_create_round_prompt(round_num, data_config),
            target=_create_round_target(round_num),
            metadata={
                "round": round_num,
                "phase": phase,
                "data_config": data_config,
                "seed": seed,
            },
        )
        samples.append(sample)
    
    return Dataset(samples)


def _get_data_config(round_num: int, phase: int) -> Dict[str, Any]:
    """Determine what data is available for this round and phase."""
    config = {
        "training_data": False,
        "validation_data": False,
        "feature_metadata": False,
        "tournament_data": False,
        "meta_model_info": False,
        "historical_tournaments": False,
        "regime_labels": False,
    }
    
    # Phase 1: Basic data for rounds 1-10
    if phase >= 1 and round_num <= 10:
        config.update({
            "training_data": True,
            "validation_data": True,
        })
    
    # Phase 2: Full data for rounds 11-20
    if phase >= 2 and round_num <= 20:
        config.update({
            "training_data": True,
            "validation_data": True,
            "feature_metadata": True,
        })
    
    # Phase 3: Tournament data for rounds 21-25
    if phase >= 3 and round_num <= 25:
        config.update({
            "training_data": True,
            "validation_data": True,
            "feature_metadata": True,
            "tournament_data": True,
            "meta_model_info": True,
        })
    
    # Phase 4: All historical data for rounds 26-40
    if phase >= 4 and round_num <= 40:
        config.update({
            "training_data": True,
            "validation_data": True,
            "feature_metadata": True,
            "tournament_data": True,
            "meta_model_info": True,
            "historical_tournaments": True,
            "regime_labels": True,
        })
    
    return config


def _create_round_prompt(round_num: int, data_config: Dict[str, Any]) -> str:
    """Create the prompt for a tournament round."""
    prompt = f"""# Numerai Tournament Round {round_num}

You are competing in the Numerai tournament as a data scientist. Your goal is to:
1. Explore the available data
2. Develop and train predictive models
3. Manage your stake and risk
4. Submit predictions for evaluation

## Available Data
"""
    
    if data_config["training_data"]:
        prompt += "- Training dataset with features and targets\n"
    if data_config["validation_data"]:
        prompt += "- Validation dataset for model evaluation\n"
    if data_config["feature_metadata"]:
        prompt += "- Feature metadata and descriptions\n"
    if data_config["tournament_data"]:
        prompt += "- Tournament-era data for live predictions\n"
    if data_config["meta_model_info"]:
        prompt += "- Meta-model information and ensemble strategies\n"
    if data_config["historical_tournaments"]:
        prompt += "- Historical tournament results and performance data\n"
    if data_config["regime_labels"]:
        prompt += "- Regime labels for understanding market conditions\n"
    
    prompt += f"""
## Your Task
Analyze the data, develop models, and make strategic decisions for Round {round_num}.
Use the available tools to:
- Load and explore the Numerai data
- Develop predictive models
- Simulate submissions and manage risk
- Track your progress and learnings

Begin your analysis and model development now.
"""
    
    return prompt


def _create_round_target(round_num: int) -> str:
    """Create the target/expected output for a tournament round."""
    return f"Successfully complete Round {round_num} with data analysis, model development, and strategic decision-making."