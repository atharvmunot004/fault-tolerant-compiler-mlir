# 9-Qubit Shor Code (toy) in MLIR Python

This repo contains a Jupyter notebook that **constructs MLIR** for the 9-qubit Shor encode/decode circuit using **Python MLIR bindings** (no full LLVM build).

## Quickstart

**IMPORTANT:** MLIR Python bindings must be installed separately. See [INSTALL.md](INSTALL.md) for detailed instructions.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Follow INSTALL.md to install MLIR Python bindings
jupyter lab
```

Open: `notebooks/9q_shor_mlir.ipynb`

## Notes
- The MLIR portion uses only standard dialects (`builtin`, `func`, `arith`, `tensor`).
- Quantum gates are modeled as **external functions** like `@h`, `@cx` (so the IR is portable without needing a quantum dialect).
- The notebook includes a small **NumPy statevector simulator** to sanity-check the encode/decode structure.
- **Noise model** included for testing error correction with bit-flip (X) and phase-flip (Z) errors.
- Error correction testing demonstrates the Shor code's ability to correct single errors.

