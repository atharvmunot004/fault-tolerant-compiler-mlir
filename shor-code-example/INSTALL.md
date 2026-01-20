# MLIR Python Bindings Installation Guide

This project requires the **official MLIR Python bindings** from LLVM, which are **not** available via simple `pip install mlir`. The `mlir` package on PyPI is just a stub and does not provide the required functionality.

## Option 1: Build from Source (Recommended)

The official MLIR Python bindings must be built from the LLVM project source.

### Prerequisites
- CMake (3.13.4 or newer)
- Python 3.8+ (with development headers)
- C++ compiler (GCC, Clang, or MSVC on Windows)
- Ninja (recommended) or Make

### Steps

1. **Clone LLVM project:**
   ```bash
   git clone https://github.com/llvm/llvm-project.git
   cd llvm-project
   ```

2. **Configure with Python bindings enabled:**
   ```bash
   mkdir build
   cd build
   cmake -G "Ninja" \
     -DLLVM_ENABLE_PROJECTS="mlir" \
     -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
     -DPython3_EXECUTABLE=$(which python3) \
     -DCMAKE_BUILD_TYPE=Release \
     ../llvm
   ```
   
   **On Windows (PowerShell):**
   ```powershell
   cmake -G "Ninja" `
     -DLLVM_ENABLE_PROJECTS="mlir" `
     -DMLIR_ENABLE_BINDINGS_PYTHON=ON `
     -DPython3_EXECUTABLE="C:\path\to\python.exe" `
     -DCMAKE_BUILD_TYPE=Release `
     ..\llvm
   ```

3. **Build:**
   ```bash
   ninja
   ```
   (This may take 30-60 minutes depending on your system)

4. **Add to PYTHONPATH:**
   ```bash
   # Linux/macOS
   export PYTHONPATH=$PWD/tools/mlir/python_packages/mlir_core:$PYTHONPATH
   
   # Windows (PowerShell)
   $env:PYTHONPATH="$PWD\tools\mlir\python_packages\mlir_core;$env:PYTHONPATH"
   ```

5. **Verify installation:**
   ```python
   python -c "from mlir import ir; from mlir.dialects import builtin, func; print('MLIR bindings installed successfully!')"
   ```

### Full Documentation
See: https://mlir.llvm.org/docs/Bindings/Python/

## Option 2: Conda (If Available)

Some platforms have MLIR available via conda:

```bash
conda install -c conda-forge mlir
```

**Note:** Availability varies by platform. Windows support may be limited.

## Option 3: Pre-built Wheels (Community)

Check for community-provided wheels:
- Search for "mlir-wheels" on GitHub
- Check MLIR community forums/discourse

## Troubleshooting

### "cannot import name 'ir' from 'mlir'"
- You likely have the wrong `mlir` package installed. Uninstall it:
  ```bash
  pip uninstall mlir
  ```
- Ensure you've built MLIR with `MLIR_ENABLE_BINDINGS_PYTHON=ON`
- Verify PYTHONPATH includes the MLIR Python package directory

### Python version mismatch
- Ensure the Python version used to build MLIR matches your runtime Python version
- Check with: `python --version` and verify CMake detected the correct Python

### Missing dependencies
- On Linux: `sudo apt-get install python3-dev` (or equivalent)
- On macOS: Python headers usually come with Xcode command line tools
- On Windows: Ensure Python development headers are available

## Quick Test

After installation, test with:
```python
from mlir import ir
from mlir.dialects import builtin, func, arith, tensor
from mlir.passmanager import PassManager

with ir.Context() as ctx:
    builtin.register_dialect(ctx)
    module = ir.Module.create()
    print("MLIR bindings working!")
```

