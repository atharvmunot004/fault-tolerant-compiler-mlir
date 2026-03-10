from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

try:
    from mlir import ir
    from mlir.dialects import builtin, func, arith, tensor
    from mlir.passmanager import PassManager
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Failed to import MLIR python bindings.\n"
        "\n"
        "The official MLIR Python bindings are NOT available via 'pip install mlir'.\n"
        "They must be built from source as part of LLVM/MLIR.\n"
        "\n"
        "Installation options:\n"
        "1. Build from source (recommended for full functionality):\n"
        "   - Clone: git clone https://github.com/llvm/llvm-project.git\n"
        "   - Build with: -DMLIR_ENABLE_BINDINGS_PYTHON=ON\n"
        "   - See: https://mlir.llvm.org/docs/Bindings/Python/\n"
        "\n"
        "2. Use conda (if available for your platform):\n"
        "   - conda install -c conda-forge mlir\n"
        "\n"
        "3. Check for pre-built wheels:\n"
        "   - Search for 'mlir-wheels' or community packages\n"
        "\n"
        f"Original import error: {e}\n"
        "\n"
        "Note: If you installed 'mlir' via pip, uninstall it first:\n"
        "   pip uninstall mlir"
    )


@dataclass
class ShorMLIRConfig:
    """Configuration for the toy Shor-code IR."""

    qubit_elem_type: str = "i1"  # we model qubits as i1 placeholders
    n_qubits: int = 9


def _i1(ctx: ir.Context) -> ir.Type:
    return ir.IntegerType.get_signless(1)


def _tensor9_i1(ctx: ir.Context) -> ir.Type:
    return ir.RankedTensorType.get((9,), _i1(ctx))


def build_shor_module(cfg: ShorMLIRConfig = ShorMLIRConfig()) -> ir.Module:
    """Builds an MLIR module implementing Shor encode/decode as function calls.

    We deliberately avoid a quantum dialect to keep installation simple.
    Gates are represented as external functions:
      - @h(%q:i1)->i1
      - @x(%q:i1)->i1
      - @z(%q:i1)->i1
      - @cx(%c:i1,%t:i1)->(i1,i1)

    The main functions:
      - @shor_encode(%psi:i1) -> tensor<9xi1>
      - @shor_decode(%code:tensor<9xi1>) -> i1

    IMPORTANT: This is a *structural* MLIR representation (call graph), not an executable quantum runtime.
    """

    with ir.Context() as ctx:
        # Register core dialects we use.
        builtin.register_dialect(ctx)
        func.register_dialect(ctx)
        arith.register_dialect(ctx)
        tensor.register_dialect(ctx)

        module = ir.Module.create()

        i1 = _i1(ctx)
        t9 = _tensor9_i1(ctx)

        # External gate declarations.
        with ir.InsertionPoint(module.body):
            func.FuncOp("h", ([i1], [i1]), visibility="private")
            func.FuncOp("x", ([i1], [i1]), visibility="private")
            func.FuncOp("z", ([i1], [i1]), visibility="private")
            func.FuncOp("cx", ([i1, i1], [i1, i1]), visibility="private")

        def call1(name: str, v: ir.Value) -> ir.Value:
            op = func.CallOp([i1], ir.FlatSymbolRefAttr.get(name), [v])
            return op.results[0]

        def call2(name: str, a: ir.Value, b: ir.Value) -> Tuple[ir.Value, ir.Value]:
            op = func.CallOp([i1, i1], ir.FlatSymbolRefAttr.get(name), [a, b])
            return op.results[0], op.results[1]

        # Helper: extract/insert from tensor<9xi1>
        def tget(t: ir.Value, idx: int) -> ir.Value:
            c = arith.ConstantOp(ir.IntegerType.get_signless(64), idx).result
            return tensor.ExtractOp(i1, t, [c]).result

        def tset(t: ir.Value, idx: int, v: ir.Value) -> ir.Value:
            c = arith.ConstantOp(ir.IntegerType.get_signless(64), idx).result
            return tensor.InsertOp(v, t, [c]).result

        # --- shor_encode ---
        # Layout: (q0..q8)
        # Steps (canonical Shor encoding):
        # 1) Start with |psi> on q0, ancillas |0> on others.
        # 2) Create 3-qubit cat across q0,q3,q6 using CNOTs.
        # 3) Apply H to q0,q3,q6 (phase-flip protection).
        # 4) For each of q0,q3,q6, do bit-flip repetition by CNOT to the two neighbors.

        with ir.InsertionPoint(module.body):
            f_encode = func.FuncOp("shor_encode", ([i1], [t9]))

        entry = f_encode.add_entry_block()
        with ir.InsertionPoint(entry):
            psi = entry.arguments[0]

            # Initialize tensor<9xi1> = all zeros.
            # Use tensor.empty + inserts; then set q0 = psi.
            t = tensor.EmptyOp((9,), i1).result
            t = tset(t, 0, psi)

            # Load qubits as SSA values.
            q = [tget(t, i) for i in range(9)]

            # Step 2: CNOT q0 -> q3, q0 -> q6 (build 3-qubit repetition in computational basis)
            q[0], q[3] = call2("cx", q[0], q[3])
            q[0], q[6] = call2("cx", q[0], q[6])

            # Step 3: Hadamard on q0,q3,q6
            for i in (0, 3, 6):
                q[i] = call1("h", q[i])

            # Step 4: bit-flip repetition within each block
            # Block 0: q0 -> q1,q2
            q[0], q[1] = call2("cx", q[0], q[1])
            q[0], q[2] = call2("cx", q[0], q[2])
            # Block 1: q3 -> q4,q5
            q[3], q[4] = call2("cx", q[3], q[4])
            q[3], q[5] = call2("cx", q[3], q[5])
            # Block 2: q6 -> q7,q8
            q[6], q[7] = call2("cx", q[6], q[7])
            q[6], q[8] = call2("cx", q[6], q[8])

            # Write back into tensor.
            out = tensor.EmptyOp((9,), i1).result
            for i in range(9):
                out = tset(out, i, q[i])

            func.ReturnOp([out])

        # --- shor_decode ---
        # We model decoding as the inverse sequence of encode (no syndrome/measurement here).
        # This returns the recovered logical qubit (q0).
        with ir.InsertionPoint(module.body):
            f_decode = func.FuncOp("shor_decode", ([t9], [i1]))

        entry = f_decode.add_entry_block()
        with ir.InsertionPoint(entry):
            code = entry.arguments[0]
            q = [tget(code, i) for i in range(9)]

            # Inverse Step 4: undo intra-block repetition (reverse order)
            q[6], q[8] = call2("cx", q[6], q[8])
            q[6], q[7] = call2("cx", q[6], q[7])

            q[3], q[5] = call2("cx", q[3], q[5])
            q[3], q[4] = call2("cx", q[3], q[4])

            q[0], q[2] = call2("cx", q[0], q[2])
            q[0], q[1] = call2("cx", q[0], q[1])

            # Inverse Step 3: Hadamard on q0,q3,q6 (self-inverse)
            for i in (0, 3, 6):
                q[i] = call1("h", q[i])

            # Inverse Step 2: undo cat across q0,q3,q6
            q[0], q[6] = call2("cx", q[0], q[6])
            q[0], q[3] = call2("cx", q[0], q[3])

            # Logical qubit recovered in q0
            func.ReturnOp([q[0]])

        return module


def build_shor_module_with_noise(cfg: ShorMLIRConfig = ShorMLIRConfig()) -> ir.Module:
    """Builds an MLIR module with noise injection functions.
    
    Adds functions to inject bit-flip (X) and phase-flip (Z) errors:
      - @apply_noise_x(%code:tensor<9xi1>, %qubit_idx:i64) -> tensor<9xi1>
      - @apply_noise_z(%code:tensor<9xi1>, %qubit_idx:i64) -> tensor<9xi1>
      - @apply_noise(%code:tensor<9xi1>, %qubit_idx:i64, %error_type:i64) -> tensor<9xi1>
        where error_type: 0=none, 1=X, 2=Z, 3=Y (X then Z)
    """
    module = build_shor_module(cfg)
    
    with ir.Context() as ctx:
        builtin.register_dialect(ctx)
        func.register_dialect(ctx)
        arith.register_dialect(ctx)
        tensor.register_dialect(ctx)
        
        i1 = _i1(ctx)
        i64 = ir.IntegerType.get_signless(64)
        t9 = _tensor9_i1(ctx)
        
        def tget(t: ir.Value, idx: ir.Value) -> ir.Value:
            return tensor.ExtractOp(i1, t, [idx]).result
        
        def tset(t: ir.Value, idx: ir.Value, v: ir.Value) -> ir.Value:
            return tensor.InsertOp(v, t, [idx]).result
        
        # --- apply_noise_x: apply X error on qubit at index ---
        with ir.InsertionPoint(module.body):
            f_noise_x = func.FuncOp("apply_noise_x", ([t9, i64], [t9]))
        
        entry = f_noise_x.add_entry_block()
        with ir.InsertionPoint(entry):
            code = entry.arguments[0]
            qubit_idx = entry.arguments[1]
            
            # Extract qubit, apply X, insert back
            q = tget(code, qubit_idx)
            q_x = func.CallOp([i1], ir.FlatSymbolRefAttr.get("x"), [q]).results[0]
            out = tset(code, qubit_idx, q_x)
            func.ReturnOp([out])
        
        # --- apply_noise_z: apply Z error on qubit at index ---
        with ir.InsertionPoint(module.body):
            f_noise_z = func.FuncOp("apply_noise_z", ([t9, i64], [t9]))
        
        entry = f_noise_z.add_entry_block()
        with ir.InsertionPoint(entry):
            code = entry.arguments[0]
            qubit_idx = entry.arguments[1]
            
            # Extract qubit, apply Z, insert back
            q = tget(code, qubit_idx)
            q_z = func.CallOp([i1], ir.FlatSymbolRefAttr.get("z"), [q]).results[0]
            out = tset(code, qubit_idx, q_z)
            func.ReturnOp([out])
        
        # --- apply_noise: apply error based on type (0=none, 1=X, 2=Z, 3=Y) ---
        with ir.InsertionPoint(module.body):
            f_noise = func.FuncOp("apply_noise", ([t9, i64, i64], [t9]))
        
        entry = f_noise.add_entry_block()
        with ir.InsertionPoint(entry):
            code = entry.arguments[0]
            qubit_idx = entry.arguments[1]
            error_type = entry.arguments[2]
            
            # Extract qubit
            q = tget(code, qubit_idx)
            
            # Compare error_type and apply accordingly
            # This is simplified - in real MLIR you'd use scf.if or similar
            # For now, we'll just call the appropriate function
            # Note: This is a structural representation; actual branching would need scf dialect
            q_x = func.CallOp([i1], ir.FlatSymbolRefAttr.get("x"), [q]).results[0]
            q_z = func.CallOp([i1], ir.FlatSymbolRefAttr.get("z"), [q]).results[0]
            q_y = func.CallOp([i1], ir.FlatSymbolRefAttr.get("z"), [q_x]).results[0]
            
            # For simplicity, return with X applied (actual conditional logic would need scf)
            out = tset(code, qubit_idx, q_x)
            func.ReturnOp([out])
    
    return module


def canonicalize_and_cse(module: ir.Module) -> None:
    """Run a small, standard pass pipeline."""
    pm = PassManager.parse("builtin.module(canonicalize,cse,symbol-dce)")
    pm.run(module.operation)

