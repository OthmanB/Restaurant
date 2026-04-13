# Restaurant Analytical Model for Sales and Expenses

This project provides a configuration-driven analytical simulation of restaurant attendance, revenue, expenses, and income.
It supports both:

- standalone forward modeling (script + plots), and
- programmatic synthetic-data generation for downstream workflows.

## Documentation Index

Start from the docs hub, then jump to focused guides:

- [Documentation Hub](docs/README.md)
- [Quick Start](docs/quick-start.md)
- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Simulation API](docs/simulation-api.md)
- [Testing](docs/testing.md)
- [Theory report source](docs/tex/report.tex)
- [Theory report PDF](docs/tex/report.pdf)
- [Research notes](docs/research/README.md)

## Quick Start

1. Create and populate the virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy scipy matplotlib pyyaml
```

2. Run the standalone simulation:

```bash
python3 sources/main.py
```

3. Run automated checks:

```bash
scripts/run_tests.sh fast
scripts/run_tests.sh simulation
```

## Configuration Format

Runtime configurations are YAML-first and live under `setup/`:

- `setup/menu_setup_R1.yaml`
- `setup/behavior_setup_r1.yaml`
- `setup/population_setup_R1.yaml`
- `setup/expenses_setup_R1.yaml`

JSON remains temporarily supported for compatibility, but YAML is the default for new and updated flows.

## Programmatic Entry Points

Use these modules for embedding the model in other software:

- `sources/config_loader.py` for strict config loading and validation
- `sources/simulation_api.py` for `simulate_year`, `simulate_batch`, and `expand_sweep_configs`

For examples, see [Simulation API](docs/simulation-api.md).
