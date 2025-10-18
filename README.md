# MedallionBench

**MedallionBench: LLM ML Research Capability Evaluation Framework**

A modular, multi-round evaluation framework designed to assess LLMs as data scientists competing in the Numerai tournament. MedallionBench evaluates data exploration, model development, risk management, and long-horizon coherence across multiple phases.

## Overview

MedallionBench simulates the Numerai tournament experience, where participants develop machine learning models to predict stock market performance. The framework tests LLMs across four phases:

- **Phase 1-2**: Data exploration & model development 
- **Phase 3**: Research synthesis & documentation 
- **Phase 4**: Long-horizon coherence & memory ablations

## Features

- **Progressive Data Disclosure**: Data availability increases across phases
- **Multi-Agent Architecture**: Specialized agents for data, modeling, and submission
- **Comprehensive Scoring**: Technical, methodology, iterative, bankroll, and coherence metrics
- **Memory & Persistence**: Scratchpad, KV store, and vector memory tools
- **Risk Management**: Bankroll simulation and risk metric tracking
- **Reproducibility**: Seed control and variance analysis

## Installation

```bash
# Basic installation
pip install medallion-bench

# With development dependencies
pip install medallion-bench[dev]

# With Numerai API support
pip install medallion-bench[numerai]

# Full installation
pip install medallion-bench[all]
```

## Running MedallionBench

The framework exposes a single `medallion_bench` task factory that can be
executed with any [Inspect AI](https://github.com/openai/inspect_ai) compatible
model. The examples below assume you have already configured credentials for
your chosen model provider (for example by exporting `OPENAI_API_KEY`).

### Python API

```python
from medallion_bench import medallion_bench
from inspect_ai import eval

# Phase 1 quick run (10 rounds)
result = eval(medallion_bench(), model="openai/gpt-4o-mini")
print(result.summary())

# Phase 4 extended run (40 rounds)
task = medallion_bench(rounds=40, phase=4, seed=42)
result = eval(task, model="anthropic/claude-3-5-sonnet-20241022")
print(result.summary())
```

### Inspect AI CLI

Inspect AI also ships with a CLI that can execute tasks directly from the
command line. Save any task configuration you want to tweak in a Python file,
then point the CLI at it:

```bash
cat <<'PY' > run_medallion.py
from medallion_bench import medallion_bench

task = medallion_bench(rounds=20, phase=2, seed=7)
PY

inspect eval run_medallion.py --model openai/gpt-4o-mini
```

The CLI command prints a structured report containing overall scores plus the
per-round scratchpad information recorded during the evaluation. Add
`--output medallion-results.json` to persist the full result artifact.

## Quick Start

```python
from medallion_bench import medallion_bench

# Create a task with custom configuration
task = medallion_bench(rounds=30, phase=3, seed=11)

print(task.metadata)
```

## Architecture

### Core Components

- **Task Definition**: Main evaluation task with configurable phases and rounds
- **Dataset Module**: Progressive data disclosure and sample generation
- **Solver Module**: Multi-agent coordination and tool management
- **Scoring Framework**: Multi-dimensional evaluation metrics
- **Specialized Tools**: Numerai data access, simulation, and memory tools

### Multi-Agent Architecture

MedallionBench uses a multi-agent approach with specialized sub-agents:

- **DataAgent**: Handles EDA and feature engineering
- **ModelAgent**: Develops and trains predictive models
- **SubmissionAgent**: Manages submissions and risk strategy

## Evaluation Metrics

### Core Scoring Dimensions

1. **Technical Score** (35%): Code quality, library usage, error handling
2. **Methodology Score** (35%): Data exploration, feature engineering, model selection
3. **Iterative Score** (30%): Learning and improvement across rounds
4. **Bankroll Score**: Risk management and financial performance
5. **Coherence Score**: Long-horizon memory and consistency (Phase 4)

### Phase-Specific Weighting

- **Phase 1-2**: Equal focus on technical and methodology
- **Phase 3**: Added research synthesis evaluation
- **Phase 4**: Includes coherence and variance metrics

## Tools & Capabilities

### Data Tools
- **NumeraiDataTool**: Access to tournament datasets
- **ScratchpadTool**: Persistent note-taking across rounds
- **KVTool**: Structured key-value storage

### Model Tools
- **ModelTrainingTool**: Model development with seed control
- **SubmissionSimulatorTool**: Historical submission simulation

### Risk Management
- **BusinessSimTool**: Bankroll tracking and risk metrics
- **VectorMemoryTool**: Embedding-based memory retrieval

## Development

### Setup

```bash
git clone https://github.com/your-org/medallion-bench
cd medallion-bench
pip install -e .[dev]
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_dataset.py
pytest tests/test_scoring.py
```

### Code Quality

```bash
# Format code
black medallion_bench tests

# Sort imports
isort medallion_bench tests

# Type checking
mypy medallion_bench

# Lint
flake8 medallion_bench tests
```

## Current Status

This is a skeleton implementation that provides the basic structure for MedallionBench. Key components implemented:

- ✅ Core package structure with proper Inspect AI integration
- ✅ Task definition with configurable phases and rounds
- ✅ Dataset module with progressive data disclosure
- ✅ Multi-agent solver architecture (placeholder)
- ✅ Comprehensive scoring framework
- ✅ Specialized tools for Numerai simulation
- ✅ Basic test suite and development setup

### Next Steps

1. **Integration with multiagent-inspect**: Implement proper multi-agent coordination
2. **Tool Implementation**: Add actual Numerai API integration and data loading
3. **Scoring Logic**: Implement real evaluation metrics instead of placeholders
4. **Memory Systems**: Add persistent storage and vector memory capabilities
5. **Testing**: Expand test coverage and add integration tests

## Contributing



## License


## Citation

If you use MedallionBench in your research, please cite:

```bibtex
@misc{medallion-bench,
  title={MedallionBench: LLM ML Research Capability Evaluation Framework},
  author={MedallionBench Contributors},
  year={2025},
  url={https://github.com/your-org/medallion-bench}
}
```
