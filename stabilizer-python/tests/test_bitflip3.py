from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tableau import StabilizerState


def measure_syndrome_after_error(error_qubit: int):
    st = StabilizerState.zero(5)  # data 0..2, anc 3..4
    BitFlip3Code.encoder_circuit().run(st)
    st.x(error_qubit)
    s01, s12 = BitFlip3Code.measure_syndrome(st)
    return (s01, s12)


def measure_syndrome_after_phase_error(error_qubit: int):
    st = StabilizerState.zero(5)  # data 0..2, anc 3..4
    BitFlip3Code.encoder_circuit().run(st)
    st.z(error_qubit)
    s01, s12 = BitFlip3Code.measure_syndrome(st)
    return (s01, s12)


def test_bitflip3_syndrome_table():
    # Expected mapping:
    # error on 0 => (1,0), error on 1 => (1,1), error on 2 => (0,1)
    assert measure_syndrome_after_error(0) == (1, 0)
    assert measure_syndrome_after_error(1) == (1, 1)
    assert measure_syndrome_after_error(2) == (0, 1)


def test_bitflip3_phase_errors_are_not_detected_by_z_parity_syndrome():
    # This code/check pair is designed for X errors, so Z errors return trivial syndrome.
    assert measure_syndrome_after_phase_error(0) == (0, 0)
    assert measure_syndrome_after_phase_error(1) == (0, 0)
    assert measure_syndrome_after_phase_error(2) == (0, 0)


def test_bitflip3_corrects_single_x():
    for q in (0, 1, 2):
        st = StabilizerState.zero(5)
        BitFlip3Code.encoder_circuit().run(st)
        st.x(q)
        s01, s12 = BitFlip3Code.measure_syndrome(st)
        BitFlip3Code.correct_x_from_syndrome(st, s01, s12)
        s01b, s12b = BitFlip3Code.measure_syndrome(st)
        assert (s01b, s12b) == (0, 0)

