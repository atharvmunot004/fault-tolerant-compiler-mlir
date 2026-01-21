### 0.3 Installing MLIR

**Installation Options**

**Option 1: Using Pre-built Binaries (Easiest for Windows)**

1. Download LLVM with MLIR from: https://github.com/llvm/llvm-project/releases
2. Extract and add `bin` directory to PATH
3. Verify: `mlir-opt --version`

**Option 2: Building from Source (Full Control)**

```bash
# Clone LLVM repository
git clone https://github.com/llvm/llvm-project.git
cd llvm-project

# Create build directory
mkdir build && cd build

# Based on your version of Visual Studio, run the command
# Configure CMake (Windows with Visual Studio)
cmake -G "Visual Studio 16 2019" -A x64   -DLLVM_ENABLE_PROJECTS="mlir" -DLLVM_TARGETS_TO_BUILD="host" -DCMAKE_BUILD_TYPE=Release ..\llvm

# This is purely for mlir-opt and mlir-translate
# Build (this takes a while!)
cmake --build . --config Release --target mlir-opt mlir-translate

# Run this command to build the entire project (will take hours!)
cmake --build . --config Release
```

After this, add the path of $PATH$\llvm-project\build\Release\bin to your environment varible.
Restart the kernel and check

> I haven't tried this on a Windows or a Linux machine, so I can't vouch for this. If you are using this, ensure that you can use the MLIR commands, and it's not instantiating a basic LLVM project with no MLIR
**Option 3: Using Docker (Cross-platform)**

```bash
docker pull llvm/llvm-project:latest
docker run -it llvm/llvm-project:latest
```

**Option 4: Python Bindings (For Notebook Examples)**

```bash
pip install mlir
# Or if available:
pip install mlir-core
```

**Windows-Specific Installation (Recommended)**

For Windows, the easiest approach is:

> This doesn't ensure the installation of MLIR, as there's no garuntee of MLIR bring in the installer
1. **Download Pre-built LLVM**:
   - Visit: https://github.com/llvm/llvm-project/releases
   - Download the latest Windows release (e.g., `LLVM-XX.X.X-win64.exe`)
   - Run installer and select "Add LLVM to system PATH"

2. **Verify Installation**:
   ```powershell
   mlir-opt --version
   mlir-translate --version
   ```

> This might only work through WSL
3. **Alternative: Use WSL (Windows Subsystem for Linux)**:
   ```bash
   # In WSL
   sudo apt-get update
   sudo apt-get install llvm mlir
   ```

**Verifying Installation**

Run the code below to check if MLIR tools are available.


```python
# Check MLIR Installation
import subprocess
import sys
import os
from pathlib import Path

def check_mlir_installation():
    """Check if MLIR tools are installed and accessible."""
    tools = ['mlir-opt', 'mlir-translate']
    results = {}
    
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                results[tool] = {
                    'installed': True,
                    'version': result.stdout.strip().split('\n')[0] if result.stdout else 'Unknown'
                }
            else:
                results[tool] = {'installed': False, 'error': 'Command failed'}
        except FileNotFoundError:
            results[tool] = {'installed': False, 'error': 'Not found in PATH'}
        except Exception as e:
            results[tool] = {'installed': False, 'error': str(e)}
    
    return results

# Check installation
mlir_status = check_mlir_installation()

print("=" * 60)
print("MLIR Installation Status")
print("=" * 60)

for tool, status in mlir_status.items():
    if status['installed']:
        print(f"✅ {tool}: {status['version']}")
    else:
        print(f"❌ {tool}: {status.get('error', 'Not installed')}")

print("\n" + "=" * 60)

# Create directory for MLIR examples
examples_dir = Path("mlir_examples")
examples_dir.mkdir(exist_ok=True)
print(f"\n📁 Created examples directory: {examples_dir.absolute()}")

# Check if we can write MLIR files (even without mlir-opt)
print("\n💡 Note: Even without mlir-opt installed, you can:")
print("   - Write MLIR IR to files")
print("   - Learn MLIR syntax")
print("   - Run examples once MLIR is installed")


```