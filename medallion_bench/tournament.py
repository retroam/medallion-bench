"""Simulated Numerai tournament environment for MedallionBench."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import pandas as pd

from .data_pipeline import NumeraiDataPipeline


@dataclass
class StakeDecision:
    """Decision returned by an agent when staking NMR."""

    amount: float
    confidence: float = 0.5
    corr_weight: Optional[float] = None
    mmc_weight: Optional[float] = None

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


class NumeraiAgent:
    """Base interface for Numerai tournament agents."""

    async def generate_predictions(self, round_data: Dict[str, Any]) -> pd.DataFrame:  # pragma: no cover - interface
        raise NotImplementedError

    async def decide_stake(self, context: Dict[str, Any]) -> StakeDecision:  # pragma: no cover - interface
        raise NotImplementedError


class SimulatedNumeraiTournament:
    """Simulate Numerai's tournament mechanics with historical delay."""

    def __init__(
        self,
        data_pipeline: Optional[NumeraiDataPipeline] = None,
        start_round: int = 200,
        corr_weight: float = 1.0,
        mmc_weight: float = 0.0,
        initial_balance: float = 100.0,
    ) -> None:
        self.data_pipeline = data_pipeline or NumeraiDataPipeline()
        self.current_round = start_round
        self.agent_balance = float(initial_balance)
        self.pending_rounds: List[Dict[str, Any]] = []
        self.resolved_rounds: List[Dict[str, Any]] = []
        self.corr_weight = corr_weight
        self.mmc_weight = mmc_weight

    # ------------------------------------------------------------------
    async def run_round(self, agent: NumeraiAgent) -> Dict[str, Any]:
        """Execute a tournament round with the supplied agent."""

        round_data = self.data_pipeline.get_round_data(self.current_round)

        predictions = await agent.generate_predictions(round_data)
        if not {"id", "prediction"}.issubset(predictions.columns):
            raise ValueError("Predictions must contain 'id' and 'prediction' columns")

        stake_decision = await agent.decide_stake(self.get_agent_context())
        corr_weight = (
            stake_decision.corr_weight
            if stake_decision.corr_weight is not None
            else self.corr_weight
        )
        mmc_weight = (
            stake_decision.mmc_weight
            if stake_decision.mmc_weight is not None
            else self.mmc_weight
        )

        targets = self.get_hidden_targets(self.current_round)
        correlation = self.calculate_correlation(predictions, targets)

        corr_weight = float(corr_weight)
        mmc_weight = float(mmc_weight)

        pending_entry = {
            "round": self.current_round,
            "stake": float(max(0.0, stake_decision.amount)),
            "correlation": correlation,
            "corr_weight": corr_weight,
            "mmc_weight": mmc_weight,
            "mmc": 0.0,
            "resolves_at": self.current_round + 20,
        }
        self.pending_rounds.append(pending_entry)

        self.process_resolutions()

        status = "ACTIVE"
        if self.agent_balance <= 0:
            status = "BANKRUPTCY"

        result = {
            "round": self.current_round,
            "correlation": correlation,
            "stake_decision": stake_decision.as_dict(),
            "status": status,
            "balance": self.agent_balance,
            "pending": len(self.pending_rounds),
        }

        self.current_round += 1
        return result

    # ------------------------------------------------------------------
    def get_agent_context(self) -> Dict[str, Any]:
        """Return context provided to the agent for staking decisions."""

        return {
            "balance": self.agent_balance,
            "current_round": self.current_round,
            "pending_rounds": [entry.copy() for entry in self.pending_rounds],
            "recent_results": self.resolved_rounds[-5:],
        }

    def get_hidden_targets(self, round_num: int) -> pd.DataFrame:
        return self.data_pipeline.get_hidden_targets(round_num)

    # ------------------------------------------------------------------
    def process_resolutions(self) -> None:
        """Resolve pending rounds whose resolution date has passed."""

        still_pending: List[Dict[str, Any]] = []
        for entry in self.pending_rounds:
            if entry["resolves_at"] <= self.current_round:
                payout = entry["stake"] * (
                    entry["corr_weight"] * entry["correlation"]
                    + entry["mmc_weight"] * entry.get("mmc", 0.0)
                )
                self.agent_balance += payout
                resolved_entry = entry.copy()
                resolved_entry.update({
                    "payout": payout,
                    "resolved_at": self.current_round,
                    "balance_after": self.agent_balance,
                })
                self.resolved_rounds.append(resolved_entry)
            else:
                still_pending.append(entry)

        self.pending_rounds = still_pending

    # ------------------------------------------------------------------
    @staticmethod
    def calculate_correlation(
        predictions: pd.DataFrame, targets: pd.DataFrame
    ) -> float:
        """Compute Numerai-style Spearman correlation on ranked predictions."""

        if predictions.empty or targets.empty:
            return 0.0

        merged = predictions.merge(targets, on="id", how="inner", suffixes=("", "_target"))
        if merged.empty:
            return 0.0

        pred_rank = merged["prediction"].rank(pct=True, method="average")
        target_rank = merged["target"].rank(pct=True, method="average")
        corr = pred_rank.corr(target_rank)
        return float(corr) if not pd.isna(corr) else 0.0


def run_round_sync(tournament: SimulatedNumeraiTournament, agent: NumeraiAgent) -> Dict[str, Any]:
    """Synchronous helper for environments without an event loop."""

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(tournament.run_round(agent))
    else:  # pragma: no cover - sync helper during interactive usage
        return loop.run_until_complete(tournament.run_round(agent))


__all__ = [
    "StakeDecision",
    "NumeraiAgent",
    "SimulatedNumeraiTournament",
    "run_round_sync",
]

