# 🏗️ GNN-Driven Truss Optimization

[![CI](https://img.shields.io/github/actions/workflow/status/USER/gnn-truss-optimization/ci.yml?branch=main&label=CI&logo=github)](https://github.com/USER/gnn-truss-optimization/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licence](https://img.shields.io/badge/Licence-MIT-green)](LICENSE)

> A step-by-step **learning project** that teaches a computer to design the shape and
> cross-sections of a truss so that it is **as light as possible while still carrying its load**.

The full Persian curriculum lives in [`amozeshi/roadmap.md`](amozeshi/roadmap.md); this
repository implements that 8-step path as a conventional, tested Python package.
Persian version of this file: [`README.md`](README.md)

---

## 🗺️ Roadmap

| Step | Topic | Where it lives | Status |
|:---:|---|---|:---:|
| 1 | Vectors, matrices, `F = K·u` | `week1/` | ✅ |
| 2 | Single bar, `k = EA/L` | `single_bar_exercise/` | ✅ |
| 3 | Stiffness assembly, solving the system | `src/trussgnn/fem/` | ✅ (ported) |
| 4 | Internal force, stress, support reactions | `src/trussgnn/fem/truss.py` | ✅ (ported + tested) |
| 5 | Multiple load cases, data generation | `src/trussgnn/data/` | 🔜 |
| 6 | Truss as a graph (`edge_index`, Laplacian) | `src/trussgnn/graph/` | ✅ |
| 7 | **GNN** (message passing on graphs) | `src/trussgnn/models/` | 🔜 |
| 8 | **Optimization with the GNN** 🎯 | `src/trussgnn/optimize/` | 🔜 |

## 📁 Project layout

```
gnn-truss-optimization/
├── amozeshi/                # Persian learning roadmap (reference document)
├── week1/                   # Step-1 exercises (matrices and graphs)
├── single_bar_exercise/     # Step-2 exercises (single bar)
├── src/trussgnn/            # ← the package (new and ported code)
│   ├── fem/                 #   finite-element core (steps 3-4)
│   ├── graph/               #   truss -> graph conversion (step 6)
│   ├── data/                #   dataset generation (step 5)
│   ├── models/              #   graph neural networks (step 7)
│   └── optimize/            #   weight minimization (step 8)
├── tests/                   # pytest suite (hand-checked validation)
├── notebooks/               # Jupyter notes
├── configs/                 # experiment configuration (YAML)
├── scripts/                 # operational helper scripts
└── docs/                    # technical documentation
```

## 🚀 Quick start

```bash
# 1. Install dependencies (uv creates and manages the virtual environment)
uv sync

# 2. Run the canonical triangle-truss analysis
uv run truss-fem

# 3. Run the test suite
uv run pytest

# 4. Plot the deformed shape
uv run python -c "import trussgnn.plot; from trussgnn.fem.truss import solve_tutorial; solve_tutorial(plot=True)"
```

### Example: analysing the triangle truss

```python
import numpy as np
from trussgnn.fem.truss import TrussModel, solve_truss

model = TrussModel(
    nodes=np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]]),
    elements=np.array([[0, 1], [1, 2], [2, 0]]),
    fixed_dofs=np.array([0, 1, 2, 3]),
)
loads = np.zeros((3, 2))
loads[2, 1] = -100_000.0          # 100 kN downward at the apex

result = solve_truss(model, loads)
print(result.displacement)         # nodal displacements (m)
print(result.axial_forces)         # internal member forces (N)
print(result.stresses)             # axial stresses (Pa)
```

## ✅ Tests and code quality

The project is **validation-first**: numeric answers are checked against hand
calculations (golden rule #1 of the roadmap).

| Tool | Purpose | Command |
|---|---|---|
| pytest | unit tests | `uv run pytest` |
| coverage | coverage report | `uv run coverage run -m pytest && uv run coverage report` |
| ruff | lint + formatting | `uv run ruff check . && uv run ruff format --check .` |
| mypy | strict type checking | `uv run mypy src` |
| pre-commit | commit-time hooks | `uv run pre-commit run --all-files` |

## 🔧 Development

```bash
uv sync --dev --all-extras    # install every development dependency
uv run pre-commit install     # enable the pre-commit hooks
```

The learning path is [`amozeshi/roadmap.md`](amozeshi/roadmap.md); the next milestone
is **step 5 (data generation)**.

## 📄 Licence

MIT — free to use for learning.