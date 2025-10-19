#!/usr/bin/env python3
"""Test Phase 1 with full round resolution."""

import asyncio
import pandas as pd
from medallion_bench.data_pipeline import NumeraiDataPipeline
from medallion_bench.tournament import SimulatedNumeraiTournament, NumeraiAgent, StakeDecision


class DummyAgent(NumeraiAgent):
    """Simple test agent with varying performance."""

    def __init__(self):
        self.round_count = 0

    async def generate_predictions(self, round_data):
        """Generate predictions with some variability."""
        tournament_df = round_data["tournament"]

        # Add some noise to predictions to vary correlation
        import numpy as np
        np.random.seed(self.round_count)

        # Base predictions with some noise
        predictions = pd.DataFrame({
            "id": tournament_df["id"],
            "prediction": np.random.uniform(0, 1, len(tournament_df))
        })

        self.round_count += 1
        return predictions

    async def decide_stake(self, context):
        """Adaptive staking based on balance and recent performance."""
        balance = context["balance"]
        recent_results = context.get("recent_results", [])

        # Start conservative, increase if doing well
        base_stake_pct = 0.03

        if recent_results:
            # Calculate average payout from recent results
            avg_payout = sum(r.get("payout", 0) for r in recent_results) / len(recent_results)
            if avg_payout > 0.5:  # Doing well
                base_stake_pct = 0.08
            elif avg_payout < -0.5:  # Doing poorly
                base_stake_pct = 0.01

        stake_amount = balance * base_stake_pct

        return StakeDecision(
            amount=stake_amount,
            confidence=0.6,
            corr_weight=1.0,
            mmc_weight=0.0
        )


async def main():
    """Run 25 rounds to see resolution."""
    print("=" * 60)
    print("Phase 1 Full Tournament Test (25 rounds)")
    print("=" * 60)

    # Create data pipeline
    pipeline = NumeraiDataPipeline(cache_dir="./test_cache", base_seed=42)

    # Create tournament
    tournament = SimulatedNumeraiTournament(
        data_pipeline=pipeline,
        start_round=200,
        initial_balance=100.0
    )

    print(f"\nInitial balance: {tournament.agent_balance} NMR")

    # Create test agent
    agent = DummyAgent()

    # Run 25 rounds
    results = []
    for i in range(25):
        result = await tournament.run_round(agent)
        results.append(result)

        if i < 5 or i >= 20:  # Show first 5 and last 5
            print(f"\nRound {result['round']}: ", end="")
            print(f"Corr={result['correlation']:.4f}, ", end="")
            print(f"Stake={result['stake_decision']['amount']:.2f}, ", end="")
            print(f"Balance={result['balance']:.2f}, ", end="")
            print(f"Pending={result['pending']}, Resolved={len(tournament.resolved_rounds)}")
        elif i == 5:
            print("  ... (rounds 206-219) ...")

    # Summary
    print("\n" + "=" * 60)
    print("Tournament Summary")
    print("=" * 60)

    print(f"\nTotal rounds run: {len(results)}")
    print(f"Final balance: {tournament.agent_balance:.2f} NMR")
    print(f"Net change: {tournament.agent_balance - 100.0:+.2f} NMR")
    print(f"Pending rounds: {len(tournament.pending_rounds)}")
    print(f"Resolved rounds: {len(tournament.resolved_rounds)}")

    # Show resolved round statistics
    if tournament.resolved_rounds:
        print("\n" + "=" * 60)
        print("Resolved Round Statistics")
        print("=" * 60)

        total_payout = sum(r["payout"] for r in tournament.resolved_rounds)
        avg_corr = sum(r["correlation"] for r in tournament.resolved_rounds) / len(tournament.resolved_rounds)
        avg_payout = total_payout / len(tournament.resolved_rounds)

        print(f"\nResolved: {len(tournament.resolved_rounds)} rounds")
        print(f"Average correlation: {avg_corr:.4f}")
        print(f"Average payout: {avg_payout:+.2f} NMR")
        print(f"Total payout: {total_payout:+.2f} NMR")

        # Show first few resolved rounds
        print("\nFirst 3 resolved rounds:")
        for resolved in tournament.resolved_rounds[:3]:
            print(f"  Round {resolved['round']}: ", end="")
            print(f"Corr={resolved['correlation']:.4f}, ", end="")
            print(f"Stake={resolved['stake']:.2f}, ", end="")
            print(f"Payout={resolved['payout']:+.2f}")

    print("\n" + "=" * 60)
    print("✓ Phase 1 full test completed successfully!")
    print("=" * 60)

    # Cleanup
    pipeline.clear_cache()


if __name__ == "__main__":
    asyncio.run(main())
