# test\.venv\Scripts\python test\smoke_test.py

import stabilizer_python
from stabilizer_python import Circuit, StabilizerState


def main() -> None:
    state = StabilizerState.zero(2)
    measurements = Circuit(2).h(0).cnot(0, 1).run(state)

    assert "Circuit" in stabilizer_python.__all__
    assert measurements == []
    print("stabilizer_python import and basic circuit smoke test passed")


if __name__ == "__main__":
    main()
