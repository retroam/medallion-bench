"""Tests for the simulated Numerai tournament environment."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from medallion_bench.data_pipeline import NumeraiDataPipeline
from medallion_bench.tournament import (
    NumeraiAgent,
    SimulatedNumeraiTournament,
    StakeDecision,
)


@dataclass
class _PerfectAgent(NumeraiAgent):
    pipeline: NumeraiDataPipeline

    async def generate_predictions(self, round_data):
        round_id = round_data["metadata"]["round"]
        hidden = self.pipeline.get_hidden_targets(round_id)
        return hidden.rename(columns={"target": "prediction"})

    async def decide_stake(self, context):
        return StakeDecision(amount=2.0, confidence=0.9, corr_weight=1.0, mmc_weight=0.0)


@pytest.mark.asyncio
async def test_tournament_runs_round(tmp_path, tmp_path_factory, request):
    del tmp_path_factory, request
    pipeline = NumeraiDataPipeline(cache_dir=tmp_path)
    tournament = SimulatedNumeraiTournament(data_pipeline=pipeline, start_round=210)
    agent = _PerfectAgent(pipeline)

    result = await tournament.run_round(agent)

    assert result["round"] == 210
    assert result["status"] == "ACTIVE"
    assert len(tournament.pending_rounds) == 1


@pytest.mark.asyncio
async def test_tournament_resolves_after_delay(tmp_path, tmp_path_factory, request):
    del tmp_path_factory, request
    pipeline = NumeraiDataPipeline(cache_dir=tmp_path)
    tournament = SimulatedNumeraiTournament(data_pipeline=pipeline, start_round=210)
    agent = _PerfectAgent(pipeline)

    starting_balance = tournament.agent_balance

    for _ in range(21):
        await tournament.run_round(agent)

    assert tournament.agent_balance > starting_balance
    assert any(entry["round"] == 210 for entry in tournament.resolved_rounds)
    assert tournament.pending_rounds


def test_calculate_correlation_handles_missing_ids():
    predictions = pd.DataFrame({"id": ["a", "b"], "prediction": [0.1, 0.2]})
    targets = pd.DataFrame({"id": ["c", "d"], "target": [0.3, 0.4]})

    corr = SimulatedNumeraiTournament.calculate_correlation(predictions, targets)
    assert corr == 0.0
