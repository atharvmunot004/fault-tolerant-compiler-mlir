from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Op:
    name: str
    targets: Tuple[int, ...]


class Circuit:
    def __init__(self, n_qubits: int):
        if n_qubits <= 0:
            raise ValueError("n_qubits must be >= 1")
        self.n_qubits = n_qubits
        self.ops: List[Op] = []

    def h(self, q: int) -> "Circuit":
        self.ops.append(Op("H", (q,)))
        return self

    def s(self, q: int) -> "Circuit":
        self.ops.append(Op("S", (q,)))
        return self

    def x(self, q: int) -> "Circuit":
        self.ops.append(Op("X", (q,)))
        return self

    def z(self, q: int) -> "Circuit":
        self.ops.append(Op("Z", (q,)))
        return self

    def cnot(self, control: int, target: int) -> "Circuit":
        self.ops.append(Op("CNOT", (control, target)))
        return self

    def mz(self, q: int, key: Optional[str] = None) -> "Circuit":
        # key is stored as metadata-like op name suffix; simple + dependency-free.
        self.ops.append(Op("MZ" if key is None else f"MZ:{key}", (q,)))
        return self

    def extend(self, ops: Iterable[Op]) -> "Circuit":
        self.ops.extend(list(ops))
        return self

    def run(self, state: "StabilizerState") -> List[int]:
        if state.n < self.n_qubits:
            raise ValueError("State has fewer qubits than circuit")
        out: List[int] = []
        for op in self.ops:
            if op.name == "H":
                state.h(op.targets[0])
            elif op.name == "S":
                state.s(op.targets[0])
            elif op.name == "X":
                state.x(op.targets[0])
            elif op.name == "Z":
                state.z(op.targets[0])
            elif op.name == "CNOT":
                c, t = op.targets
                state.cnot(c, t)
            elif op.name.startswith("MZ"):
                out.append(state.measure_z(op.targets[0]))
            else:
                raise ValueError(f"Unknown op: {op.name}")
        return out

