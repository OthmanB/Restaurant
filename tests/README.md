# Test Suite Guide

This directory contains **automated, non-interactive tests** for the Restaurant modeling codebase.

## Structure (intent-based)

- `test_config_loading.py`
  - Config loader behavior, key validation, alias normalization.

- `test_simulation_outputs.py`
  - Simulation API output contracts and deterministic reproducibility checks.

- `test_sweep_generation.py`
  - Sweep expansion rules and batch metadata contracts.

- `test_math_properties.py`
  - Mathematical property tests (monotonicity, bounds, normalization, scaling, truncation behavior).

- `test_system_invariants.py`
  - System-level invariants (non-negativity, accounting identities, time monotonicity, provenance stability, seeded stochastic reproducibility).

## Manual vs automated tests

- Automated tests are in this `tests/` folder.
- Manual visual probes remain in `sources/tests.py` and are **not** part of CI-style runs.

## Running tests

Use the helper script at repo root:

```bash
scripts/run_tests.sh all
```

Available modes:

```bash
scripts/run_tests.sh all         # full suite
scripts/run_tests.sh fast        # quick config + sweep checks
scripts/run_tests.sh properties  # math + system property checks
scripts/run_tests.sh simulation  # simulation output contract checks
```

You can also pass a specific unittest target:

```bash
scripts/run_tests.sh tests.test_math_properties
```

## Environment notes

The script expects:
- virtual environment at `.venv`
- required packages installed (`numpy`, `scipy`, `matplotlib`, `pyyaml`)

If missing:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy scipy matplotlib pyyaml
```

## Design principles for new tests

1. Keep tests deterministic (use explicit seeds).
2. Prefer property/invariant assertions over visual checks.
3. Keep tests intent-focused and small.
4. Avoid side effects (no file output unless explicitly tested).
5. Do not import `sources/main.py` for unit tests; prefer API-level calls.
