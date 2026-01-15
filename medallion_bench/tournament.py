"""Simulated Numerai tournament environment for MedallionBench."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import pandas as pd

from .data_pipeline import NumeraiDataPipeline
from .failure_modes import RegimeManager, BurnPeriodSimulator, FeatureDrift


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
        enable_failure_modes: bool = False,
        failure_mode_seed: int = 42,
    ) -> None:
        self.data_pipeline = data_pipeline or NumeraiDataPipeline()
        self.current_round = start_round
        self.agent_balance = float(initial_balance)
        self.pending_rounds: List[Dict[str, Any]] = []
        self.resolved_rounds: List[Dict[str, Any]] = []
        self.corr_weight = corr_weight
        self.mmc_weight = mmc_weight
        
        # Phase 2: Failure mode components
        self.enable_failure_modes = enable_failure_modes
        if enable_failure_modes:
            self.regime_manager = RegimeManager(seed=failure_mode_seed)
            self.burn_simulator = BurnPeriodSimulator()
            self.feature_drift = FeatureDrift()
            self.failure_history: List[Dict[str, Any]] = []

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
        base_correlation = self.calculate_correlation(predictions, targets)
        
        # Phase 2: Apply failure modes if enabled
        correlation = base_correlation
        failure_info = {}
        if self.enable_failure_modes:
            # Apply regime effects
            correlation = self.regime_manager.apply_regime_effects(correlation, self.current_round)
            
            # Apply burn period effects
            correlation = self.burn_simulator.inject_burn(self.current_round, correlation)
            
            # Track failure mode application
            failure_info = {
                'base_correlation': base_correlation,
                'modified_correlation': correlation,
                'regime_info': self.regime_manager.current_regime(self.current_round).name,
                'burn_applied': self.burn_simulator.inject_burn(self.current_round, 0.0) != 0.0,
            }
            self.failure_history.append({
                'round': self.current_round,
                **failure_info
            })

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
        
        # Add failure mode information if enabled
        if self.enable_failure_modes and failure_info:
            result["failure_modes"] = failure_info

        self.current_round += 1
        return result

    # ------------------------------------------------------------------
    def get_agent_context(self) -> Dict[str, Any]:
        """Return context provided to the agent for staking decisions."""

        context = {
            "balance": self.agent_balance,
            "current_round": self.current_round,
            "pending_rounds": [entry.copy() for entry in self.pending_rounds],
            "recent_results": self.resolved_rounds[-5:],
        }
        
        # Phase 2: Add failure mode context if enabled
        if self.enable_failure_modes:
            context["failure_modes"] = {
                "current_regime": self.regime_manager.current_regime(self.current_round).name,
                "is_burn_period": self.burn_simulator.inject_burn(self.current_round, 0.0) != 0.0,
                "recent_failures": self.failure_history[-3:] if self.failure_history else [],
            }
        
        return context

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
    
    # ------------------------------------------------------------------
    def get_failure_mode_summary(self) -> Dict[str, Any]:
        """Get summary of applied failure modes (Phase 2)."""
        
        if not self.enable_failure_modes:
            return {"failure_modes_enabled": False}
        
        # Count failure types
        regime_counts = {}
        burn_count = 0
        
        for entry in self.failure_history:
            regime = entry.get('regime_info', 'unknown')
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            if entry.get('burn_applied', False):
                burn_count += 1
        
        # Calculate correlation impact
        if self.failure_history:
            correlation_changes = [
                entry['modified_correlation'] - entry['base_correlation']
                for entry in self.failure_history
            ]
            correlation_impact = {
                'mean_change': sum(correlation_changes) / len(correlation_changes),
                'min_change': min(correlation_changes),
                'max_change': max(correlation_changes),
            }
        else:
            correlation_impact = {'mean_change': 0.0, 'min_change': 0.0, 'max_change': 0.0}
        
        return {
            "failure_modes_enabled": True,
            "total_rounds_with_failures": len(self.failure_history),
            "regime_distribution": regime_counts,
            "burn_periods": burn_count,
            "correlation_impact": correlation_impact,
        }
    
    def get_current_regime_info(self) -> Dict[str, Any]:
        """Get current regime information (Phase 2)."""
        
        if not self.enable_failure_modes:
            return {"failure_modes_enabled": False}
        
        current_regime = self.regime_manager.current_regime(self.current_round)
        return {
            "failure_modes_enabled": True,
            "current_round": self.current_round,
            "regime": {
                "name": current_regime.name,
                "corr_multiplier": current_regime.corr_multiplier,
                "volatility": current_regime.volatility,
            },
            "is_burn_period": self.burn_simulator.inject_burn(self.current_round, 0.0) != 0.0,
        }


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

