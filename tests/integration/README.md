# MedallionBench Integration Tests

This directory contains integration tests for MedallionBench that test the complete system end-to-end.

## Test Files

### Phase 1 Tests

#### `test_phase1.py`
Tests basic task creation and dataset generation.

**What it tests:**
- Task factory (`medallion_bench()`)
- Dataset creation with progressive disclosure
- Sample generation with proper metadata
- Phase 1 data configuration

**Run:**
```bash
python tests/integration/test_phase1.py
```

**Expected output:**
- Task metadata display
- Sample inspection (Round 1)
- Data config progression for all rounds

---

#### `test_phase1_simulation.py`
Tests tournament simulation mechanics without LLM.

**What it tests:**
- Data pipeline with synthetic data generation
- Tournament round execution
- Correlation calculation (Spearman)
- Staking decisions
- Pending round tracking

**Run:**
```bash
python tests/integration/test_phase1_simulation.py
```

**Expected output:**
- 5 rounds executed
- Correlations calculated
- Stakes tracked
- Pending rounds queued for resolution

---

#### `test_phase1_full.py`
Tests full tournament with round resolutions (20+ rounds).

**What it tests:**
- 25-round tournament execution
- 20-round resolution delay (realistic Numerai timing)
- Payout calculations
- Balance management
- Adaptive staking strategy
- Resolved vs pending round tracking

**Run:**
```bash
python tests/integration/test_phase1_full.py
```

**Expected output:**
- 25 rounds executed
- First 5 rounds resolve after 20-round delay
- Balance changes from payouts
- Statistics on resolved rounds

---

#### `test_phase1_scoring.py`
Tests the multi-dimensional scoring system.

**What it tests:**
- All 6 scorer components (Technical, Methodology, Iterative, Bankroll, Coherence, Variance)
- Score calculation logic
- Phase 1 composite weighting
- Metadata tracking

**Run:**
```bash
python tests/integration/test_phase1_scoring.py
```

**Expected output:**
- Individual scores for each dimension
- Composite score calculation
- Phase 1 weighted final score

---

#### `test_phase1_with_llm.py`
Tests full evaluation with a real LLM model.

**What it tests:**
- Complete Inspect AI evaluation workflow
- LLM agent interaction with tools
- Model output and scoring
- End-to-end Phase 1 evaluation

**Requirements:**
- Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variable

**Run:**
```bash
export ANTHROPIC_API_KEY='your-key'
python tests/integration/test_phase1_with_llm.py
```

**Expected output:**
- Evaluation with real LLM (2 rounds)
- Model outputs and tool usage
- Scores for each round
- Log files saved to `./eval_logs`

**Note:** This test makes real API calls and will incur costs (~$0.01-0.10 depending on model).

---

## Running All Tests

### Quick Test (no LLM)
```bash
cd tests/integration
python test_phase1.py
python test_phase1_simulation.py
python test_phase1_scoring.py
```

### Full Test Suite (no LLM)
```bash
cd tests/integration
python test_phase1.py
python test_phase1_simulation.py
python test_phase1_full.py
python test_phase1_scoring.py
```

### Complete Test (with LLM)
```bash
export ANTHROPIC_API_KEY='your-key'
cd tests/integration
python test_phase1.py
python test_phase1_simulation.py
python test_phase1_full.py
python test_phase1_scoring.py
python test_phase1_with_llm.py
```

## Test Results

See [PHASE1_TEST_RESULTS.md](./PHASE1_TEST_RESULTS.md) for detailed test results and analysis.

## Unit Tests

For faster unit tests that don't require full integration, see the main `tests/` directory:
```bash
pytest tests/
```

These unit tests cover individual components:
- `test_data_pipeline.py` - Data pipeline functionality
- `test_tournament.py` - Tournament mechanics
- `test_dataset.py` - Dataset creation
- `test_scoring.py` - Individual scorers
- `test_medallion_bench.py` - Task factory

## Troubleshooting

### Cache Issues
If you encounter caching issues, clear the test cache:
```bash
rm -rf test_cache numerai_cache ./eval_logs
```

### Import Errors
Make sure MedallionBench is installed in development mode:
```bash
pip install -e .
# or with uv:
uv pip install --system -e .
```

### API Key Issues
For LLM tests, ensure your API key is set:
```bash
# For Anthropic
export ANTHROPIC_API_KEY='your-key'

# For OpenAI
export OPENAI_API_KEY='your-key'
```

### Slow Tests
The full tests can take time:
- `test_phase1_full.py`: ~10-30 seconds (25 rounds)
- `test_phase1_with_llm.py`: ~1-3 minutes (2 rounds with LLM)

Use smaller round counts for faster testing during development.

## Adding New Integration Tests

When adding new integration tests:

1. Create a descriptive filename: `test_phase{N}_{feature}.py`
2. Add a module docstring explaining what it tests
3. Include print statements for progress visibility
4. Clean up any created files/caches at the end
5. Update this README with the new test details

## CI/CD Integration

These integration tests are designed to be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests (no LLM)
  run: |
    python tests/integration/test_phase1.py
    python tests/integration/test_phase1_simulation.py
    python tests/integration/test_phase1_full.py
    python tests/integration/test_phase1_scoring.py

- name: Run LLM Integration Test
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    python tests/integration/test_phase1_with_llm.py
```
