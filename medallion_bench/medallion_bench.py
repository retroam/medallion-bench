"""MedallionBench main task definition."""

from inspect_ai import Task, task

from .dataset import numerai_dataset
from .scorer import medallion_scorer
from .solver import medallion_solver


@task
def medallion_bench(
    rounds: int = 10,
    phase: int = 1,
    seed: int = 42,
) -> Task:
    """MedallionBench evaluation task.
    
    A multi-round evaluation framework that assesses LLMs as data scientists
    competing in the Numerai tournament. Evaluates across multiple phases:
    - Phase 1-2: Data exploration & model development (rounds 1-20)
    - Phase 3: Research synthesis & documentation (rounds 21-25)
    - Phase 4: Long-horizon coherence & memory ablations (rounds 26-40)
    
    Args:
        rounds: Number of tournament rounds to simulate
        phase: Which phase of evaluation (1-4)
        seed: Random seed for reproducibility
    
    Returns:
        Task: The configured MedallionBench evaluation task
    """
    return Task(
        dataset=numerai_dataset(rounds=rounds, phase=phase, seed=seed),
        solver=medallion_solver(phase=phase),
        scorer=medallion_scorer(phase=phase),
        metadata={
            "rounds": rounds,
            "phase": phase,
            "seed": seed,
        },
    )