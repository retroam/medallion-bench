#!/bin/bash
# Run all Phase 1 integration tests (excluding LLM test)

set -e  # Exit on error

echo "=========================================="
echo "Running MedallionBench Integration Tests"
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "Test 1/4: Task Creation Test"
echo "----------------------------------------"
python test_phase1.py
echo ""

echo "Test 2/4: Tournament Simulation Test"
echo "----------------------------------------"
python test_phase1_simulation.py
echo ""

echo "Test 3/4: Full Tournament Test (25 rounds)"
echo "----------------------------------------"
python test_phase1_full.py
echo ""

echo "Test 4/4: Scoring System Test"
echo "----------------------------------------"
python test_phase1_scoring.py
echo ""

echo "=========================================="
echo "✓ All integration tests passed!"
echo "=========================================="
echo ""
echo "To test with a real LLM, run:"
echo "  export ANTHROPIC_API_KEY='your-key'"
echo "  python test_phase1_with_llm.py"
