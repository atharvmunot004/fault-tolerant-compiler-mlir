from stabilizer_python.codes import Shor9Code
from stabilizer_python.tableau import StabilizerState


def _print_state(st: StabilizerState, heading: str) -> None:
    print(heading)
    print(st.format_chp_printstate())
    print()
    print(st.format_xz_binary_matrices())
    print()


def main() -> None:
    st = StabilizerState.zero(9)
    Shor9Code.encoder_circuit().run(st)
    _print_state(st, "Tableau after Shor 9-qubit encoding (|0_L>):")

    st.x(4)
    _print_state(st, "Tableau after injected X on qubit 4 (middle of block 1):")

    syndrome = Shor9Code.read_syndrome(st)
    print("Syndrome (9 stabilizer phase bits):", syndrome)
    print()

    Shor9Code.correct_x_from_syndrome(st, syndrome)
    syndrome_b = Shor9Code.read_syndrome(st)
    print("After correction syndrome:", syndrome_b)
    _print_state(st, "Tableau after correction:")


if __name__ == "__main__":
    main()
