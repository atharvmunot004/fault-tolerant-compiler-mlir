# CHP: Example Circuits

This document walks through the example circuits from the [CHP website](https://www.scottaaronson.com/chp/). The corresponding `.chp` files are in this folder. Run them with:

```bash
chp epr
chp ghz
chp teleport z
chp densecoding zz
chp simon
chp qecc9 zZZ
```

(Adjust the optional input for `teleport`, `densecoding`, and `qecc9` as described below.)

---

## 1. EPR Pair — `epr.chp`

**Goal:** Create an EPR (Bell) pair \(|\Phi^+\rangle = (|00\rangle + |11\rangle)/\sqrt{2}\) on qubits 0 and 1, then measure qubit 1.

**Circuit:**

1. **H 0** — Put qubit 0 in \(|+\rangle\).
2. **CNOT 0 1** — Entangle: \(|00\rangle+|11\rangle\).
3. **M 1** — Measure qubit 1 in Z basis.

**Expected:** Measurement of qubit 1 is **random** (0 or 1 with probability 1/2 each). The state before measurement is a Bell state, so either outcome is possible.

**Run:** `chp epr` (no input needed).

---

## 2. GHZ — `ghz.chp`

**Goal:** Create a 3-qubit GHZ state and run a simple “GHZ game”: three players share the state and each measures in either the Z or the X basis depending on a bit; the parity of their outcomes is used to satisfy a condition that would be impossible classically.

**State created:** \(|000\rangle - |011\rangle - |101\rangle - |110\rangle\) (up to global phase), i.e. a GHZ-type state with specific phases.

**Circuit outline:**

- H on 0 and 1, CNOTs to build entanglement (e.g. 0→2, 1→2), then phase gates to set phases.
- H on 0 and 1 (to measure in X basis on those qubits).
- Measure 0, 1, 2.

**Expected:** The three measurement outcomes are **random** but their **parity is 1** (mod 2). So you see (0,0,1), (0,1,0), (1,0,0), (1,1,1), etc., but never even parity. This illustrates the GHZ paradox.

**Run:** `chp ghz`.

---

## 3. Quantum Teleportation — `teleport.chp`

**Goal:** Teleport the state of qubit 0 to qubit 2 using one EPR pair (qubits 1 and 2) and two classical bits (simulated by qubits 3 and 4).

**Protocol (conceptually):**

1. Qubit 0 = state to teleport. Qubits 1–2 = EPR pair. Alice has 0,1; Bob has 2.
2. Alice: CNOT 0→1, H on 0, then measures 0 and 1 → two classical bits.
3. Those bits are “sent” to Bob by copying into qubits 3 and 4 (CNOT from measured qubits to 3,4).
4. Bob corrects qubit 2 using the syndrome: conditional Z (from bit 1), conditional X (from bit 0).
5. Measure qubit 2 — it should be in the same state as the original qubit 0 (up to deterministic corrections).

**Initial state (input string):**

- **z** or **x:** \(|+\rangle\) → after teleport, qubit 2 is \(|+\rangle\); measurement is **random**.
- **Z:** \(|-\rangle\) → after teleport, qubit 2 is \(|-\rangle\); measurement is **random**.
- **z:** \(|0\rangle\) → outcome **0**; **Z:** \(|1\rangle\) → outcome **1** (deterministic).

So: `chp teleport z` (or `x`) for \( |+\rangle \), `chp teleport Z` for \( |1\rangle \), `chp teleport y` for \( |0\rangle+i|1\rangle \), etc.

---

## 4. Dense Coding — `densecoding.chp`

**Goal:** Send **2 classical bits** using 1 shared EPR pair and **1 qubit** sent from Alice to Bob (Bennett–Wiesner protocol).

**Qubits:** 0,1 = two bits to send (as stabilizer state). 2,3 = EPR pair (2 = Alice, 3 = Bob). 4 = the one “quantum channel” qubit (Alice’s half is transferred to 4 and “sent” to Bob).

**Protocol:**

1. Create EPR on 2,3.
2. Alice encodes the message in qubits 0,1 into her half (qubit 2): conditional X and Z from 0,1.
3. “Send” qubit 2 to Bob by copying to qubit 4 (so 4 and 3 are now the pair Bob sees).
4. Bob: CNOT 4→3, H on 4, then measure 4 and 3 to read the 2 bits.

**Input:**

- **zz** → send 00  
- **zZ** → send 01  
- **Zz** → send 10  
- **ZZ** → send 11  

**Run:** e.g. `chp densecoding ZZ` to send 11.

---

## 5. Simon’s Algorithm — `simon.chp`

**Goal:** Illustrate Simon’s algorithm: find the “hidden shift” \(s\) such that \(f(x)=f(y)\) iff \(y = x \oplus s\) (here \(f\) is a linear map and \(s = 11111\)).

**Circuit:**

- **Qubits 0–4:** First register (5 bits).
- **Qubits 5–8:** Second register (4 bits), holding \(f(a,b,c,d,e) = (a+b, b+c, c+d, d+e)\) (linear map).

**Steps:**

1. H on 0,1,2,3,4 → uniform superposition over 5-bit strings.
2. CNOTs implement the linear \(f\) from reg 1 to reg 2 (e.g. 0→5, 1→5 and 1→6, etc.).
3. Measure 5,6,7,8 → random 4-bit string (collapsed state).
4. H on 0,1,2,3,4 (inverse QFT / Hadamard on first register).
5. Measure 0,1,2,3,4 → random 5-bit string **y** such that \(y \cdot s = 0 \pmod{2}\) (even parity with \(s\)).

Repeating many times gives several such **y**; linear algebra over GF(2) reveals \(s = 11111\).

**Run:** `chp simon`. Outcomes of the first measurement are random 4-bit values; outcomes of the second are random 5-bit values with \(y \cdot s = 0\).

---

## 6. Shor 9-Qubit Code — `qecc9.chp`

**Goal:** Encode one logical qubit (qubit 0) into 9 physical qubits with the Shor [[9,1,3]] code, apply an **encoded** Pauli (I, X, Z, or Y) controlled by qubits 1 and 2, then decode and measure the logical qubit.

**Input string (3 characters):**

- **First character (qubit 0):** Logical state to encode: z = \( |+\rangle \), Z = \( |-\rangle \), x = \( |+\rangle \), X = \( |-\rangle \), y = \( |0\rangle+i|1\rangle \), Y = \( |0\rangle-i|1\rangle \).
- **Second (qubit 1):** 1 → apply encoded **X** to the codeword.
- **Third (qubit 2):** 1 → apply encoded **Z** to the codeword.

So:

- **zZZ:** Encode \( |+\rangle \), apply encoded X and Z (i.e. encoded Y). Result: logical \( |-\rangle \) → measurement **1**.
- **yZz:** Encode \( |0\rangle+i|1\rangle \), apply encoded X only. Result: \( |0\rangle-i|1\rangle \) → measurement **random** (superposition).
- **z:** Encode \( |+\rangle \), no encoded Pauli → outcome random (still \( |+\rangle \)).

**Run:** e.g. `chp qecc9 zZZ` (expect 1), `chp qecc9 yZz` (expect random).

---

## 7. Random Circuits — `rand100.chp`, `rand200.chp`, `rand300.chp`

On the CHP website, these are 10000-gate random stabilizer circuits on 100, 200, and 300 qubits (generated by `randqc.c`). They are used for **benchmarking** the simulator. They are not included in this folder; you can download them from [the CHP page](https://www.scottaaronson.com/chp/) if needed.

---

## Quick Reference: Run Commands

| Circuit    | Command              | Notes                          |
|-----------|----------------------|---------------------------------|
| EPR       | `chp epr`            | Measure qubit 1 → random       |
| GHZ       | `chp ghz`            | 3 outcomes, parity = 1         |
| Teleport  | `chp teleport z`     | z,Z,x,X,y,Y for input state    |
| Dense     | `chp densecoding zz` | zz, zZ, Zz, ZZ for 2 bits      |
| Simon     | `chp simon`          | No input                       |
| Shor 9    | `chp qecc9 zZZ`      | 3-char: state, X?, Z?          |

For more theory and implementation details, see [01_Overview_and_Theory.md](01_Overview_and_Theory.md) and [02_Data_Structures_and_Algorithms.md](02_Data_Structures_and_Algorithms.md).
