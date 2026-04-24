import pytest

from stabilizer_python.linear_algebra import gaussian_elimination_gf2, rank_gf2


def test_gaussian_elimination_returns_rref_and_pivots():
    matrix = [
        [1, 1, 0, 1],
        [1, 0, 1, 1],
        [0, 1, 1, 0],
    ]

    rref, pivots = gaussian_elimination_gf2(matrix)

    assert rref == [
        [1, 0, 1, 1],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ]
    assert pivots == [0, 1]


def test_gaussian_elimination_does_not_mutate_input():
    matrix = [
        [1, 0, 1],
        [0, 1, 1],
    ]
    original = [row[:] for row in matrix]

    gaussian_elimination_gf2(matrix)

    assert matrix == original


def test_rank_gf2_matches_number_of_pivots():
    matrix = [
        [1, 0, 1, 0],
        [0, 1, 1, 1],
        [1, 1, 0, 0],
    ]
    assert rank_gf2(matrix) == 3


def test_gaussian_elimination_handles_empty_matrix():
    rref, pivots = gaussian_elimination_gf2([])
    assert rref == []
    assert pivots == []
    assert rank_gf2([]) == 0


def test_gaussian_elimination_rejects_non_binary_entries():
    with pytest.raises(ValueError, match="0/1"):
        gaussian_elimination_gf2([[1, 2], [0, 1]])


def test_gaussian_elimination_rejects_ragged_matrix():
    with pytest.raises(ValueError, match="rectangular"):
        gaussian_elimination_gf2([[1, 0], [1]])
