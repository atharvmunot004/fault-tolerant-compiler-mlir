## stabilizer-python

Minimal stabilizer (Clifford) simulator in pure Python, plus example error-correcting codes inspired by the CHP material.

### What you get

- **Stabilizer simulator**: tableau-based Aaronson–Gottesman style state update for Clifford gates and Z measurement.
- **2-qubit circuits**: build and run small Clifford circuits (H, S, X, Z, CNOT, measurements).
- **3-qubit bit-flip code**: encoder and Z-parity syndrome extraction (measures \(Z_0 Z_1\) and \(Z_1 Z_2\)).
- **9-qubit Shor code**: encoder built as phase-protection + three bit-flip blocks.

### Quick start

From repo root:

```bash
python -m stabilizer_python.examples.two_qubit_bell
python -m stabilizer_python.examples.bitflip3_demo
python -m stabilizer_python.examples.shor9_demo
```

Run tests:

```bash
pytest -q stabilizer-python/tests
```

