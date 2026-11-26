
import os
import subprocess

# =====================================================
# 1. CONFIGURATION
# =====================================================

python_exe = (
    r"C:\Program Files\QGIS 3.44.15"
    r"\apps\Python312\python.exe"
)

project_dir = r"C:\Users\Ermus\Desktop\GeoMine"

package_dir = os.path.join(
    project_dir,
    "ml_packages"
)

print("======================================")
print("INSTALL MISSING ML DEPENDENCIES")
print("======================================")

# =====================================================
# 2. INSTALL CLOUDPICKLE
# =====================================================

command = [
    python_exe,
    "-m",
    "pip",
    "install",
    "--target",
    package_dir,
    "--no-deps",
    "cloudpickle"
]

result = subprocess.run(
    command,
    capture_output=True,
    text=True
)

print("\nRETURN CODE:", result.returncode)
print("\nOUTPUT:")
print(result.stdout)

if result.stderr:
    print("\nMESSAGES:")
    print(result.stderr)

if result.returncode != 0:
    raise Exception("Cloudpickle installation failed.")

print("\nCLOUDPICKLE INSTALLATION COMPLETED")
