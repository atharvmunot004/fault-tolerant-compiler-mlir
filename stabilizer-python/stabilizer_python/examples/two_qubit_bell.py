import sys
from pathlib import Path

_pkg_root = Path(__file__).resolve().parents[2]
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from stabilizer_python.codes import run_2qubit_bell


def main() -> None:
    st, _ = run_2qubit_bell()

    print("Tableau for |Phi+> on q0, q1 (H(0) then CNOT(0,1)):")
    print(st.format_tableau_debug())


if __name__ == "__main__":
    main()
