# CHP: CNOT-Hadamard-Phase Simulator

**CHP** is a high-performance simulator of **stabilizer circuits** — quantum circuits built only from **CNOT**, **Hadamard**, and **π/2 phase** gates, plus **1-qubit measurements**. It was written by Scott Aaronson and Daniel Gottesman and implements the algorithms from their paper *Improved simulation of stabilizer circuits* (Physical Review A 70:052328, 2004).

## What You Can Do With CHP

- **Design and debug** quantum error-correction architectures  
- **Study** large, highly-entangled quantum systems numerically  
- **Demonstrate** quantum effects: teleportation, dense coding, GHZ paradox, Simon’s algorithm  

## Documentation in This Folder

| Document | Description |
|----------|-------------|
| [01_Overview_and_Theory.md](01_Overview_and_Theory.md) | What stabilizer circuits are, Gottesman–Knill theorem, why CHP is efficient |
| [02_Data_Structures_and_Algorithms.md](02_Data_Structures_and_Algorithms.md) | How the simulator represents states (destabilizers/stabilizers) and implements gates and measurement |
| [03_File_Format_and_Usage.md](03_File_Format_and_Usage.md) | `.chp` file format, command-line options, and initial-state input |
| [04_Example_Circuits.md](04_Example_Circuits.md) | Walkthrough of EPR, GHZ, teleportation, dense coding, Simon, and Shor 9-qubit code |

## Quick Start

### Build

```bash
gcc -o chp chp.c
```

### Run a circuit

```bash
chp epr
chp teleport z
chp ghz
```

Optional initial state (e.g. for `teleport.chp`): `chp teleport z` (see [03_File_Format_and_Usage.md](03_File_Format_and_Usage.md)).

### Options

```text
chp [-qQtpsm] <filename> [input]
```

- `-q` / `-Q`: print final (or every) quantum state  
- `-t`: print timing  
- `-p`: print instructions as they run  
- `-s`: silent (no measurement output)  
- `-m`: suppress computation of determinate measurement results  

## Example Circuits Included

- **epr.chp** — Create EPR pair \( |00\rangle+|11\rangle \) and measure one qubit  
- **ghz.chp** — GHZ state and 3-player measurement game  
- **teleport.chp** — Quantum teleportation (input: z, Z, x, X, y, Y)  
- **densecoding.chp** — Dense coding (input: zz, zZ, Zz, ZZ)  
- **simon.chp** — Simon’s algorithm (hidden shift)  
- **qecc9.chp** — Shor 9-qubit code encode → Pauli → decode (input: e.g. zZZ, yZz)  

## References

- **Paper:** S. Aaronson and D. Gottesman. *Improved simulation of stabilizer circuits* [PDF](https://arxiv.org/abs/quant-ph/0406196), Physical Review A 70:052328, 2004.  
- **CHP page:** [https://www.scottaaronson.com/chp/](https://www.scottaaronson.com/chp/)  
- **Source:** [chp.c](https://www.scottaaronson.com/chp/chp.c)  

CHP is free to use; cite the paper in any publication. Do not use in commercial products without permission.
