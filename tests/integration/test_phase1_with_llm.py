#!/usr/bin/env python3
"""Test Phase 1 with an actual LLM using Inspect AI."""

from medallion_bench import medallion_bench
from inspect_ai import eval
from inspect_ai.log import read_eval_log
import os
import sys

def main():
    """Run Phase 1 evaluation with a real LLM."""

    print("=" * 60)
    print("Phase 1 LLM Evaluation Test")
    print("=" * 60)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  No API key found!")
        print("\nTo run this test, set one of:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        print("\nSkipping LLM evaluation test.")
        return 1

    # Determine which model to use
    if os.getenv("ANTHROPIC_API_KEY"):
        model = "anthropic/claude-3-5-haiku-20241022"
        print(f"\n✓ Using model: {model}")
    elif os.getenv("OPENAI_API_KEY"):
        model = "openai/gpt-4o-mini"
        print(f"\n✓ Using model: {model}")

    # Create Phase 1 task with minimal rounds for testing
    print("\nCreating Phase 1 task (2 rounds)...")
    task = medallion_bench(rounds=2, phase=1, seed=42)

    print(f"Task: {task.dataset.name}")
    print(f"Samples: {len(task.dataset)}")
    print(f"Metadata: {task.metadata}")

    # Run evaluation
    print("\n" + "=" * 60)
    print("Running Evaluation...")
    print("=" * 60)
    print("\nNote: This will call the LLM API and may take 1-2 minutes.")
    print("The agent will attempt to:")
    print("  1. Load and explore Numerai data")
    print("  2. Develop predictive models")
    print("  3. Make strategic decisions")
    print("\nStarting evaluation...\n")

    try:
        result = eval(
            task,
            model=model,
            log_dir="./eval_logs"
        )

        # Display results
        print("\n" + "=" * 60)
        print("Evaluation Results")
        print("=" * 60)

        print(f"\nStatus: {result.status}")
        print(f"Samples: {result.stats.total_samples}")
        print(f"Completed: {result.stats.completed_samples}")

        if result.results:
            print("\n" + "=" * 60)
            print("Sample Results")
            print("=" * 60)

            for i, sample_result in enumerate(result.results):
                print(f"\n--- Sample {i+1} (Round {i+1}) ---")
                print(f"Sample ID: {sample_result.id}")

                # Show scores if available
                if sample_result.scores:
                    print("\nScores:")
                    for score_name, score_value in sample_result.scores.items():
                        if hasattr(score_value, 'value'):
                            print(f"  {score_name}: {score_value.value:.2f}")
                        else:
                            print(f"  {score_name}: {score_value}")

                # Show model output (truncated)
                if hasattr(sample_result, 'output') and sample_result.output:
                    output_text = str(sample_result.output)
                    if len(output_text) > 300:
                        output_text = output_text[:300] + "..."
                    print(f"\nModel output (first 300 chars):\n{output_text}")

        print("\n" + "=" * 60)
        print("✓ Phase 1 LLM evaluation completed successfully!")
        print("=" * 60)

        print(f"\nFull logs saved to: ./eval_logs")
        print("View with: inspect view ./eval_logs")

        return 0

    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
