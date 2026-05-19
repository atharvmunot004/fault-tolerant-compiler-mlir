from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tableau import StabilizerState


def _print_state(st: StabilizerState, heading: str) -> None:
    print(heading)
    print(st.format_chp_printstate())
    print()
    print(st.format_xz_binary_matrices())
    print()


def main() -> None:
    st = StabilizerState.zero(3)
    BitFlip3Code.encoder_circuit().run(st)
    _print_state(st, "Tableau after 3-qubit repetition encoding (|000>):")

    st.x(1)
    _print_state(st, "Tableau after injected X on qubit 1:")

    s01, s12 = BitFlip3Code.read_syndrome(st)
    print("Syndrome (s01, s12):", (s01, s12))
    _print_state(st, "Tableau after syndrome read (no extra ancillas):")

    BitFlip3Code.correct_x_from_syndrome(st, s01, s12)
    s01b, s12b = BitFlip3Code.read_syndrome(st)
    print("After correction syndrome:", (s01b, s12b))
    _print_state(st, "Tableau after correction:")


if __name__ == "__main__":
    main()
