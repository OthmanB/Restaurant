# Synthetic Data API Quick Reference
**For the Restaurant Project - Immediate Actions**

---

## 1. Essential Pattern: Modern NumPy RNG (2 minutes to adopt)

### Current Issue in Your Code
If using `np.random.seed()` or `np.random.RandomState()` → **migrate to `Generator`**

### Minimal Change Required
```python
# OLD (don't use)
np.random.seed(42)
samples = np.random.normal(0, 1, size=1000)

# NEW (use this)
from numpy.random import default_rng
rng = default_rng(42)
samples = rng.normal(0, 1, size=1000)
```

**Why:** 2-10x faster, better statistics, supports parallel streams.

---

## 2. Seeding Strategy for Reproducibility

### Pattern for Single Script
```python
# At top of main.py or in YAML config
MASTER_SEED = 42

# In your functions
from numpy.random import default_rng

def compute_Nc(setup_file, seed=MASTER_SEED):
    rng = default_rng(seed)
    # Use rng.normal(), rng.poisson(), etc.
    return rng.poisson(lam=..., size=...)
```

### Pattern for Multiple Model Components
```python
# In main.py - create independent streams
from numpy.random import default_rng

MASTER_SEED = 42
rng = default_rng(MASTER_SEED)

# Spawn independent generators for each model component
population_rng = rng.spawn(1)[0]  # For functions_population.py
income_rng = rng.spawn(1)[0]      # For functions_income.py

# Pass these to your functions
daily_population = compute_daily_attendance(config, population_rng)
daily_revenue = compute_revenue(menu_config, income_rng)
```

**Key benefit:** Each component has independent RNG stream, no interference.

---

## 3. Parameter Sweep Pattern (for optimization loops)

### Minimal Implementation
```python
def test_menu_configurations(base_config, param_ranges, seed=42):
    """Test multiple parameter combinations with reproducibility."""
    from numpy.random import default_rng
    
    rng = default_rng(seed)
    results = []
    
    # Example: sweep over price ranges
    for price in param_ranges['prices']:
        # Each config gets independent RNG
        config_rng = rng.spawn(1)[0]
        
        # Generate synthetic customer data
        customers = generate_synthetic_customers(config_rng, n=1000)
        
        # Run simulation with this price
        revenue = simulate_restaurant(customers, price=price)
        results.append({'price': price, 'revenue': revenue})
    
    return results
```

---

## 4. Metadata Tracking (lightweight version)

### Add to Your Existing Functions
```python
def compute_Nc(setup_file, seed=42):
    """Compute daily customers - now with metadata."""
    from numpy.random import default_rng
    import json
    from datetime import datetime
    
    rng = default_rng(seed)
    
    # Your existing logic...
    Nc = rng.poisson(lam=expected_customers, size=365)
    
    # Add metadata tracking
    metadata = {
        'seed': seed,
        'timestamp': datetime.now().isoformat(),
        'config_file': setup_file,
        'n_days': len(Nc),
        'mean_customers': float(Nc.mean()),
        'std_customers': float(Nc.std())
    }
    
    return Nc, metadata
```

### Save Metadata with Plots
```python
# In your plotting code (main.py)
import json

# After generating plot
metadata = {
    'seed': MASTER_SEED,
    'config_files': {
        'menu': menu_config_path,
        'population': pop_config_path,
        'expenses': expense_config_path
    },
    'generation_date': datetime.now().isoformat()
}

# Save alongside plot
plot_path = 'data/plots/yearly_revenue.png'
meta_path = plot_path.replace('.png', '_meta.json')
with open(meta_path, 'w') as f:
    json.dump(metadata, f, indent=2)
```

---

## 5. Batch Generation for Large Simulations

### Memory-Efficient Pattern
```python
def simulate_yearly_revenue_batched(config, seed=42, batch_size=30):
    """Process year in monthly batches to reduce memory."""
    from numpy.random import default_rng
    
    rng = default_rng(seed)
    monthly_revenues = []
    
    for month in range(12):
        # Generate one month at a time
        days_in_month = batch_size
        daily_customers = rng.poisson(lam=config['mean_customers'], 
                                      size=days_in_month)
        
        # Process batch
        revenue = compute_monthly_revenue(daily_customers, config)
        monthly_revenues.append(revenue)
    
    return np.array(monthly_revenues)
```

---

## 6. Config Integration (YAML-based seed)

### Add to Your YAML Files
```yaml
# setup/simulation_config.yaml
simulation:
  seed: 42  # Master seed for reproducibility
  n_iterations: 1000
  
population:
  seed_offset: 0  # Will use master_seed + 0
  
income:
  seed_offset: 1  # Will use master_seed + 1
```

### Load in Code
```python
import yaml

with open('setup/simulation_config.yaml') as f:
    config = yaml.safe_load(f)

master_seed = config['simulation']['seed']
pop_seed = master_seed + config['population']['seed_offset']
income_seed = master_seed + config['income']['seed_offset']
```

---

## 7. Validation Utility

### Add to tests.py
```python
def test_reproducibility():
    """Verify same seed produces identical results."""
    from numpy.random import default_rng
    import numpy.testing as npt
    
    seed = 12345
    
    # Generate twice
    rng1 = default_rng(seed)
    data1 = rng1.normal(size=1000)
    
    rng2 = default_rng(seed)
    data2 = rng2.normal(size=1000)
    
    # Should be exactly equal
    npt.assert_array_equal(data1, data2)
    print("✓ Reproducibility test passed")

def test_independence():
    """Verify spawned RNGs produce different streams."""
    from numpy.random import default_rng
    
    parent = default_rng(42)
    children = parent.spawn(3)
    
    samples = [rng.random(100) for rng in children]
    
    # Check all different
    for i in range(len(samples)):
        for j in range(i+1, len(samples)):
            assert not np.allclose(samples[i], samples[j])
    
    print("✓ Independence test passed")
```

---

## 8. Immediate Action Items

**Priority 1 (Today):**
1. Add `from numpy.random import default_rng` to functions using randomness
2. Replace `np.random.seed()` → `rng = default_rng(seed)`
3. Replace `np.random.function()` → `rng.function()`

**Priority 2 (This Week):**
1. Add `seed` parameter to YAML configs
2. Add metadata output to key functions
3. Add reproducibility tests to `tests.py`

**Priority 3 (Next Sprint):**
1. Implement spawn pattern for independent model components
2. Add batch generation for parameter sweeps
3. Save metadata alongside plot outputs

---

## 9. Function Signature Template

Use this template for any new generator functions:

```python
def generate_synthetic_X(
    n_samples: int,
    *,  # Force keyword-only
    random_state: int | None = None,
    **params
) -> tuple[np.ndarray, dict]:
    """
    Generate synthetic X data.
    
    Parameters
    ----------
    n_samples : int
        Number of samples
    random_state : int or None
        Seed for reproducibility
    **params : dict
        Model-specific parameters
        
    Returns
    -------
    data : ndarray
        Generated data
    metadata : dict
        Generation metadata (seed, params, timestamp)
    """
    from numpy.random import default_rng
    from datetime import datetime
    
    rng = default_rng(random_state)
    
    # Generation logic
    data = rng.normal(size=n_samples)
    
    # Metadata
    metadata = {
        'seed': random_state,
        'timestamp': datetime.now().isoformat(),
        'n_samples': n_samples,
        'params': params
    }
    
    return data, metadata
```

---

## 10. Common Distributions (Quick Reference)

```python
from numpy.random import default_rng
rng = default_rng(42)

# Uniform [0, 1)
rng.random(size=100)

# Normal (mean, std)
rng.normal(loc=10.0, scale=2.0, size=100)

# Poisson (customers per day)
rng.poisson(lam=50, size=365)

# Integer range [low, high)
rng.integers(low=0, high=10, size=100)

# Choice from array
rng.choice(['menu1', 'menu2', 'menu3'], size=100)

# Exponential (time between events)
rng.exponential(scale=1.0, size=100)

# Binomial (n trials, p success)
rng.binomial(n=10, p=0.3, size=100)
```

---

**Questions? See full reference:** `synthetic_data_api_patterns_2026-04-13.md`
