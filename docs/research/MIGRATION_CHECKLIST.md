# Migration Checklist: Synthetic Data API Modernization
**Restaurant Project - April 2026**

---

## Current State Analysis

Based on AGENTS.md and repository structure:
- **Language:** Python 3.10+
- **Dependencies:** NumPy, SciPy, Matplotlib
- **Structure:** Flat `sources/` modules
- **Config:** JSON files in `setup/`
- **Randomness:** Status unknown (likely needs audit)

---

## Migration Status: Before → After

### ✅ **Phase 1: Core RNG Upgrade** (Effort: 1-2 hours)

| Aspect | Current (likely) | Target | Status |
|--------|------------------|--------|---------|
| RNG API | `np.random.seed()` | `default_rng(seed)` | ⬜ TODO |
| Random calls | `np.random.normal()` | `rng.normal()` | ⬜ TODO |
| Seeding location | Hardcoded or missing | YAML config | ⬜ TODO |
| Generator scope | Global state | Function-local | ⬜ TODO |

**Files to modify:**
- `sources/functions_population.py` - attendance models
- `sources/functions_income.py` - revenue simulations
- `sources/main.py` - orchestration
- `sources/tests.py` - test utilities

**Code pattern to find:**
```bash
grep -r "np.random\." sources/ --include="*.py"
grep -r "random.seed" sources/ --include="*.py"
```

---

### ✅ **Phase 2: Reproducibility & Config** (Effort: 2-3 hours)

| Aspect | Current | Target | Status |
|--------|---------|--------|---------|
| Seed in config | Not in JSON | Add to all setup files | ⬜ TODO |
| Seed validation | None | Check at load time | ⬜ TODO |
| Metadata output | None | JSON sidecar files | ⬜ TODO |
| Reproducibility tests | Limited | Full test coverage | ⬜ TODO |

**Config files to update:**
- `setup/menu_setup_R1.json` → add `"seed": 42`
- `setup/behavior_setup_r1.json` → add `"seed": 43`
- `setup/population_setup_R1.json` → add `"seed": 44`
- `setup/expenses_setup_R1.json` → add `"seed": 45`

**Example addition:**
```json
{
  "simulation": {
    "seed": 42,
    "description": "Master seed for reproducible results"
  },
  ...existing config...
}
```

---

### ✅ **Phase 3: Independent Streams** (Effort: 1 hour)

| Aspect | Current | Target | Status |
|--------|---------|--------|---------|
| Model coupling | Shared global RNG | Independent per model | ⬜ TODO |
| Parallel safety | Not guaranteed | Spawn-based streams | ⬜ TODO |
| Component isolation | None | Generator per component | ⬜ TODO |

**Implementation in `main.py`:**
```python
from numpy.random import default_rng

def main(test_menu_setup_file=None, test_behavior_setup_file=None, ...):
    # Load configs (existing code)
    menu_cfg = json.load(open(test_menu_setup_file or 'setup/menu_setup_R1.json'))
    
    # NEW: Create master RNG and spawn children
    master_seed = menu_cfg.get('simulation', {}).get('seed', 42)
    master_rng = default_rng(master_seed)
    
    # Spawn independent generators
    population_rng, income_rng, expense_rng = master_rng.spawn(3)
    
    # Pass to model functions
    daily_attendance = compute_attendance(population_cfg, rng=population_rng)
    daily_revenue = compute_revenue(menu_cfg, rng=income_rng)
    # ...
```

---

### ✅ **Phase 4: Metadata & Validation** (Effort: 2-3 hours)

| Aspect | Current | Target | Status |
|--------|---------|--------|---------|
| Plot metadata | None | JSON sidecar | ⬜ TODO |
| Generation logs | print() statements | Structured logging | ⬜ TODO |
| Statistical validation | Manual inspection | Automated checks | ⬜ TODO |
| Benchmark tracking | None | Timing utilities | ⬜ TODO |

**Add to plotting code:**
```python
# In main.py after plot generation
import json
from datetime import datetime

metadata = {
    'generation_date': datetime.now().isoformat(),
    'master_seed': master_seed,
    'configs': {
        'menu': test_menu_setup_file,
        'population': test_population_setup_file,
        'behavior': test_behavior_setup_file,
        'expenses': test_expenses_setup_file
    },
    'statistics': {
        'mean_daily_revenue': float(np.mean(daily_revenues)),
        'std_daily_revenue': float(np.std(daily_revenues)),
        'total_annual_profit': float(annual_profit)
    }
}

# Save alongside plot
plot_path = 'data/plots/yearly_results.png'
with open(plot_path.replace('.png', '_meta.json'), 'w') as f:
    json.dump(metadata, f, indent=2)
```

---

### ✅ **Phase 5: Advanced Features** (Effort: 3-4 hours, optional)

| Aspect | Current | Target | Status |
|--------|---------|--------|---------|
| Parameter sweeps | Manual reruns | Vectorized batch API | ⬜ TODO |
| Batch processing | Load all in memory | Iterator-based | ⬜ TODO |
| Parallel execution | None | ProcessPoolExecutor | ⬜ TODO |
| Checkpointing | None | Save/restore RNG state | ⬜ TODO |

---

## File-by-File Audit Checklist

### `sources/functions_population.py`
- [ ] Audit all uses of randomness (likely in attendance models)
- [ ] Add `rng` parameter to relevant functions
- [ ] Replace global random calls with `rng.method()`
- [ ] Add docstring parameter documentation
- [ ] Add unit test for reproducibility

**Expected changes:**
```python
# BEFORE (hypothetical)
def compute_daily_attendance(config):
    base = config['mean_customers']
    noise = np.random.normal(0, config['std_customers'], size=365)
    return base + noise

# AFTER
def compute_daily_attendance(config, rng=None):
    """Compute daily attendance with reproducible randomness.
    
    Parameters
    ----------
    config : dict
        Configuration with 'mean_customers', 'std_customers'
    rng : numpy.random.Generator, optional
        Random number generator. If None, creates from config seed.
    """
    if rng is None:
        from numpy.random import default_rng
        rng = default_rng(config.get('seed', 42))
    
    base = config['mean_customers']
    noise = rng.normal(0, config['std_customers'], size=365)
    return base + noise
```

### `sources/functions_income.py`
- [ ] Audit menu combination sampling logic
- [ ] Add `rng` parameter to revenue functions
- [ ] Replace random choice/sampling with `rng.choice()`
- [ ] Add reproducibility test

### `sources/main.py`
- [ ] Add master seed initialization
- [ ] Implement RNG spawning for components
- [ ] Add metadata collection
- [ ] Save metadata with plots

### `sources/tests.py`
- [ ] Add `test_rng_reproducibility()`
- [ ] Add `test_rng_independence()`
- [ ] Add `test_statistical_properties()`
- [ ] Verify all tests pass with same seed

### `sources/misc.py`
- [ ] Audit utility functions for randomness
- [ ] Add RNG utilities if needed

### `sources/error_checks.py`
- [ ] Add seed validation helper
- [ ] Add RNG state validation

---

## Config File Updates

### Template for JSON configs
```json
{
  "simulation": {
    "seed": 42,
    "version": "2.0",
    "description": "Reproducible simulation with explicit RNG seeding"
  },
  
  "__comment": "Existing configuration below",
  
  "menu": { ... },
  "population": { ... }
}
```

### Validation helper (add to `error_checks.py`)
```python
def validate_seed(config: dict, config_name: str) -> int:
    """Validate and extract seed from config.
    
    Returns
    -------
    seed : int
        Valid seed value
        
    Raises
    ------
    ValueError
        If seed missing or invalid
    """
    if 'simulation' not in config:
        raise ValueError(f"{config_name}: Missing 'simulation' section")
    
    if 'seed' not in config['simulation']:
        raise ValueError(f"{config_name}: Missing 'seed' in simulation config")
    
    seed = config['simulation']['seed']
    
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"{config_name}: seed must be non-negative integer, got {seed}")
    
    return seed
```

---

## Testing Strategy

### Reproducibility Test Suite (add to `tests.py`)
```python
def test_population_reproducibility():
    """Test that population model produces identical results with same seed."""
    from sources.functions_population import compute_daily_attendance
    from numpy.random import default_rng
    import numpy.testing as npt
    
    config = {'mean_customers': 100, 'std_customers': 10, 'seed': 12345}
    
    rng1 = default_rng(12345)
    result1 = compute_daily_attendance(config, rng=rng1)
    
    rng2 = default_rng(12345)
    result2 = compute_daily_attendance(config, rng=rng2)
    
    npt.assert_array_equal(result1, result2)
    print("✓ Population model reproducibility verified")

def test_income_reproducibility():
    """Test that income model produces identical results with same seed."""
    from sources.functions_income import compute_daily_revenue
    from numpy.random import default_rng
    import numpy.testing as npt
    
    config = {'menu': {...}, 'seed': 12345}
    
    rng1 = default_rng(12345)
    result1 = compute_daily_revenue(config, rng=rng1)
    
    rng2 = default_rng(12345)
    result2 = compute_daily_revenue(config, rng=rng2)
    
    npt.assert_array_equal(result1, result2)
    print("✓ Income model reproducibility verified")

def test_component_independence():
    """Test that spawned RNGs for different components are independent."""
    from numpy.random import default_rng
    
    master_rng = default_rng(42)
    pop_rng, inc_rng = master_rng.spawn(2)
    
    pop_samples = pop_rng.random(1000)
    inc_samples = inc_rng.random(1000)
    
    # Should be statistically independent (correlation near 0)
    correlation = np.corrcoef(pop_samples, inc_samples)[0, 1]
    assert abs(correlation) < 0.1, f"Streams not independent: r={correlation}"
    print("✓ Component independence verified")

def test_full_pipeline_reproducibility():
    """Test that entire simulation is reproducible."""
    from sources.main import main
    
    # Run twice with same configs
    result1 = main(
        test_menu_setup_file='setup/menu_setup_R1.json',
        test_behavior_setup_file='setup/behavior_setup_r1.json',
        test_population_setup_file='setup/population_setup_R1.json',
        test_expenses_setup_file='setup/expenses_setup_R1.json'
    )
    
    result2 = main(
        test_menu_setup_file='setup/menu_setup_R1.json',
        test_behavior_setup_file='setup/behavior_setup_r1.json',
        test_population_setup_file='setup/population_setup_R1.json',
        test_expenses_setup_file='setup/expenses_setup_R1.json'
    )
    
    # Compare key metrics
    assert np.allclose(result1['annual_profit'], result2['annual_profit'])
    print("✓ Full pipeline reproducibility verified")
```

---

## Rollout Plan

### Week 1: Foundation
- [ ] Day 1: Audit current code for random number usage
- [ ] Day 2: Implement Phase 1 (core RNG upgrade)
- [ ] Day 3: Add seeds to config files (Phase 2)
- [ ] Day 4: Add reproducibility tests
- [ ] Day 5: Verify all tests pass, commit changes

### Week 2: Enhancement
- [ ] Day 1: Implement independent streams (Phase 3)
- [ ] Day 2-3: Add metadata tracking (Phase 4)
- [ ] Day 4: Add statistical validation
- [ ] Day 5: Documentation update, close migration

### (Optional) Week 3: Advanced
- [ ] Implement parameter sweep utilities
- [ ] Add batch processing support
- [ ] Add benchmark tracking
- [ ] Performance optimization

---

## Success Criteria

✅ **Migration Complete When:**
1. All functions accept `rng` parameter
2. No global `np.random.*` calls remain
3. All configs have `seed` field
4. Reproducibility tests pass
5. Metadata saved with all outputs
6. Documentation updated (README, AGENTS.md)

✅ **Verification Commands:**
```bash
# No legacy random calls
! grep -r "np.random\.[a-z]" sources/ --include="*.py" | grep -v "default_rng"

# All tests pass
python3 sources/tests.py

# Reproducibility verified
python3 -c "from sources.tests import test_full_pipeline_reproducibility; test_full_pipeline_reproducibility()"
```

---

## Resources

- Full API reference: `synthetic_data_api_patterns_2026-04-13.md`
- Quick start: `QUICK_REFERENCE.md`
- NumPy docs: https://numpy.org/doc/stable/reference/random/index.html

---

**Status Legend:**
- ⬜ TODO - Not started
- 🔄 IN PROGRESS - Work underway  
- ✅ DONE - Completed and tested
- ⚠️ BLOCKED - Waiting on dependency

**Last Updated:** 2026-04-13
