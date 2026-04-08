# CHP: File Format and Usage

This document describes the **.chp circuit file format**, **command-line syntax**, and **initial-state input** used by CHP.

## 1. Command-Line Syntax

```text
chp [-options] <filename> [input]
```

- **filename:** Circuit file, with or without `.chp` extension. If the name has no extension, CHP tries `<filename>.chp`.
- **options:** Optional, must start with `-`. Each character after `-` enables a flag (case-insensitive where noted).
- **input:** Optional string used as the initial state for the first qubits (see Section 3). Only some circuits use it (e.g. `teleport`, `densecoding`, `qecc9`).

### 1.1 Option Flags

| Option | Meaning |
|--------|--------|
| `-q` or `-Q` | **DISPQSTATE:** Print the quantum state. `q` = print only at the end; `Q` = print after every step (if supported). In the code, both set the same flag; typically used as `-q` for final state. |
| `-t` or `-T` | **DISPTIME:** Print timing (gate time, measurement time, time per 10000 gates/measurements). |
| `-p` or `-P` | **DISPPROG:** Print each gate as it is executed (e.g. `CNOT 0->1`, `Hadamard 2`). |
| `-s` or `-S` | **SILENT:** Do not print measurement outcomes. |
| `-m` or `-M` | **SUPPRESSM:** Do not actually compute determinate measurement results (faster when you only care about random outcomes). |

**Examples:**

```bash
chp epr
chp -t epr
chp -q teleport z
chp -pt densecoding ZZ
chp -s simon
```

## 2. .chp File Format

### 2.1 Structure

1. **Comment block:** Lines before the first line that contains only `#` (possibly with surrounding whitespace) are treated as comments. The **first line that contains `#`** is the delimiter: CHP skips until it finds that line, then reads instructions after it.
2. **Instructions:** After the `#` line, each instruction is one line: a single letter (gate type) followed by one or two qubit indices.

### 2.2 Instruction Syntax

| Letter | Gate | Arguments | Example |
|--------|------|-----------|--------|
| `c` or `C` | CNOT | control, target | `c 0 1` |
| `h` or `H` | Hadamard | qubit | `h 0` |
| `p` or `P` | Phase (S) | qubit | `p 2` |
| `m` or `M` | Measure | qubit | `m 1` |

- Qubit indices are **0-based** integers.
- The number of qubits is **inferred** from the circuit: it is the maximum qubit index appearing in any instruction, plus 1.
- Blank lines and lines that are only `\r` or `\n` are skipped after the `#`.

### 2.3 Example: Minimal EPR Circuit

```text
# Comment lines above the first line containing #
# This creates EPR pair on qubits 0 and 1, then measures qubit 1
#
h 0
c 0 1
m 1
```

### 2.4 Parsing Notes (from `readprog` in chp.c)

- The program does **two passes**: first to count instructions and infer `n`, then to fill `a[]`, `b[]`, `c[]`.
- It scans until it finds a line containing `#`, then reads instructions. So the **first line that contains `#`** starts the “after comment” section; the actual circuit starts on the following lines (after skipping newlines).
- For CNOT, two numbers are read; for H, P, M, only one number is read.

## 3. Initial State Input (Optional Third Argument)

When you run e.g. `chp teleport z`, the third argument `z` is the **input string**. It specifies the state of the **first few qubits** (one character per qubit) **before** the circuit runs. The rest of the qubits start in \( |0\rangle \).

### 3.1 Input Characters (One Qubit Each)

Each character specifies a **single-qubit stabilizer state** (eigenstate of a Pauli):

| Input | State | Description |
|-------|--------|-------------|
| `z` | \( |0\rangle + |1\rangle \) (unnormalized) | +1 eigenstate of X |
| `Z` | \( |0\rangle - |1\rangle \) | \(-1\) eigenstate of X |
| `x` | \( |0\rangle + |1\rangle \) | Same as `z` (Hadamard of \( |0\rangle \)) |
| `X` | \( |0\rangle - |1\rangle \) | \(-1\) eigenstate of X (like Z) |
| `y` | \( |0\rangle + i|1\rangle \) | +1 eigenstate of Y |
| `Y` | \( |0\rangle - i|1\rangle \) | \(-1\) eigenstate of Y |

So:

- **z / x:** \( |+\rangle \) (X = +1)
- **Z / X:** \( |-\rangle \) (X = −1)
- **y:** \( |0\rangle + i|1\rangle \) (Y = +1)
- **Y:** \( |0\rangle - i|1\rangle \) (Y = −1)

Length of the string = number of qubits whose state you set. Qubits beyond the string start in \( |0\rangle \).

### 3.2 How CHP Applies the Input (`preparestate`)

The simulator starts in \( |0\ldots 0\rangle \) (destabilizers \(X_i\), stabilizers \(Z_i\)). Then, for each character in the input string (indexed by qubit \(b\)), it applies:

- **Z:** H → S² → H (rotate \( |0\rangle \) to \( |1\rangle \)).
- **x:** H (\( |0\rangle \to |+\rangle \)).
- **X:** H → S² (\( |0\rangle \to |-\rangle \)).
- **y:** H → S (\( |0\rangle \to |0\rangle+i|1\rangle \)).
- **Y:** H → S³ (\( |0\rangle \to |0\rangle-i|1\rangle \)).

So the “input” is implemented as a short stabilizer circuit applied to the initial \( |0\ldots 0\rangle \) state.

### 3.3 Examples by Circuit

- **teleport.chp:** First qubit is the state to teleport.  
  `chp teleport z` → teleport \( |+\rangle \); `chp teleport Z` → teleport \( |-\rangle \); `chp teleport y` → teleport \( |0\rangle+i|1\rangle \).
- **densecoding.chp:** First two qubits encode the 2-bit message (e.g. `zz` = 00, `zZ` = 01, `Zz` = 10, `ZZ` = 11).
- **qecc9.chp:** Qubit 0 = data to encode; qubits 1 and 2 = whether to apply encoded X and Z. E.g. `chp qecc9 zZZ` encodes \( |0\rangle \) and applies encoded Y (output \( |1\rangle \)).

## 4. Summary

- **Run:** `chp [-options] <file> [input]`.
- **File:** Comment block, then a line containing `#`, then lines `c i j`, `h i`, `p i`, `m i`.
- **Input:** Optional string of `z,Z,x,X,y,Y` to set initial stabilizer state of the first qubits.

Next: [04_Example_Circuits.md](04_Example_Circuits.md) — detailed walkthrough of the example circuits.
