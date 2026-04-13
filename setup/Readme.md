# Setup Configurations

This directory stores runtime configuration files for the simulation.

## Canonical format

- YAML is the primary format (`*.yaml`).
- JSON files are kept temporarily for backward compatibility.
- Loader entrypoints in `sources/config_loader.py` support both.

## Canonical R1 files

- `menu_setup_R1.yaml`
- `behavior_setup_r1.yaml`
- `population_setup_R1.yaml`
- `expenses_setup_R1.yaml`

## Test fixtures

- Test fixture copies exist under `setup/tests/` in YAML and JSON.
- Automated tests should prefer YAML fixtures.

## Notes for edits

- Keep probability values in `[0, 1]`.
- Keep time ranges in 24h format (`[start, end]`).
- For `Nworking.places`, keep numeric-like identifiers quoted in YAML (for example `'0'`, `'1'`).
