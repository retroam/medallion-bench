#!/usr/bin/env python3
"""Test Phase 1 of MedallionBench."""

from medallion_bench import medallion_bench

# Create a Phase 1 task with minimal rounds for quick testing
task = medallion_bench(rounds=3, phase=1, seed=42)

print("=" * 60)
print("MedallionBench Phase 1 Test")
print("=" * 60)
print(f"\nTask Name: {task.dataset.name}")
print(f"Task Metadata: {task.metadata}")
print(f"\nNumber of samples: {len(task.dataset)}")

# Inspect the first sample
print("\n" + "=" * 60)
print("Sample 1 (Round 1)")
print("=" * 60)
sample = task.dataset[0]
print(f"\nSample ID: {sample.id}")
print(f"Metadata: {sample.metadata}")
print(f"\nInput prompt (first 500 chars):")
print(sample.input[:500] + "...")
print(f"\nTarget: {sample.target}")

# Show data config progression
print("\n" + "=" * 60)
print("Data Config Progression")
print("=" * 60)
for i, sample in enumerate(task.dataset):
    config = sample.metadata.get("data_config", {})
    print(f"\nRound {i+1}:")
    print(f"  Training data: {config.get('training_data', False)}")
    print(f"  Validation data: {config.get('validation_data', False)}")
    print(f"  Feature metadata: {config.get('feature_metadata', False)}")
    print(f"  Tournament data: {config.get('tournament_data', False)}")

print("\n" + "=" * 60)
print("✓ Phase 1 task created successfully!")
print("=" * 60)
