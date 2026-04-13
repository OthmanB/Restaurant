# Synthetic Data Generation API Research
**Date:** April 13, 2026  
**Purpose:** Best practices for ML dataset creation & parameter optimization in numerical modeling contexts

---

## 📚 Document Index

### 1. **QUICK_REFERENCE.md** - Start Here ⭐
**Read this first (10 min)**
- Essential patterns for immediate use
- Minimal code examples
- Common distributions reference
- Priority action items

**Use when:** You need to add synthetic data generation NOW

---

### 2. **synthetic_data_api_patterns_2026-04-13.md** - Comprehensive Guide
**Deep dive (30-45 min)**
- Complete API design patterns with examples
- Reproducibility strategies (seeding, spawning, parallel streams)
- Output formats & metadata tracking
- Vectorized batch generation
- Distribution libraries
- Testing patterns
- Benchmarking utilities

**Use when:** Designing new generator APIs or refactoring existing code

---

### 3. **MIGRATION_CHECKLIST.md** - Restaurant Project Specific
**Implementation roadmap (reference during work)**
- Current state → target state comparison
- File-by-file audit checklist
- Config file update templates
- Testing strategy
- Week-by-week rollout plan
- Success criteria & verification

**Use when:** Implementing changes in the Restaurant codebase

---

## 🎯 Key Recommendations (TL;DR)

### For Immediate Use
```python
# Modern NumPy pattern (use this)
from numpy.random import default_rng

rng = default_rng(42)  # Reproducible seed
data = rng.normal(loc=0, scale=1, size=1000)
```

### For Parallel/Independent Streams
```python
# Spawn independent generators
parent = default_rng(42)
child_rngs = parent.spawn(10)  # 10 independent streams
```

### For Metadata Tracking
```python
# Return data + metadata
def generate(n, seed=42):
    rng = default_rng(seed)
    data = rng.normal(size=n)
    metadata = {'seed': seed, 'n': n, 'timestamp': ...}
    return data, metadata
```

---

## 📊 Research Sources

**Official Documentation:**
- NumPy Random API: https://numpy.org/doc/stable/reference/random/
- NumPy Generator: https://numpy.org/doc/stable/reference/random/generator.html
- NumPy Parallel: https://numpy.org/doc/stable/reference/random/parallel.html
- Scikit-learn Datasets: https://scikit-learn.org/stable/datasets/
- SciPy Stats: https://docs.scipy.org/doc/scipy/reference/stats.html

**Key Concepts:**
- **Generator class**: Modern NumPy RNG (v1.17+), 2-10x faster than RandomState
- **PCG64**: Default bit generator, excellent statistical properties
- **SeedSequence spawning**: Guaranteed independent streams for parallel work
- **128-bit seeds**: Use `secrets.randbits(128)` for high-quality entropy

---

## 🏗️ Repository Context

**Target Project:** Restaurant analytical model (`/Users/obenomar/Trade/Restaurant`)

**Current Structure:**
```
Restaurant/
├── sources/
│   ├── functions_population.py  # Attendance models
│   ├── functions_income.py      # Revenue models  
│   ├── main.py                  # Orchestration
│   ├── tests.py                 # Testing utilities
│   ├── misc.py                  # Utilities
│   └── error_checks.py          # Validation
├── setup/                        # JSON configs
├── data/plots/                   # Output visualizations
└── docs/research/               # This directory
```

**Dependencies:** NumPy, SciPy, Matplotlib (no external ML frameworks)

---

## ⚡ Quick Start (5 minutes)

1. **Read:** `QUICK_REFERENCE.md` sections 1-2
2. **Try:** Copy the "Essential Pattern" code into Python REPL
3. **Audit:** Check your code for `np.random.seed()` or `np.random.normal()` calls
4. **Migrate:** Replace with `default_rng()` pattern
5. **Test:** Verify reproducibility with same seed

---

## 📈 Implementation Priority

**Priority 1 (Critical):**
- [ ] Migrate to `default_rng()` API
- [ ] Add explicit seeding parameters
- [ ] Verify reproducibility

**Priority 2 (Important):**
- [ ] Add seeds to YAML/JSON configs
- [ ] Implement metadata tracking
- [ ] Add reproducibility tests

**Priority 3 (Optimization):**
- [ ] Implement independent streams (spawn)
- [ ] Add batch generation for sweeps
- [ ] Add statistical validation

---

## 🔬 Use Cases Covered

1. ✅ **Single script reproducibility** - Same results every run
2. ✅ **Multi-component models** - Independent RNG per module
3. ✅ **Parameter sweeps** - Vectorized configuration testing
4. ✅ **Parallel processing** - Safe concurrent generation
5. ✅ **Batch processing** - Memory-efficient large datasets
6. ✅ **Metadata tracking** - Full provenance for results
7. ✅ **Statistical validation** - Verify generated distributions
8. ✅ **Benchmarking** - Performance measurement utilities

---

## 🚀 Next Steps

### For New Users
1. Read `QUICK_REFERENCE.md`
2. Try examples in Python REPL
3. Apply patterns to one function
4. Verify with reproducibility test

### For Restaurant Project Implementation
1. Read `MIGRATION_CHECKLIST.md`
2. Run code audit commands
3. Start with Phase 1 (RNG upgrade)
4. Follow week-by-week plan
5. Check success criteria

### For Deep Understanding
1. Read full `synthetic_data_api_patterns_2026-04-13.md`
2. Study official NumPy documentation
3. Experiment with spawn patterns
4. Implement advanced features (Phase 5)

---

## 📝 Notes

- **No heavy platforms:** These patterns work with pure NumPy/SciPy (no TensorFlow/PyTorch/Dask)
- **Small team friendly:** Minimal boilerplate, gradual adoption path
- **Production ready:** Based on NumPy 1.17+ stable API
- **Backward compatible:** Can coexist with legacy code during migration

---

## ❓ FAQ

**Q: Why not use `np.random.seed()`?**  
A: Global state makes parallel execution unsafe, harder to test, slower performance.

**Q: Do I need to change all code at once?**  
A: No! Gradual migration is fine. Start with new code, migrate legacy incrementally.

**Q: What if I'm using RandomState?**  
A: It still works, but Generator is 2-10x faster with better statistical properties.

**Q: How do I ensure parallel workers don't overlap?**  
A: Use `spawn()` or prepend worker IDs to seed lists: `[worker_id, root_seed]`

**Q: Can I use this for ML training loops?**  
A: Yes! Scikit-learn datasets + NumPy Generator patterns work seamlessly.

---

**Questions or issues?** Check the comprehensive guide or NumPy documentation.

**Last Updated:** 2026-04-13
