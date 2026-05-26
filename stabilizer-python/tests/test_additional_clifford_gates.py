from stabilizer_python.tableau import StabilizerState


def _assert_same_tableau(left: StabilizerState, right: StabilizerState) -> None:
    assert left.n == right.n
    assert left.x_mat == right.x_mat
    assert left.z_mat == right.z_mat
    assert left.r_phase == right.r_phase


def _print_phase_matrix(label: str, state: StabilizerState) -> None:
    print(f"\n{label}")
    print(state.format_phase_matrix())


def _prepared_state(n_qubits: int) -> StabilizerState:
    state = StabilizerState.zero(n_qubits)
    state.h(0)
    state.s(0)
    if n_qubits > 1:
        state.h(1)
        state.cnot(0, 1)
    if n_qubits > 2:
        state.s(2)
        state.cnot(1, 2)
    return state


def test_identity_gate_is_noop():
    state = _prepared_state(3)
    expected = state.copy()

    state.i(1)

    _print_phase_matrix("I gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_y_matches_x_z_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.y(1)
    expected.x(1)
    expected.z(1)

    _print_phase_matrix("Y gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_sdg_matches_three_s_gates():
    state = _prepared_state(3)
    expected = state.copy()

    state.sdg(1)
    expected.s(1)
    expected.s(1)
    expected.s(1)

    _print_phase_matrix("Sdg gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_sqrt_x_matches_h_s_h_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.sx(1)
    expected.h(1)
    expected.s(1)
    expected.h(1)

    _print_phase_matrix("sqrt-X gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_sqrt_x_dagger_matches_h_sdg_h_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.sxdg(1)
    expected.h(1)
    expected.s(1)
    expected.s(1)
    expected.s(1)
    expected.h(1)

    _print_phase_matrix("sqrt-X-dagger gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_cx_alias_matches_cnot():
    state = _prepared_state(3)
    expected = state.copy()

    state.cx(0, 2)
    expected.cnot(0, 2)

    _print_phase_matrix("CX gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_cz_matches_h_cnot_h_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.cz(0, 2)
    expected.h(2)
    expected.cnot(0, 2)
    expected.h(2)

    _print_phase_matrix("CZ gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_cy_matches_s_cnot_sdg_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.cy(0, 2)
    expected.s(2)
    expected.s(2)
    expected.s(2)
    expected.cnot(0, 2)
    expected.s(2)

    _print_phase_matrix("CY gate phase matrix", state)
    _assert_same_tableau(state, expected)


def test_swap_matches_three_cnot_decomposition():
    state = _prepared_state(3)
    expected = state.copy()

    state.swap(0, 2)
    expected.cnot(0, 2)
    expected.cnot(2, 0)
    expected.cnot(0, 2)

    _print_phase_matrix("SWAP gate phase matrix", state)
    _assert_same_tableau(state, expected)
