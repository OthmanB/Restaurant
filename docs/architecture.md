# Architecture

The repository is organized around a strict loader layer, a simulation API layer, and a plotting script layer.

## High-Level Architecture

```mermaid
flowchart TD
    A[setup/*.yaml] --> B[config_loader.py]
    B --> C[simulation_api.py]
    C --> D[main.py plotting]
    C --> E[Programmatic caller]
    C --> F[tests/*]

    C --> G[functions_population.py]
    C --> H[functions_income.py]
    C --> I[misc.py]
    C --> J[error_checks.py]
```

## Module Responsibilities

- `sources/config_loader.py`
  - Parses `.yaml/.yml` and `.json` configs.
  - Enforces strict schema validation.
  - Raises `ConfigValidationError` on invalid structure.
- `sources/simulation_api.py`
  - Core callable engine (`simulate_year`, `simulate_batch`, `expand_sweep_configs`).
  - Computes population, revenues, expenses, income, and metadata.
- `sources/main.py`
  - Script entrypoint for standalone modeling and figure generation.
  - Uses canonical YAML configs in `setup/` by default.
- `sources/functions_population.py`
  - Attendance/population signal generation (`compute_Nc`).
- `sources/functions_income.py`
  - Revenue and expense primitives (menu, fees, staff, recurring).
- `tests/`
  - Automated intent-based suite (loading, outputs, sweeps, properties, invariants).

## Runtime Data Flow

```mermaid
sequenceDiagram
    participant U as User/Caller
    participant L as config_loader
    participant S as simulation_api
    participant P as population/income funcs

    U->>L: load_*_config(path)
    L-->>U: validated dicts
    U->>S: simulate_year(...)
    S->>P: compute_Nc + revenue/expense blocks
    P-->>S: arrays and aggregates
    S-->>U: output dict (metadata/time/population/revenue/expenses/income)
```

## Two Primary Use Cases

1. Standalone forward modeling
   - Run `python3 sources/main.py` with YAML configs.
2. Embedded synthetic-data generation
   - Import `sources.simulation_api` and call simulation functions directly from another program.
