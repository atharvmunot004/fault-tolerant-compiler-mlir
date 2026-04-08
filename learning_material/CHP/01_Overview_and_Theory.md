# CHP: Overview and Theory

This document explains **what** CHP simulates and **why** that simulation can be done efficiently on a classical computer.

## 1. Stabilizer Circuits

A **stabilizer circuit** is a quantum circuit that uses only the following gates and operations:

| Gate / operation | Symbol | Action |
|------------------|--------|--------|
| **CNOT** | Controlled-NOT | Control qubit \(a\), target qubit \(b\): \(\|x,y\rangle \to \|x, x\oplus y\rangle\). |
| **Hadamard** | \(H\) | \(\|0\rangle \leftrightarrow (\|0\rangle+\|1\rangle)/\sqrt{2}\), \(\|1\rangle \leftrightarrow (\|0\rangle-\|1\rangle)/\sqrt{2}\). |
| **Phase** | \(S\), \(\pi/2\) phase | \(\|0\rangle\to\|0\rangle\), \(\|1\rangle\to i\|1\rangle\). |
| **Measurement** | \(M\) | Measure one qubit in the computational (Z) basis; outcome 0 or 1. |

**Initial state:** Qubits are assumed to start in the computational basis (e.g. \(\|0\ldots 0\rangle\)). CHP also allows an optional “input” string per qubit (e.g. z, Z, x, X, y, Y) to set a one-qubit stabilizer state before the circuit runs (see [03_File_Format_and_Usage.md](03_File_Format_and_Usage.md)).

No T gate (\(\pi/4\) phase), no general single-qubit unitaries, no Toffoli. So the set of gates is a strict subset of “full” quantum computing, but it is still very useful for:

- Quantum error correction (many codes use only Clifford gates)
- Protocols like teleportation, dense coding, GHZ
- Some algorithms (e.g. Simon’s algorithm)

## 2. Stabilizer States and the Pauli Group

### Pauli operators

On one qubit, the **Pauli operators** are:

- \(I\), \(X\), \(Y\), \(Z\) (with possible overall factors \(\pm 1\), \(\pm i\)).

On \(n\) qubits, a **Pauli product** is a tensor product of \(n\) one-qubit Paulis (again up to \(\pm 1\), \(\pm i\)). For example: \(X_1 Z_2\), \(Y_3\), etc.

### Stabilizer of a state

A pure state \( |\psi\rangle \) is a **stabilizer state** if there is an Abelian group \(\mathcal{S}\) of \(n\) Pauli products (excluding \(-I^{\otimes n}\)) such that:

- Every \(P \in \mathcal{S}\) satisfies \(P|\psi\rangle = |\psi\rangle\).

So \( |\psi\rangle \) is the unique (+1) common eigenstate of the generators of \(\mathcal{S}\). For \(n\) qubits there are \(n\) independent generators; the group has \(2^n\) elements.

**Key fact:** If you start in a stabilizer state (e.g. \( |0\ldots 0\rangle \)) and apply only CNOT, Hadamard, and phase gates, you always stay in a stabilizer state. Measurement in the computational basis either keeps it stabilizer (deterministic outcome) or projects to a stabilizer state (random outcome).

So the **entire state** can be described by the **stabilizer group** (or a set of \(n\) generators) instead of \(2^n\) amplitudes. CHP represents this with a **destabilizer–stabilizer table**: \(n\) destabilizer generators (rows that “anticommute appropriately” with the stabilizers) and \(n\) stabilizer generators; see [02_Data_Structures_and_Algorithms.md](02_Data_Structures_and_Algorithms.md).

## 3. Gottesman–Knill Theorem

The **Gottesman–Knill theorem** says:

- Any circuit made of:
  - Preparation in computational basis,
  - CNOT, Hadamard, phase gates,
  - and Z-basis measurements  
  can be **simulated classically in polynomial time** (in number of qubits and gates).

So there is no “quantum advantage” from stabilizer circuits alone; the power of CHP is that it makes this classical simulation **fast and explicit** by representing the state as stabilizer (and destabilizer) generators and updating them under each gate and measurement.

## 4. Why CHP Is Efficient

- **State representation:** The simulator does **not** store \(2^n\) amplitudes. It stores:
  - \(n\) **stabilizer** generators (each is \(n\) Paulis → \(O(n^2)\) bits with phases),
  - and \(n\) **destabilizer** generators (see [02_Data_Structures_and_Algorithms.md](02_Data_Structures_and_Algorithms.md)).
  So memory is \(O(n^2)\).

- **Gate application:** Each gate is applied by **updating** the generator table (how each generator transforms under the gate). That is \(O(n)\) work per gate, no exponentials.

- **Measurement:** Either the outcome is determined by the stabilizer (then no random choice), or one generator is replaced and others updated; again \(O(n^2)\) in the worst case.

So the runtime is **polynomial** in \(n\) and the number of gates, and CHP can handle thousands of qubits for stabilizer circuits. Circuits are supplied as `.chp` files (see [03_File_Format_and_Usage.md](03_File_Format_and_Usage.md)).

## 5. What CHP Does Not Do

- **Non-Clifford gates:** No T (\(\pi/4\) phase), no general single-qubit unitaries. Those take the state out of the stabilizer formalism.
- **General initial states:** Only stabilizer initial states (e.g. \( |0\ldots 0\rangle \) or states prepared with H/S/CNOT from \( |0\ldots 0\rangle \)). The “input” string (z, Z, x, X, y, Y) in CHP prepares specific one-qubit stabilizer states.
- **Noise:** The simulator is ideal (no decoherence or gate errors) unless you explicitly add extra qubits/gates to model noise.

## 6. Complexity Note (from the paper)

Simulating stabilizer circuits is **complete for ParityL** (classical complexity class related to parity). So stabilizer circuits are not even believed to be universal for **classical** computation; they sit in a restricted class that is classically tractable.

## 7. Reference

- S. Aaronson and D. Gottesman, *Improved simulation of stabilizer circuits*, Physical Review A **70**, 052328 (2004); [arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196).

---

Next: [02_Data_Structures_and_Algorithms.md](02_Data_Structures_and_Algorithms.md) — how CHP represents the state and implements gates and measurement.
