# MedallionBench

**MedallionBench: LLM ML Research Capability Evaluation Framework**

A modular, multi-round evaluation framework designed to assess LLMs as data scientists competing in the Numerai tournament. MedallionBench evaluates data exploration, model development, risk management, and long-horizon coherence across multiple phases.

## Overview

MedallionBench simulates the Numerai tournament experience, where participants develop machine learning models to predict stock market performance. The framework tests LLMs across four phases:

- **Phase 1-2**: Data exploration & model development (rounds 1-20)
- **Phase 3**: Research synthesis & documentation (rounds 21-25)  
- **Phase 4**: Long-horizon coherence & memory ablations (rounds 26-40)

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

## Quick Start

```python
from medallion_bench import medallion_bench
from inspect_ai import eval

# Run basic evaluation (Phase 1, 10 rounds)
task = medallion_bench()
result = eval(task, model="openai/gpt-4")

# Run advanced evaluation (Phase 4, 40 rounds)
task = medallion_bench(rounds=40, phase=4, seed=42)
result = eval(task, model="anthropic/claude-3-sonnet-20240229")
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
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Lint
flake8 src/ tests/
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

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use MedallionBench in your research, please cite:

```bibtex
@misc{medallion-bench,
  title={MedallionBench: LLM ML Research Capability Evaluation Framework},
  author={MedallionBench Contributors},
  year={2024},
  url={https://github.com/your-org/medallion-bench}
}
```
