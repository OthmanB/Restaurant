# AGENTS.md

## Purpose
Repository-specific guidance for coding agents working in `/Users/obenomar/Trade/Restaurant`.
Use this file as the source of truth for layout, commands, and conventions.

## Snapshot
- Language: Python (3.10+ assumed)
- Source code: `sources/`
- Runtime config: `setup/`
- Automated tests: `tests/`
- Test helper script: `scripts/run_tests.sh`
- Data / plots output: `data/`
- Main script entrypoint: `sources/main.py`
- Programmatic API: `sources/simulation_api.py`
- Config loading/validation API: `sources/config_loader.py`
- Theory/docs: `Readme.md`, `docs/`, `setup/Readme.md`, `instructions/`

## Important Files
- `sources/main.py`: script entrypoint; loads configs and generates plots from simulation outputs.
- `sources/simulation_api.py`: core callable simulation interface (`simulate_year`, `simulate_batch`, `expand_sweep_configs`).
- `sources/config_loader.py`: strict config loading + validation, JSON and YAML support, raises `ConfigValidationError`.
- `sources/functions_population.py`: attendance and population curves (`compute_Nc`).
- `sources/functions_income.py`: revenue + expense primitives (`expenses_fees`, staff/recurring/menu costs).
- `sources/error_checks.py`: validation helpers used by legacy flow (return code-list style checks).
- `sources/misc.py`: integration/sums/combinatorics utilities.
- `sources/tests.py`: manual/visual helper script (not part of automated suite).
- `tests/test_config_loading.py`: loader validation tests.
- `tests/test_sweep_generation.py`: sweep expansion behavior tests.
- `tests/test_simulation_outputs.py`: simulation output contract tests.
- `tests/test_math_properties.py`: mathematical property tests.
- `tests/test_system_invariants.py`: system-level invariants.
- `scripts/run_tests.sh`: canonical test runner wrapper.

## Repo Rules
- Repo policy exists in `.github/copilot-instructions.md` and must be followed.
- No `.cursorrules` file was found.
- No `.cursor/rules/` directory was found.

## Tooling Reality
- No `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini`, `pytest.ini`, `Makefile`, `Dockerfile`, `package.json`, or CI workflow is defined.
- No official repo-defined build/lint/typecheck commands exist.
- Current runtime/test dependencies used by code and scripts: `numpy`, `scipy`, `matplotlib`.
- Optional dependency: `pyyaml` (required for YAML config files).

## Environment Setup
### Recommended venv
```bash
python3 -m venv .venv
.venv/bin/pip install numpy scipy matplotlib pyyaml
```

### PYTHONPATH requirement
Many modules in `sources/` still use sibling imports (for example `from error_checks import ...`).
Use this before direct module/test runs:
```bash
export PYTHONPATH="/Users/obenomar/Trade/Restaurant/sources:/Users/obenomar/Trade/Restaurant"
```

## Commands Agents Can Run
These are practical commands matching the current repo.

### Main script
```bash
python3 sources/main.py
```

### Main script with explicit configs
```bash
python3 -c "from sources.main import main; main(test_menu_setup_file='setup/menu_setup_R1.yaml', test_behavior_setup_file='setup/behavior_setup_r1.yaml', test_population_setup_file='setup/population_setup_R1.yaml', test_expenses_setup_file='setup/expenses_setup_R1.yaml')"
```

### Canonical test commands (preferred)
```bash
scripts/run_tests.sh all
scripts/run_tests.sh fast
scripts/run_tests.sh properties
scripts/run_tests.sh simulation
```

### Run a single test module
```bash
export PYTHONPATH="/Users/obenomar/Trade/Restaurant/sources:/Users/obenomar/Trade/Restaurant"
.venv/bin/python -m unittest tests.test_config_loading
```

### Run a single test function
```bash
export PYTHONPATH="/Users/obenomar/Trade/Restaurant/sources:/Users/obenomar/Trade/Restaurant"
.venv/bin/python -m unittest tests.test_math_properties.TestMathematicalProperties.test_attractiveness_monotonicity
```

### Full unittest discovery directly
```bash
export PYTHONPATH="/Users/obenomar/Trade/Restaurant/sources:/Users/obenomar/Trade/Restaurant"
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

### Manual visual checks (non-automated)
```bash
python3 sources/tests.py
```

## Programmatic API (for external callers)
### Recommended load path
1. Load and validate configs with `sources/config_loader.py`.
2. Call simulation functions from `sources/simulation_api.py`.

### Config loading functions
- `load_menu_config(path_like)`
- `load_behavior_config(path_like)`
- `load_population_config(path_like)`
- `load_expenses_config(path_like)`
- `ConfigValidationError` is raised on missing/invalid structure.

### Simulation functions
- `simulate_year(menu_cfg, behavior_cfg, population_cfg, expenses_cfg, *, seed=None, mode='deterministic', run_id=None, sweep_id=None, sweep_params=None)`
- `simulate_batch(config_iterable, *, seed=None, n_runs=1, mode='deterministic')`
- `expand_sweep_configs(base_configs, sweep_spec, *, sweep_id='sweep-0')`

### Output contract highlights (`simulate_year`)
Returns a nested dict with keys:
- `metadata` (mode, seed, hashes, run/sweep tags, model version)
- `time` (hour/day/week/month axes and integrated versions)
- `population` (hourly and aggregated attendance)
- `revenue` (day/week/month)
- `expenses` (menu/fees/staff/recurring and totals)
- `income` (revenue minus total expenses)

## Testing Guidance
- `tests/` is the automated suite; prefer `scripts/run_tests.sh` targets.
- `sources/tests.py` is exploratory/manual and may include plotting behavior.
- Property tests include stochastic checks; keep tolerances realistic and seeds explicit.
- After edits, run the narrowest relevant subset first, then broader suite if needed.

## Code Style
Follow existing style unless task is an explicit refactor.

### Naming and structure
- Use `snake_case` for functions, variables, and config keys.
- Preserve flat module layout in `sources/`.
- Avoid broad structural rewrites unless requested.

### Imports
- Prefer explicit imports for new/edited code.
- Keep standard library imports above local imports.
- Be aware sibling imports currently assume root/PYTHONPATH setup.

### Formatting and typing
- No formatter is configured; match surrounding style.
- Avoid formatting-only churn.
- Type hints are sparse; add narrowly when they improve clarity for touched code.

## Error Handling
- New config/API path uses exceptions (for example `ConfigValidationError`, `ValueError`).
- Legacy validators in `sources/error_checks.py` return error-code lists (`[False]` means success).
- Do not silently swallow errors.
- When extending behavior, fail fast with clear messages for invalid config/state.

## Config Conventions
- Keep tunable business parameters in config files under `setup/`.
- YAML is preferred when adding new config flows; JSON remains supported.
- Validate immediately after loading; no silent defaults for required keys.
- Preserve canonical key names expected downstream (for example `daily_proba`).
- Reference canonical fixtures:
  - `setup/menu_setup_R1.yaml`
  - `setup/behavior_setup_r1.yaml`
  - `setup/population_setup_R1.yaml`
  - `setup/expenses_setup_R1.yaml`

## Known Sharp Edges
- `sources/main.py` does not execute simulation on import anymore; execution is under `if __name__ == '__main__':`.
- Bare sibling imports in `sources/` can fail if `PYTHONPATH` is not configured or working dir is unexpected.
- Time-series logic assumes hourly resolution and full-year coverage in key paths.
- `sources/error_checks.py` follows legacy return-code validation style.
- No formal packaging/build/lint/typecheck pipeline is defined.

## Guidance From `.github/copilot-instructions.md`
Reflect these rules in your work:
- Work methodically and verify assumptions.
- Be explicit about limits and what was not verified.
- Build context before changing code.
- Prefer modular design and remove obsolete code when appropriate.
- Keep tunable values in configuration rather than code.
- Validate configuration immediately after loading it.
- Keep secrets out of code and config.
- Use timeouts for terminal commands.
- Put instructions/runbooks in dated `instructions/YYYY-MM-DD/` markdown files.

## Practical Do / Do Not
- Do make small, surgical changes consistent with current procedural/numerical style.
- Do use `config_loader` + `simulation_api` for new callable workflows.
- Do run targeted tests first (`fast`, `simulation`, or `properties`) before broader validation.
- Do report validation limits clearly, especially for stochastic checks.
- Do not assume package-style imports currently work without environment setup.
- Do not rename config keys casually; downstream code expects exact spelling.
- Do not introduce hidden defaults for required configuration.
- Do not add secrets or credential-like values to source or configs.

## When To Update This File
Update `AGENTS.md` whenever dependencies, official commands, source layout, API contract, config schema, or repo rules change.
