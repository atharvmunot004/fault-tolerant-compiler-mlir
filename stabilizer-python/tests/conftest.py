import os
import sys

# python -m pytest -q


# Allow `import stabilizer_python` when running pytest from repo root.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

