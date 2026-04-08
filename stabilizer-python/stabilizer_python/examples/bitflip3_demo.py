from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tableau import StabilizerState


def main() -> None:
    # 5 qubits: data q0..q2, ancillas q3..q4
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)  # acts on q0..q2

    # Inject an X error on qubit 1 (demo).
    st.x(1)

    s01, s12 = BitFlip3Code.measure_syndrome(st)
    print("Syndrome (s01, s12):", (s01, s12))

    BitFlip3Code.correct_x_from_syndrome(st, s01, s12)
    s01b, s12b = BitFlip3Code.measure_syndrome(st)
    print("After correction syndrome:", (s01b, s12b))


if __name__ == "__main__":
    main()

