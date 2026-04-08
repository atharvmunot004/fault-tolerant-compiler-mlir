from stabilizer_python.codes import Shor9Code
from stabilizer_python.tableau import StabilizerState


def main() -> None:
    st = StabilizerState.zero(9)
    Shor9Code.encoder_circuit().run(st)
    print("Shor 9-qubit encoder applied.")
    print("Number of stabilizer generators:", len(st.stabilizer_generators()))


if __name__ == "__main__":
    main()

