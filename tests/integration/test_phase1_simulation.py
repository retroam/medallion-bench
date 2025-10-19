#!/usr/bin/env python3
"""Test Phase 1 tournament simulation."""

import asyncio
import pandas as pd
from medallion_bench.data_pipeline import NumeraiDataPipeline
from medallion_bench.tournament import SimulatedNumeraiTournament, NumeraiAgent, StakeDecision


class DummyAgent(NumeraiAgent):
    """Simple test agent that makes random predictions."""

    async def generate_predictions(self, round_data):
        """Generate simple predictions based on tournament data."""
        tournament_df = round_data["tournament"]

        # Create predictions - just use row index normalized
        predictions = pd.DataFrame({
            "id": tournament_df["id"],
            "prediction": [i / len(tournament_df) for i in range(len(tournament_df))]
        })

        return predictions

    async def decide_stake(self, context):
        """Conservative staking strategy."""
        balance = context["balance"]

        # Stake 5% of balance
        stake_amount = balance * 0.05

        return StakeDecision(
            amount=stake_amount,
            confidence=0.7,
            corr_weight=1.0,
            mmc_weight=0.0
        )


async def main():
    """Run Phase 1 simulation test."""
    print("=" * 60)
    print("Phase 1 Tournament Simulation Test")
    print("=" * 60)

    # Create data pipeline
    pipeline = NumeraiDataPipeline(cache_dir="./test_cache", base_seed=42)

    # Create tournament starting at round 200
    tournament = SimulatedNumeraiTournament(
        data_pipeline=pipeline,
        start_round=200,
        initial_balance=100.0
    )

    print(f"\nInitial balance: {tournament.agent_balance} NMR")
    print(f"Starting round: {tournament.current_round}")

    # Create test agent
    agent = DummyAgent()

    # Run 5 rounds
    print("\n" + "=" * 60)
    print("Running 5 Tournament Rounds")
    print("=" * 60)

    for i in range(5):
        result = await tournament.run_round(agent)

        print(f"\n--- Round {result['round']} ---")
        print(f"Correlation: {result['correlation']:.4f}")
        print(f"Stake decision: {result['stake_decision']['amount']:.2f} NMR")
        print(f"Confidence: {result['stake_decision']['confidence']:.2f}")
        print(f"Balance: {result['balance']:.2f} NMR")
        print(f"Pending rounds: {result['pending']}")
        print(f"Status: {result['status']}")

    # Show resolved rounds
    print("\n" + "=" * 60)
    print("Resolved Rounds")
    print("=" * 60)

    if tournament.resolved_rounds:
        for resolved in tournament.resolved_rounds:
            print(f"\nRound {resolved['round']}:")
            print(f"  Stake: {resolved['stake']:.2f} NMR")
            print(f"  Correlation: {resolved['correlation']:.4f}")
            print(f"  Payout: {resolved['payout']:.2f} NMR")
            print(f"  Balance after: {resolved['balance_after']:.2f} NMR")
    else:
        print("\nNo rounds resolved yet (need to advance 20 rounds)")

    # Show pending rounds
    print("\n" + "=" * 60)
    print("Pending Rounds")
    print("=" * 60)

    if tournament.pending_rounds:
        for pending in tournament.pending_rounds:
            print(f"\nRound {pending['round']}:")
            print(f"  Stake: {pending['stake']:.2f} NMR")
            print(f"  Correlation: {pending['correlation']:.4f}")
            print(f"  Resolves at: Round {pending['resolves_at']}")

    print("\n" + "=" * 60)
    print("✓ Phase 1 simulation completed successfully!")
    print("=" * 60)

    # Cleanup
    pipeline.clear_cache()


if __name__ == "__main__":
    asyncio.run(main())
