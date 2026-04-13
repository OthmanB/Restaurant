# Synthetic Data Generation API Best Practices
**Research Date:** 2026-04-13  
**Context:** ML dataset creation & parameter optimization loops for numerical modeling  
**Target:** Small scientific Python teams using NumPy/SciPy

---

## 1. Core API Design Patterns

### 1.1 Function Signature Standards

**Recommended pattern from NumPy Generator:**
```python
def generate_synthetic_data(
    n_samples: int,
    *,  # Force keyword-only arguments
    random_state: int | np.random.Generator | None = None,
    size: int | tuple[int, ...] | None = None,
    dtype: np.dtype = np.float64,
    **params  # Distribution-specific parameters
) -> np.ndarray | dict[str, np.ndarray]:
    """
    Generate synthetic dataset with explicit controls.
    
    Parameters
    ----------
    n_samples : int
        Number of samples to generate
    random_state : int, Generator, or None
        Seed or generator instance for reproducibility
    size : int or tuple, optional
        Output array shape. If None, returns (n_samples,)
    dtype : dtype
        Output data type
    **params : dict
        Distribution/model-specific parameters
        
    Returns
    -------
    data : ndarray or dict of ndarrays
        Generated synthetic data
    """
    pass
```

**Key principles:**
- Use keyword-only args (after `*`) for everything except primary required params
- Accept both seeds (int) and Generator instances via `random_state`
- Explicit `dtype` parameter for numerical precision control
- Return structured output (dict) when generating multiple arrays

---

## 2. Reproducibility & Seeding Strategies

### 2.1 Recommended Seeding Pattern (NumPy v1.17+)

```python
import numpy as np
from numpy.random import Generator, default_rng

class SyntheticDataGenerator:
    """Stateful generator with spawn support for parallel work."""
    
    def __init__(self, seed: int | None = None):
        """Initialize with high-entropy seed."""
        if seed is None:
            import secrets
            seed = secrets.randbits(128)  # 128-bit entropy
        self.rng = default_rng(seed)
        self._seed = seed
    
    def generate_batch(self, n_samples: int, **params) -> np.ndarray:
        """Generate one batch using internal RNG state."""
        return self.rng.normal(size=(n_samples, params.get('n_features', 10)))
    
    def spawn_child(self, n_children: int = 1) -> list['SyntheticDataGenerator']:
        """Create independent child generators for parallel processing.
        
        Uses SeedSequence spawning for guaranteed stream independence.
        """
        child_rngs = self.rng.spawn(n_children)
        return [self.__class__.__new__(self.__class__) 
                for rng in child_rngs]
```

**Why this pattern:**
- **`default_rng()`**: Uses PCG64 (faster, better statistical properties than MT19937)
- **`secrets.randbits(128)`**: Prevents weak human-chosen seeds
- **`spawn()`**: Creates independent streams without coordination (critical for parallel loops)

### 2.2 Parallel Generation Pattern

```python
from concurrent.futures import ProcessPoolExecutor

def generate_parallel_batches(
    n_batches: int,
    samples_per_batch: int,
    root_seed: int,
    **params
) -> list[np.ndarray]:
    """Generate batches in parallel with independent RNG streams."""
    
    # Create parent generator
    parent_rng = default_rng(root_seed)
    
    # Spawn independent child generators
    child_rngs = parent_rng.spawn(n_batches)
    
    # Parallel execution
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(_generate_worker, rng, samples_per_batch, params)
            for rng in child_rngs
        ]
        batches = [f.result() for f in futures]
    
    return batches

def _generate_worker(rng: Generator, n_samples: int, params: dict) -> np.ndarray:
    """Worker function with independent RNG."""
    return rng.normal(size=(n_samples, params['n_features']))
```

**Alternative for coordinated workers:**
```python
def worker_with_id(root_seed: int, worker_id: int, **params):
    """Use list-of-integers seeding for deterministic worker streams."""
    # Prepend worker_id for safety when mixing with spawn()
    rng = default_rng([worker_id, root_seed])
    return rng.normal(size=(params['n_samples'], params['n_features']))
```

---

## 3. Output Formats & Metadata Tracking

### 3.1 Structured Output Pattern

```python
from dataclasses import dataclass, asdict
from typing import Any
import json

@dataclass
class SyntheticDataset:
    """Container for synthetic data with full provenance."""
    
    # Data arrays
    X: np.ndarray
    y: np.ndarray | None = None
    
    # Metadata
    generator_class: str = ""
    generator_version: str = ""
    seed: int | None = None
    generation_params: dict[str, Any] = None
    timestamp: str = ""
    n_samples: int = 0
    n_features: int = 0
    
    def to_dict(self) -> dict:
        """Export with NumPy arrays converted to lists."""
        d = asdict(self)
        d['X'] = self.X.tolist() if self.X is not None else None
        d['y'] = self.y.tolist() if self.y is not None else None
        return d
    
    def save(self, filepath: str):
        """Save as NPZ with JSON metadata sidecar."""
        # Save arrays efficiently
        np.savez_compressed(
            filepath,
            X=self.X,
            y=self.y if self.y is not None else np.array([])
        )
        
        # Save metadata
        meta = {
            'generator_class': self.generator_class,
            'generator_version': self.generator_version,
            'seed': self.seed,
            'generation_params': self.generation_params,
            'timestamp': self.timestamp,
            'n_samples': self.n_samples,
            'n_features': self.n_features
        }
        with open(f"{filepath}_meta.json", 'w') as f:
            json.dump(meta, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'SyntheticDataset':
        """Load from NPZ + JSON metadata."""
        data = np.load(filepath)
        with open(f"{filepath}_meta.json") as f:
            meta = json.load(f)
        
        return cls(
            X=data['X'],
            y=data['y'] if data['y'].size > 0 else None,
            **meta
        )
```

### 3.2 Minimal Metadata (for quick iterations)

```python
def generate_with_metadata(
    n_samples: int,
    random_state: int,
    **params
) -> tuple[np.ndarray, dict]:
    """Return data + minimal metadata dict."""
    rng = default_rng(random_state)
    X = rng.normal(size=(n_samples, params.get('n_features', 10)))
    
    metadata = {
        'seed': random_state,
        'n_samples': n_samples,
        'params': params,
        'timestamp': np.datetime64('now').astype(str)
    }
    
    return X, metadata
```

---

## 4. Vectorized Batch Generation

### 4.1 Efficient Batch API

```python
class BatchGenerator:
    """Memory-efficient batch generation for large datasets."""
    
    def __init__(self, total_samples: int, batch_size: int, seed: int):
        self.total_samples = total_samples
        self.batch_size = batch_size
        self.rng = default_rng(seed)
        self.n_batches = int(np.ceil(total_samples / batch_size))
    
    def __iter__(self):
        """Iterate over batches without storing full dataset."""
        for i in range(self.n_batches):
            start = i * self.batch_size
            end = min(start + self.batch_size, self.total_samples)
            batch_size = end - start
            
            yield self._generate_batch(batch_size, batch_idx=i)
    
    def _generate_batch(self, n: int, batch_idx: int) -> dict:
        """Generate single batch with index tracking."""
        return {
            'X': self.rng.normal(size=(n, 10)),
            'y': self.rng.integers(0, 2, size=n),
            'batch_idx': batch_idx,
            'indices': np.arange(batch_idx * self.batch_size, 
                                batch_idx * self.batch_size + n)
        }

# Usage
for batch in BatchGenerator(total_samples=100000, batch_size=1000, seed=42):
    # Process batch without loading full dataset
    train_model(batch['X'], batch['y'])
```

### 4.2 Vectorized Parameter Sweeps

```python
def generate_parameter_sweep(
    base_params: dict,
    param_grid: dict[str, np.ndarray],
    n_samples_per_config: int,
    seed: int
) -> list[tuple[np.ndarray, dict]]:
    """Generate datasets for each parameter combination.
    
    Efficient for optimization loops and hyperparameter searches.
    """
    rng = default_rng(seed)
    
    # Create all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    configs = np.array(np.meshgrid(*param_values)).T.reshape(-1, len(param_names))
    
    # Spawn independent RNG for each config
    child_rngs = rng.spawn(len(configs))
    
    results = []
    for config_vals, child_rng in zip(configs, child_rngs):
        config = dict(zip(param_names, config_vals))
        config.update(base_params)
        
        # Generate data for this config
        data = _generate_from_config(child_rng, n_samples_per_config, config)
        results.append((data, config))
    
    return results

def _generate_from_config(rng: Generator, n: int, config: dict) -> np.ndarray:
    """Generate data according to configuration."""
    loc = config.get('mean', 0.0)
    scale = config.get('std', 1.0)
    return rng.normal(loc=loc, scale=scale, size=(n, config.get('n_features', 10)))
```

---

## 5. Distribution Patterns (NumPy/SciPy)

### 5.1 Common Distribution Generators

```python
from scipy import stats

class DistributionLibrary:
    """Reusable distribution generators with consistent API."""
    
    def __init__(self, rng: Generator):
        self.rng = rng
    
    def normal_mixture(
        self,
        n_samples: int,
        means: list[float],
        stds: list[float],
        weights: list[float]
    ) -> np.ndarray:
        """Generate from Gaussian mixture."""
        weights = np.array(weights) / np.sum(weights)
        components = self.rng.choice(len(means), size=n_samples, p=weights)
        
        samples = np.zeros(n_samples)
        for i, (mean, std) in enumerate(zip(means, stds)):
            mask = components == i
            samples[mask] = self.rng.normal(mean, std, size=mask.sum())
        
        return samples
    
    def correlated_features(
        self,
        n_samples: int,
        n_features: int,
        correlation_matrix: np.ndarray
    ) -> np.ndarray:
        """Generate correlated multivariate normal features."""
        mean = np.zeros(n_features)
        return self.rng.multivariate_normal(mean, correlation_matrix, size=n_samples)
    
    def power_law(
        self,
        n_samples: int,
        alpha: float,
        x_min: float = 1.0
    ) -> np.ndarray:
        """Generate power-law distributed values."""
        u = self.rng.uniform(0, 1, size=n_samples)
        return x_min * (1 - u) ** (-1 / (alpha - 1))
```

### 5.2 Scikit-learn Dataset Generators (for ML contexts)

```python
from sklearn.datasets import make_classification, make_regression

def generate_classification_dataset(
    n_samples: int,
    n_features: int = 20,
    n_informative: int = 10,
    n_redundant: int = 5,
    random_state: int = 42
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Wrapper for sklearn with metadata."""
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=n_redundant,
        n_classes=2,
        random_state=random_state,
        shuffle=False  # Keep deterministic ordering
    )
    
    metadata = {
        'n_samples': n_samples,
        'n_features': n_features,
        'n_informative': n_informative,
        'n_redundant': n_redundant,
        'random_state': random_state,
        'generator': 'sklearn.make_classification'
    }
    
    return X, y, metadata
```

---

## 6. Testing & Validation Patterns

### 6.1 Reproducibility Tests

```python
def test_reproducibility():
    """Verify same seed produces identical output."""
    seed = 12345
    
    # Generate twice
    data1, _ = generate_with_metadata(n_samples=1000, random_state=seed)
    data2, _ = generate_with_metadata(n_samples=1000, random_state=seed)
    
    np.testing.assert_array_equal(data1, data2)

def test_independence():
    """Verify spawned generators produce different streams."""
    parent_rng = default_rng(42)
    children = parent_rng.spawn(10)
    
    samples = [rng.random(1000) for rng in children]
    
    # Check all pairs are different
    for i in range(len(samples)):
        for j in range(i + 1, len(samples)):
            assert not np.allclose(samples[i], samples[j])
```

### 6.2 Statistical Validation

```python
def validate_distribution(
    data: np.ndarray,
    expected_mean: float,
    expected_std: float,
    tolerance: float = 0.1
) -> bool:
    """Check generated data matches expected distribution."""
    actual_mean = np.mean(data)
    actual_std = np.std(data)
    
    mean_error = abs(actual_mean - expected_mean) / (expected_mean + 1e-10)
    std_error = abs(actual_std - expected_std) / (expected_std + 1e-10)
    
    return mean_error < tolerance and std_error < tolerance
```

---

## 7. Lightweight Benchmark Interface

### 7.1 Benchmark-Friendly API

```python
from time import perf_counter
from typing import Callable

@dataclass
class BenchmarkResult:
    """Results from benchmark run."""
    n_samples: int
    generation_time_ms: float
    memory_mb: float
    config: dict
    seed: int

def benchmark_generator(
    generator_fn: Callable,
    n_samples: int,
    n_repeats: int = 5,
    **params
) -> list[BenchmarkResult]:
    """Benchmark generation performance."""
    import tracemalloc
    
    results = []
    for i in range(n_repeats):
        seed = 42 + i  # Different seed per repeat
        
        tracemalloc.start()
        start = perf_counter()
        
        data = generator_fn(n_samples, random_state=seed, **params)
        
        elapsed = (perf_counter() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        results.append(BenchmarkResult(
            n_samples=n_samples,
            generation_time_ms=elapsed,
            memory_mb=peak / 1024 / 1024,
            config=params,
            seed=seed
        ))
    
    return results

# Usage
results = benchmark_generator(
    generate_with_metadata,
    n_samples=100000,
    n_repeats=5,
    n_features=50
)
avg_time = np.mean([r.generation_time_ms for r in results])
```

---

## 8. Practical Recommendations for Small Teams

### 8.1 Minimal Viable API

For quick iterations in research code:
```python
# Single-file generator utility
def generate(n: int, seed: int = 42, **kw) -> tuple[np.ndarray, dict]:
    """Minimal generator: data + metadata."""
    rng = default_rng(seed)
    X = rng.normal(size=(n, kw.get('d', 10)))
    return X, {'seed': seed, 'n': n, **kw}
```

### 8.2 Gradual Sophistication Path

**Phase 1: Script-level generation**
- Use `default_rng(seed)` directly in scripts
- Store seed in variable at top of file

**Phase 2: Function-based**
- Wrap in functions with `random_state` parameter
- Add basic metadata dict returns

**Phase 3: Class-based**
- Create generator class with spawn support
- Add structured output (dataclass/namedtuple)

**Phase 4: Production-ready**
- Full metadata tracking with JSON export
- Batch generation support
- Statistical validation utilities

### 8.3 Config Integration (YAML)

```yaml
# data_generation.yaml
synthetic_data:
  n_samples: 10000
  batch_size: 1000
  seed: 42
  
  features:
    n_features: 20
    n_informative: 15
    correlation: 0.3
  
  output:
    format: "npz"
    save_metadata: true
    output_dir: "data/synthetic"
```

```python
import yaml

def generate_from_config(config_path: str) -> SyntheticDataset:
    """Generate dataset from YAML config."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    gen_cfg = config['synthetic_data']
    
    rng = default_rng(gen_cfg['seed'])
    X = rng.normal(size=(gen_cfg['n_samples'], 
                        gen_cfg['features']['n_features']))
    
    return SyntheticDataset(
        X=X,
        seed=gen_cfg['seed'],
        generation_params=gen_cfg,
        timestamp=str(np.datetime64('now'))
    )
```

---

## 9. Key Takeaways for Restaurant Project

Based on your current codebase structure (`functions_income.py`, `functions_population.py`):

1. **Add generator utilities module:**
   ```
   sources/synthetic_generators.py
   ```

2. **Seed management pattern:**
   ```python
   # In main.py or config
   MASTER_SEED = 42  # Or from YAML
   rng = default_rng(MASTER_SEED)
   
   # For different model components
   population_rng = rng.spawn(1)[0]
   income_rng = rng.spawn(1)[0]
   ```

3. **Batch generation for parameter sweeps:**
   ```python
   # For testing different menu configurations
   def test_menu_configurations(base_config, param_grid, seed):
       rng = default_rng(seed)
       configs = create_param_combinations(param_grid)
       child_rngs = rng.spawn(len(configs))
       
       for config, child_rng in zip(configs, child_rngs):
           synthetic_data = generate_customers(child_rng, config)
           results = simulate_revenue(synthetic_data, config)
           # ... evaluate
   ```

4. **Metadata tracking:**
   - Add `seed` field to existing JSON configs
   - Track generation parameters in output plots metadata
   - Save RNG state for checkpoint/resume capability

---

## 10. References

**Official Documentation:**
- NumPy Random: https://numpy.org/doc/stable/reference/random/index.html
- NumPy Generator: https://numpy.org/doc/stable/reference/random/generator.html
- NumPy Parallel RNG: https://numpy.org/doc/stable/reference/random/parallel.html
- SciPy Stats: https://docs.scipy.org/doc/scipy/reference/stats.html
- Scikit-learn Datasets: https://scikit-learn.org/stable/datasets.html

**Key Concepts:**
- PCG64: Faster modern RNG (default in NumPy 1.17+)
- SeedSequence spawning: Guaranteed independent streams for parallel work
- 128-bit seeds: Use `secrets.randbits(128)` for cryptographic-quality randomness

**Performance Notes:**
- `Generator` methods are 2-10x faster than legacy `RandomState`
- Vectorized generation is orders of magnitude faster than loops
- Batch generation minimizes memory overhead for large datasets
