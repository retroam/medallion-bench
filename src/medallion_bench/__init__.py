"""MedallionBench: LLM ML Research Capability Evaluation Framework.

A modular, multi-round evaluation framework designed to assess LLMs as data scientists
competing in the Numerai tournament. Evaluates data exploration, model development,
risk management, and long-horizon coherence.
"""

from .medallion_bench import medallion_bench

__all__ = ["medallion_bench"]