from __future__ import annotations

from typing import List, Sequence, Tuple


def _validate_binary_matrix(matrix: Sequence[Sequence[int]]) -> Tuple[int, int]:
    if len(matrix) == 0:
        return 0, 0

    n_cols = len(matrix[0])
    for row in matrix:
        if len(row) != n_cols:
            raise ValueError("matrix must be rectangular")
        for value in row:
            if value not in (0, 1):
                raise ValueError("matrix must contain only 0/1 entries")
    return len(matrix), n_cols


def gaussian_elimination_gf2(matrix: Sequence[Sequence[int]]) -> Tuple[List[List[int]], List[int]]:
    """
    Compute reduced row-echelon form over GF(2).

    Returns:
    - rref matrix (new copy, input is not modified)
    - pivot columns list
    """
    n_rows, n_cols = _validate_binary_matrix(matrix)
    work = [list(row) for row in matrix]

    pivot_columns: List[int] = []
    pivot_row = 0

    for col in range(n_cols):
        if pivot_row >= n_rows:
            break

        # Find a row with a 1 in this column at or below pivot_row.
        candidate = -1
        for r in range(pivot_row, n_rows):
            if work[r][col] == 1:
                candidate = r
                break
        if candidate == -1:
            continue

        # Swap into pivot position.
        if candidate != pivot_row:
            work[pivot_row], work[candidate] = work[candidate], work[pivot_row]

        # Eliminate this column from all other rows (RREF over GF(2)).
        for r in range(n_rows):
            if r != pivot_row and work[r][col] == 1:
                for c in range(col, n_cols):
                    work[r][c] ^= work[pivot_row][c]

        pivot_columns.append(col)
        pivot_row += 1

    return work, pivot_columns


def rank_gf2(matrix: Sequence[Sequence[int]]) -> int:
    """Return rank of a binary matrix over GF(2)."""
    _, pivots = gaussian_elimination_gf2(matrix)
    return len(pivots)
