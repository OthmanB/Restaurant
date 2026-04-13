# Code Audit Report - Restaurant Modeling Engine

Date: 2026-04-13  
Scope: `sources/*.py`, `setup/*.json`, and alignment with the revised theory document (`docs/tex/report.tex`)  
Goal: assess readiness for two target uses:
1. **Standalone forward modeling** (configuration-driven, YAML-preferred)
2. **Callable synthetic-data generator** for ML training and parameter optimization

---

## 1) Executive Summary

The codebase is a strong research prototype with valuable domain logic, but it is not yet organized as a robust modeling engine. The main blockers are architectural: import-time execution, mixed concerns (compute + plotting + file I/O), ad-hoc error handling (`print` + `exit`), weak schema validation, and uncontrolled randomness.

The good news is that the core mathematical pieces are mostly reusable. With a focused refactor (not a rewrite), this project can become both:
- a reliable standalone model runner, and
- a reusable simulation API for synthetic-data generation.

**Priority recommendation:** do a phased hardening of interfaces and config/validation first, then expose a clean simulation API, then optimize throughput for batch generation.

---

## 2) Current Architecture (Observed)

### Core modules
- `sources/main.py`: orchestration, config loading, aggregation, plotting, file output
- `sources/functions_population.py`: population and temporal modulation models (`daily_base_fct`, `weekly_fct`, `yearly_fct`, `compute_Nc`)
- `sources/functions_income.py`: menu combinations, expected revenues/costs, payment/staff/recurring expenses
- `sources/error_checks.py`: validations
- `sources/misc.py`: integration, summation, combinatorics helpers
- `sources/tests.py`: mainly visual/manual checks

### Data/config
- Canonical config files in `setup/` are JSON and consumed directly by `main.py` and helper functions.

### Main flow
1. Load configs from JSON
2. Compute yearly `Nc(t)` split into weekday/weekend
3. Integrate to day/week/month
4. Compute menu-driven revenues/expenses
5. Plot and write figures

---

## 3) High-Impact Findings

## 3.1 Critical blockers

1. **Import-time execution in `main.py`**  
   `main(...)` is called at module bottom unguarded. Importing the module can run the full pipeline and write files.

2. **Error handling uses process exits**  
   Multiple modules use `print(...)` + `exit()`/`exit(-1)` in library-level logic. This prevents safe embedding in larger programs.

3. **Compute and side effects are tightly coupled**  
   Core orchestration intermixes numerical computation, plotting, and filesystem writes. This blocks clean API reuse.

4. **No centralized config schema validation**  
   Configs are loaded and indexed directly. Missing/wrong keys fail late and noisily.

5. **Randomness is not reproducibility-safe in expense logic**  
   `expenses_fees` uses random sampling without a controllable RNG contract at API boundary.

## 3.2 Major correctness / maintainability issues

1. **Duplicate function definition** in `error_checks.py` (`check_time_is_24h` defined twice).
2. **Mutable default argument bug risk** in `misc.step(..., result=[])`.
3. **Service consistency check is order-sensitive** (`avail_services != service_list`) and can false-fail.
4. **Brittle float equality checks** in validators.
5. **Wildcard imports in `main.py`** hide dependencies and increase coupling.

## 3.3 Config/schema quality issues

1. Inconsistent key spellings and drift:
   - `payement_proba` vs canonical `payment_proba`
   - `recuring_period` vs canonical `recurring_period`
2. Non-typed placeholder values in configs (e.g., explanatory strings where numeric values are expected later).
3. No explicit constraints for ranges (probabilities in [0,1], hours in [0,24], etc.).

---

## 4) Use-case Readiness Assessment

## A) Standalone forward modeling (YAML-driven preferred)

### Current readiness
- Partially ready for direct script usage only.
- Not robust enough for production-like CLI use due to weak validation and abrupt exits.

### Gaps
- No CLI contract (arguments, modes, output targets)
- No canonical schema layer
- JSON-only loading path in practice
- Poor failure ergonomics

### What to add
- Thin CLI entrypoint + strict loader/validator
- YAML-first config support with JSON backward compatibility
- clean output modes (compute-only, plots-only, full-run)

## B) Callable synthetic-data generator (ML/optimization)

### Current readiness
- Core math functions are close to reusable.
- System is not yet API-safe due to side effects and error contracts.

### Gaps
- No stable public simulation API
- No deterministic RNG protocol across pipeline
- No batch-generation interface
- No metadata/provenance standard for generated outputs

### What to add
- `simulate(...)` and `simulate_batch(...)` pure API
- explicit `rng`/`seed` injection and stream management
- return structured arrays + metadata, not plots/files by default

---

## 5) Recommended Target Design

## 5.1 Separation of concerns

Split into three layers:

1. **Core model layer (pure)**
   - Population/time functions
   - Revenue/expense transforms
   - No plotting, no file I/O, no prints, no exits

2. **Application layer (orchestration)**
   - Load + validate config
   - Call pure functions
   - Build output bundles (arrays/tables/metadata)

3. **Interface layer (CLI/API)**
   - CLI for standalone runs
   - Python API for embedding and batch generation

## 5.2 API proposals

```python
def simulate_year(menu_cfg, behavior_cfg, population_cfg, expenses_cfg, *, rng=None, seed=None):
    """Return deterministic structured outputs for one synthetic year."""


def simulate_batch(config_iterable, *, seed=None, n_runs=1, mode='deterministic'):
    """Vectorized/batched generation for ML datasets and optimization loops."""
```

### Expected returns
- time vectors
- `Nc` components
- revenue/expense/profit arrays (hour/day/week/month)
- metadata (`seed`, config hash, model version, assumptions)

---

## 6) YAML Migration Strategy (Safe and Incremental)

### Stage 0 (now): canonical schema and aliases
- Add central validator
- Normalize legacy keys to canonical keys (`payement_proba` -> `payment_proba`, etc.)
- Fail fast with readable error messages and key paths

### Stage 1: dual-format support
- Accept `.yaml/.yml` and `.json`
- Prefer YAML if both exist
- Emit deprecation warnings for legacy/non-canonical keys

### Stage 2: stabilize
- Move canonical setup files to YAML
- Keep JSON fallback for compatibility window

### Stage 3: enforce
- Remove fallback or keep only explicit migration mode

### Security
- Use safe YAML loading (`safe_load` equivalent)
- Never evaluate dynamic YAML constructors

---

## 7) Synthetic Data Generation Best Practices (Applied)

1. Use `numpy.random.default_rng(seed)` at API boundary
2. Pass RNG explicitly to stochastic routines
3. For parallel generation, derive independent streams deterministically
4. Persist metadata sidecars with every generated dataset
5. Support deterministic and stochastic modes explicitly
6. Include quick statistical sanity checks in generation pipeline

---

## 8) Refactoring Plan (Priority-Ordered)

## Phase 1 - Safety and Contracts (high priority)
1. Guard `main()` call under `if __name__ == '__main__':`
2. Replace `print+exit` with exceptions in core modules
3. Remove duplicate `check_time_is_24h`
4. Fix mutable default argument in `misc.step`
5. Replace wildcard imports with explicit imports

## Phase 2 - Config and Validation (high priority)
1. Add centralized config loader
2. Add strict schema validation and canonicalization
3. Add YAML support with backward-compatible JSON fallback

## Phase 3 - API Extraction (high priority)
1. Extract pure simulation pipeline from `main.py`
2. Add `simulate_year` and `simulate_batch`
3. Ensure plotting/writing are optional interface concerns

## Phase 4 - Reproducibility + ML workflow (medium priority)
1. Standardize RNG handling across full flow
2. Add metadata/provenance output
3. Add batch generation and parameter sweep helpers

## Phase 5 - Tests and Packaging (medium priority)
1. Add unit tests for deterministic behavior under fixed seed
2. Add schema tests for all canonical config files
3. Convert visual/manual tests into non-blocking automated checks
4. Add package metadata and documented public API

---

## 9) Concrete Improvement Candidates by File

### `sources/main.py`
- Move execution guard
- Split `compute` and `plot/save` paths
- Replace manual file open/close with context managers
- Add CLI arguments for modes and config paths

### `sources/functions_population.py`
- Keep as core math module
- Replace exit paths with exceptions
- tighten validation at function boundary

### `sources/functions_income.py`
- Refactor `expenses_fees` for deterministic RNG contract
- Replace error exits
- clean service-set validation (order-insensitive)

### `sources/error_checks.py`
- remove duplicate function
- return typed errors / raise exceptions
- use tolerance-aware numeric checks

### `sources/misc.py`
- fix mutable defaults
- consider replacing recursive combinatorics with bounded iterative approach for scale

### `sources/tests.py`
- remove blocking `plt.show()` from automated paths
- add reproducibility tests and schema tests

---

## 10) Risk Register

1. **Behavior changes from exception refactor**  
   Mitigation: wrap CLI with user-friendly exception handling and clear messages.

2. **YAML migration breaking old configs**  
   Mitigation: alias normalization + dual-format compatibility window.

3. **Synthetic generation drift after refactor**  
   Mitigation: lock golden test cases and compare reference outputs before/after.

4. **Combinatorial blow-up in menu combinations**  
   Mitigation: keep explicit hard limits and add documented approximations / sampling mode.

---

## 11) Suggested Implementation Order (Practical)

Week 1:
- Phase 1 + initial Phase 2 (guard, exceptions skeleton, validator skeleton)

Week 2:
- complete Phase 2 + Phase 3 extraction (`simulate_year`)

Week 3:
- Phase 4 reproducibility and batch mode

Week 4:
- Phase 5 test hardening and packaging polish

---

## 12) Final Recommendation

Do **not** rewrite from scratch. The domain equations and numerical core are already useful.  
Adopt a **stabilize-then-extract** strategy:

1. stabilize contracts (errors, configs, RNG),
2. extract a clean simulation API,
3. then scale for dataset generation and optimization loops.

This gives you a robust forward model and a reusable synthetic-data engine with minimal disruption to existing logic.


---

## 13) Phase 1 Execution Status (Implemented)

The following Phase 1 items have been executed in code:

1. Guarded runtime entrypoint:
   - `sources/main.py` now runs only under `if __name__ == '__main__':`.

2. Wildcard imports removed in `main.py`:
   - explicit imports now define concrete dependencies.

3. Core `print+exit` paths replaced by exceptions in active runtime code:
   - `sources/main.py`
   - `sources/functions_population.py`
   - `sources/functions_income.py`
   - terminal exit in `sources/error_checks.py` (`check_time_is_greater_than_period`).

4. Duplicate checker removed:
   - duplicate `check_time_is_24h` definition removed from `sources/error_checks.py`.

5. Mutable default fixed:
   - `sources/misc.py::step(..., result=None)` now initializes safely inside function.

Additional safety fixes made during runtime validation:
- scalar/array safety and truncation condition in `sources/functions_population.py::manyGauss_fct`
- optional array argument handling (`y=None`) in `sources/error_checks.py`
- output directory creation before figure writes in `sources/main.py`
- unbound local protection in `sources/functions_income.py::expenses_fees`

Validation evidence:
- bytecode compile check succeeded for modified modules
- runtime execution from `sources/` succeeded (non-fatal matplotlib warnings only)

Remaining roadmap (unchanged):
- Phase 2: centralized config loader, schema validation, YAML+JSON compatibility
- Phase 3: extract pure simulation API (`simulate_year`, `simulate_batch`)
- Phase 4: deterministic RNG protocol and metadata for dataset generation
- Phase 5: automated test hardening and packaging cleanup
