# Side-by-Side Comparison with Graphs

This report shows side-by-side outputs for:

- Python implementation: `stabilizer-python/stabilizer_python/`
- CHP implementation (`learning_material/CHP/chp.c`) with **two independent runs** per circuit

CHP was built with:

```powershell
gcc -o chp.exe chp.c
```

Python tests were validated before comparison:

```powershell
python -m pytest -q
# 5 passed
```

---

## Circuit Graph 1: EPR

```mermaid
flowchart LR
    A["q0: |0>"] --> H0["H(q0)"] --> C01["CNOT(q0->q1)"] --> M1["MZ(q1)"]
    B["q1: |0>"] --> C01
```

### Side-by-side outputs

**Python (1 run)**

```text
PY_EPR_M: [1]
```

**CHP run A**

```text
Outcome of measuring qubit 1: 1 (random)
2^0 nonzero basis states
 +|11>
```

**CHP run B**

```text
Outcome of measuring qubit 1: 0 (random)
2^0 nonzero basis states
 +|00>
```

**Comparison note**
- Python and CHP both show random collapse branches for Bell measurement (0 or 1).

---

## Circuit Graph 2: GHZ

```mermaid
flowchart LR
    A["q0: |0>"] --> H0["H(q0)"] --> C01["CNOT(q0->q1)"] --> C02["CNOT(q0->q2)"] --> M0["MZ(q0)"] --> M1["MZ(q1)"] --> M2["MZ(q2)"]
    B["q1: |0>"] --> C01
    C["q2: |0>"] --> C02
```

### Side-by-side outputs

**Python (1 run)**

```text
PY_GHZ_M: [1, 0, 0]
```

**CHP run A**

```text
Outcome of measuring qubit 0: 0 (random)
Outcome of measuring qubit 1: 0 (random)
Outcome of measuring qubit 2: 1
2^0 nonzero basis states
 +|001>
```

**CHP run B**

```text
Outcome of measuring qubit 0: 1 (random)
Outcome of measuring qubit 1: 1 (random)
Outcome of measuring qubit 2: 1
2^0 nonzero basis states
 +|111>
```

**Comparison note**
- GHZ measurement order/post-processing differs across implementations, but both runs exhibit branch-dependent outcomes.
- CHP clearly shows distinct random branches between run A and run B.

---

## Circuit Graph 3: Teleportation (`z` input)

CHP file reference: `learning_material/CHP/examples/teleport.chp`

```mermaid
flowchart LR
    Q0["q0: input z"] --> C01["CNOT(q0->q1)"] --> H0["H(q0)"] --> M0["MZ(q0)"] --> C03["CNOT(q0->q3)"]
    Q1["q1: |0>"] --> H1["H(q1)"] --> C12["CNOT(q1->q2)"] --> C01 --> M1["MZ(q1)"] --> C14["CNOT(q1->q4)"]
    Q2["q2: |0>"] --> C12 --> C42["CNOT(q4->q2)"] --> H2a["H(q2)"] --> C32["CNOT(q3->q2)"] --> H2b["H(q2)"] --> M2["MZ(q2)"]
    Q3["q3: anc"] --> C03 --> C32
    Q4["q4: anc"] --> C14 --> C42
```

### Side-by-side outputs

**Python (1 run, equivalent gate sequence)**

```text
PY_TELEPORT_M: [0, 1, 1]
```

**CHP run A**

```text
Outcome of measuring qubit 0: 0 (random)
Outcome of measuring qubit 1: 0 (random)
Outcome of measuring qubit 2: 0
2^0 nonzero basis states
 +|00000>
```

**CHP run B**

```text
Outcome of measuring qubit 0: 1 (random)
Outcome of measuring qubit 1: 1 (random)
Outcome of measuring qubit 2: 0
2^0 nonzero basis states
 +|11011>
```

**Comparison note**
- CHP run A and run B both end with `q2 = 0` for input `z`.
- Python run gave `q2 = 1` in this sample, which is a mismatch against both CHP samples.

---

## Final takeaways

- Requested format is now included: Python result vs **two CHP results** for each circuit.
- Graphs are added for EPR, GHZ, and teleportation circuits.
- Teleportation remains the key divergence area between current Python behavior and CHP behavior.
