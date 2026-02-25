from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService


def load_api_key_from_env(env_path: str = ".env") -> str:
    """Read API_KEY from a .env file."""
    path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(f".env not found: {path.resolve()}")
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("API_KEY="):
            value = line.split("=", 1)[1].strip()
            if value.startswith(("'", '"')) and value[0] == value[-1]:
                value = value[1:-1]
            return value
    raise KeyError("API_KEY not found in .env")


if __name__ == "__main__":
    api_key = load_api_key_from_env()
    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform",
        token=api_key,
        overwrite=True,
    )
