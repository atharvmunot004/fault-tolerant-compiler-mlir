from __future__ import annotations

import random
from typing import List, Tuple


def _row_mult_phase(x1: int, z1: int, x2: int, z2: int) -> int:
    """
    Phase update helper used by Aaronson–Gottesman tableau row multiplication.
    Returns exponent of i (mod 4) contributed by multiplying single-qubit Paulis.
    """
    # Identity contributes no phase.
    if (x1 == 0 and z1 == 0) or (x2 == 0 and z2 == 0):
        return 0

    # Matching Paulis also contribute no phase.
    if x1 == x2 and z1 == z2:
        return 0

    # Explicit non-commuting Pauli multiplication phases:
    # XZ = +iY, ZX = -iY
    if x1 == 1 and z1 == 0 and x2 == 0 and z2 == 1:
        return 1
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 0:
        return 3

    # ZY = +iX, YZ = -iX
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 1:
        return 1
    if x1 == 1 and z1 == 1 and x2 == 0 and z2 == 1:
        return 3

    # YX = +iZ, XY = -iZ
    if x1 == 1 and z1 == 1 and x2 == 1 and z2 == 0:
        return 1
    if x1 == 1 and z1 == 0 and x2 == 1 and z2 == 1:
        return 3

    raise ValueError("invalid Pauli bits for row multiplication")


class StabilizerState:
    """
    Stabilizer tableau representing an n-qubit stabilizer state.

    Representation follows Aaronson–Gottesman:
    - 2n rows: first n are destabilizers, last n are stabilizers
    - x[r][q], z[r][q] bits
    - r_phase[r] is 0/1 representing overall sign (-1)^r_phase (we only need +/- for state simulation)
    """

    def __init__(self, n: int, x: List[List[int]], z: List[List[int]], r_phase: List[int]):
        self.n = n
        self.x_mat = x
        self.z_mat = z
        self.r_phase = r_phase

    @classmethod
    def zero(cls, n: int) -> "StabilizerState":
        if n <= 0:
            raise ValueError("n must be >= 1")
        x = [[0] * n for _ in range(2 * n)]
        z = [[0] * n for _ in range(2 * n)]
        r_phase = [0 for _ in range(2 * n)]

        # |0...0> stabilizers: Z_i (rows n+i)
        # destabilizers: X_i (rows i)
        for i in range(n):
            x[i][i] = 1
            z[n + i][i] = 1
        return cls(n=n, x=x, z=z, r_phase=r_phase)

    # --- Basic tableau utilities ---
    def copy(self) -> "StabilizerState":
        return StabilizerState(
            n=self.n,
            x=[row[:] for row in self.x_mat],
            z=[row[:] for row in self.z_mat],
            r_phase=self.r_phase[:],
        )

    def _rowswap(self, a: int, b: int) -> None:
        self.x_mat[a], self.x_mat[b] = self.x_mat[b], self.x_mat[a]
        self.z_mat[a], self.z_mat[b] = self.z_mat[b], self.z_mat[a]
        self.r_phase[a], self.r_phase[b] = self.r_phase[b], self.r_phase[a]

    def _rowmult(self, a: int, b: int) -> None:
        """
        Row a <- Row a * Row b (Pauli multiplication) with phase tracking (mod 2 sign).
        """
        n = self.n
        # Track phase using i-exponent mod 4, then reduce to sign (0/1).
        exp_i = 0
        if self.r_phase[a]:
            exp_i += 2
        if self.r_phase[b]:
            exp_i += 2
        for q in range(n):
            exp_i += _row_mult_phase(
                self.x_mat[a][q], self.z_mat[a][q], self.x_mat[b][q], self.z_mat[b][q]
            )
        exp_i %= 4

        for q in range(n):
            self.x_mat[a][q] ^= self.x_mat[b][q]
            self.z_mat[a][q] ^= self.z_mat[b][q]

        # exp_i == 0 => +1, exp_i == 2 => -1, exp_i in {1,3} should never occur for valid tableau rows
        self.r_phase[a] = 1 if exp_i == 2 else 0

    # --- Clifford gates ---
    def i(self, q: int) -> None:
        """Identity gate; included for completeness with Clifford gate sets."""
        if q < 0 or q >= self.n:
            raise IndexError("qubit index out of range")

    def h(self, q: int) -> None:
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -Y under H (sign flip)
            self.x_mat[r][q], self.z_mat[r][q] = z, x

    def s(self, q: int) -> None:
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -X under S
            self.z_mat[r][q] ^= x

    def sdg(self, q: int) -> None:
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & (z ^ 1):
                self.r_phase[r] ^= 1  # X -> -Y under S†
            self.z_mat[r][q] ^= x

    def s_dagger(self, q: int) -> None:
        self.sdg(q)

    def sx(self, q: int) -> None:
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if (x ^ 1) & z:
                self.r_phase[r] ^= 1  # Z -> -Y under √X
            self.x_mat[r][q] ^= z

    def sqrt_x(self, q: int) -> None:
        self.sx(q)

    def sxdg(self, q: int) -> None:
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -Z under √X†
            self.x_mat[r][q] ^= z

    def sqrt_x_dagger(self, q: int) -> None:
        self.sxdg(q)

    def x(self, q: int) -> None:
        # Conjugation by X flips sign of Z and Y.
        for r in range(2 * self.n):
            if self.z_mat[r][q] == 1:
                self.r_phase[r] ^= 1

    def y(self, q: int) -> None:
        # Conjugation by Y flips sign of X and Z, but not Y.
        for r in range(2 * self.n):
            if self.x_mat[r][q] ^ self.z_mat[r][q]:
                self.r_phase[r] ^= 1

    def z(self, q: int) -> None:
        # Conjugation by Z flips sign of X and Y.
        for r in range(2 * self.n):
            if self.x_mat[r][q] == 1:
                self.r_phase[r] ^= 1

    def cx(self, control: int, target: int) -> None:
        self.cnot(control, target)

    def cnot(self, control: int, target: int) -> None:
        c, t = control, target
        for r in range(2 * self.n):
            xc = self.x_mat[r][c]
            zc = self.z_mat[r][c]
            xt = self.x_mat[r][t]
            zt = self.z_mat[r][t]

            # Phase update per Aaronson–Gottesman
            if xc & zt & (xt ^ zc ^ 1):
                self.r_phase[r] ^= 1

            self.x_mat[r][t] ^= xc
            self.z_mat[r][c] ^= zt

    def cz(self, control: int, target: int) -> None:
        self.h(target)
        self.cnot(control, target)
        self.h(target)

    def cy(self, control: int, target: int) -> None:
        self.sdg(target)
        self.cnot(control, target)
        self.s(target)

    def swap(self, q1: int, q2: int) -> None:
        self.cnot(q1, q2)
        self.cnot(q2, q1)
        self.cnot(q1, q2)

    # --- Measurement ---
    def measure_z(self, q: int) -> int:
        """
        Measure Z on qubit q. Returns outcome bit (0 -> +1 eigenvalue, 1 -> -1 eigenvalue).
        """
        n = self.n
        # Search for a stabilizer row that anticommutes with Z_q (i.e., has X on q)
        p = -1
        for r in range(n, 2 * n):
            if self.x_mat[r][q] == 1:
                p = r
                break

        if p == -1:
            # Deterministic: Z_q is fixed by stabilizers. Outcome determined by product of rows
            # that have Z on q in destabilizer part.
            # Compute sign of implied observable by eliminating X on q in destabilizers.
            # Using standard AG technique: multiply stabilizer rows where destabilizer has X on q.
            outcome = 0
            for r in range(0, n):
                if self.x_mat[r][q] == 1:
                    # This destabilizer row implies a stabilizer with Z on q; its phase contributes.
                    outcome ^= self.r_phase[n + r]
            return outcome

        # Random outcome
        outcome = random.randint(0, 1)

        # Make p the pivot stabilizer row for this measurement by clearing X on q in other rows
        for r in range(2 * n):
            if r != p and self.x_mat[r][q] == 1:
                self._rowmult(r, p)

        # Move pivot into destabilizer slot corresponding to this qubit (use row n+q as canonical)
        self._rowswap(p, n + q)

        # Set new stabilizer row (n+q) to measured Z on q with outcome sign.
        # In AG tableau, after measurement, stabilizer row becomes Z_q with phase outcome.
        for j in range(n):
            self.x_mat[n + q][j] = 0
            self.z_mat[n + q][j] = 0
        self.z_mat[n + q][q] = 1
        self.r_phase[n + q] = outcome

        # Destabilizer row q becomes previous pivot row content (now at position p), ensure X on q.
        # We want destabilizer row q to anticommute with new Z_q, simplest is set it to X_q.
        for j in range(n):
            self.x_mat[q][j] = 0
            self.z_mat[q][j] = 0
        self.x_mat[q][q] = 1
        self.r_phase[q] = 0

        return outcome

    def reset_z(self, q: int) -> int:
        """
        Measures Z on q and (if needed) applies X so the post-state has q in |0>.
        Returns the measurement outcome bit.
        """
        m = self.measure_z(q)
        if m == 1:
            self.x(q)
        return m

    # --- Debug / inspection helpers ---
    def _pauli_char_at(self, r: int, q: int) -> str:
        xb, zb = self.x_mat[r][q], self.z_mat[r][q]
        if xb == 0 and zb == 0:
            return "I"
        if xb == 1 and zb == 0:
            return "X"
        if xb == 1 and zb == 1:
            return "Y"
        return "Z"

    def format_chp_printstate(self) -> str:
        """
        Same layout as CHP's printstate(): destabilizer rows, a rule line, stabilizer rows,
        each row prefixed with + or - from the sign bit (CHP phase mod 4 reduced to +/- here).
        """
        n = self.n
        lines: List[str] = []
        for i in range(2 * n):
            if i == n:
                lines.append("")
                lines.append("-" * (n + 1))
            sign = "-" if self.r_phase[i] else "+"
            pauli = "".join(self._pauli_char_at(i, q) for q in range(n))
            lines.append(sign + pauli)
        return "\n".join(lines)

    def format_xz_binary_matrices(self) -> str:
        """Print the raw X and Z bit tables (2n rows × n columns), side by side."""

        def _fmt_row(row: List[int]) -> str:
            return "  " + " ".join(str(b) for b in row)

        n_rows = 2 * self.n
        x_title = f"X matrix ({n_rows} x {self.n})"
        z_title = f"Z matrix ({n_rows} x {self.n})"
        gap = "    "
        x_rows = [_fmt_row(row) for row in self.x_mat]
        z_rows = [_fmt_row(row) for row in self.z_mat]
        left_width = max([len(x_title)] + [len(r) for r in x_rows])

        lines = [x_title.ljust(left_width) + gap + z_title]
        lines.extend(
            x_rows[i].ljust(left_width) + gap + z_rows[i] for i in range(n_rows)
        )
        return "\n".join(lines)

    def format_phase_matrix(self) -> str:
        """Print the tableau phase bits as a 2n × 1 column matrix."""
        lines = [f"Phase matrix ({2 * self.n} x 1)"]
        lines.extend(f"  [{phase}]" for phase in self.r_phase)
        return "\n".join(lines)

    def format_tableau_debug(self) -> str:
        """CHP-style Pauli rows plus explicit X, Z, and phase matrices."""
        return (
            "Tableau (CHP-style destabilizers | stabilizers):\n"
            + self.format_chp_printstate()
            + "\n\n"
            + self.format_xz_binary_matrices()
            + "\n\n"
            + self.format_phase_matrix()
        )

    def stabilizer_generators(self) -> List[Tuple[int, List[int], List[int]]]:
        """
        Returns list of stabilizer generators as (phase_bit, x_row, z_row) for the last n rows.
        """
        out = []
        for r in range(self.n, 2 * self.n):
            out.append((self.r_phase[r], self.x_mat[r][:], self.z_mat[r][:]))
        return out

