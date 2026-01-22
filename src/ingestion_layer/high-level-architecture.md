# Ingestion Layer — High-Level Pipeline

> **Goal:** Convert *any supported circuit description* into **canonical, verifiable MLIR Logical IR** with zero ambiguity.

---

## 0. Input Classification (Format Detection)

**Purpose:** Decide *how* to read the input.

### Inputs

* OpenQASM text
* Python circuit object (Qiskit / Cirq-like)
* QASM-like DSL

### Output

* `FrontendKind ∈ {OpenQASM, PythonAdapter, DSL}`

❌ No IR creation yet
❌ No semantic assumptions

---

## 1. Frontend Adapter (Language → Canonical Form)

**Purpose:** Remove language-specific quirks.

### What Happens

* Python objects → OpenQASM
* DSL → OpenQASM
* OpenQASM → pass through

### Output (Single Canonical Format)

```
Canonical OpenQASM
```

### Why This Exists

* Avoid N×M translators
* Make correctness testable
* One semantics definition

> **Invariant after this stage:**
> “Everything is OpenQASM.”

---

## 2. OpenQASM Parsing (Syntax → AST)

**Purpose:** Structural understanding.

### Input

```
OpenQASM text
```

### Output

```
OpenQASM AST
```

### Checks (Syntax Only)

* Grammar correctness
* Valid tokens
* Correct register indexing

❌ No gate legality checks yet
❌ No lowering yet

---

## 3. Circuit Contract Validation (Semantic Gatekeeping)

**Purpose:** Enforce *“what circuits my compiler accepts”*.

### Checks

* Allowed gate set only
* Static qubit count
* No classical control flow
* Measurements only at leaf ops
* No unsupported OpenQASM features

### Failure Mode

* Hard error with explanation
  (“`if` statements are not supported in Ingestion Layer”)

> **This is the most important barrier in the system.**

---

## 4. Gate Normalization (Canonicalization)

**Purpose:** Make all circuits *structurally uniform*.

### Examples

* `cx` → `cnot`
* `u3(θ,φ,λ)` → sequence of `{H, T, S}`
* Resolve gate aliases

### Output

```
Normalized Gate AST
```

> After this, **every gate is in the logical gate set**.

---

## 5. Resource Resolution (Registers → SSA Values)

**Purpose:** Transition from *indexed wires* to *compiler values*.

### What Happens

* `q[0]` → `%q0 : !logical.qubit`
* `c[1]` → `%c1 : !logical.cbit`
* Allocation order becomes explicit

### Output

```
Resolved Circuit Graph (SSA-like)
```

> This is where **compiler semantics begin**.

---

## 6. MLIR Logical Construction

**Purpose:** Materialize the circuit in MLIR.

### Input

* Normalized gate sequence
* Resolved qubit/cbit mapping

### Output

```
MLIR Logical IR
```

Example:

```mlir
%q0 = logical.alloc : !logical.qubit
logical.h %q0 : !logical.qubit
```

Ordering is preserved **exactly**.

---

## 7. MLIR Verification (Structural Guarantees)

**Purpose:** Ensure IR is *legal and safe*.

### Checks

* No illegal ops
* Correct operand types
* No qubit reuse violations
* Measurement correctness

> After this step, downstream passes **assume correctness**.

---

# Full Ingestion Layer Flow (Single View)

```
[Any Circuit]
     ↓
[Format Detection]
     ↓
[Frontend Adapter]
     ↓
[Canonical OpenQASM]
     ↓
[Parser → AST]
     ↓
[Contract Validation]
     ↓
[Gate Normalization]
     ↓
[Resource Resolution]
     ↓
[MLIR Logical Builder]
     ↓
[MLIR Verifier]
     ↓
[Logical MLIR]
```

---

# Key Architectural Invariants (Memorize These)

1. **Only one canonical input language** (OpenQASM)
2. **No semantic guessing**
3. **Early rejection is success**
4. **MLIR never sees ambiguity**
5. **Ordering is sacred**

---
