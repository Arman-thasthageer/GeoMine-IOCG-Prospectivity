
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

os.makedirs(package_dir, exist_ok=True)

print("======================================")
print("GEO MINE ML LIBRARY INSTALLATION")
print("======================================")

print("Python:", python_exe)
print("Package directory:", package_dir)

# =====================================================
# 2. INSTALL MISSING LIBRARIES
# =====================================================

command = [
    python_exe,
    "-m",
    "pip",
    "install",
    "--target",
    package_dir,
    "--no-deps",
    "scikit-learn",
    "joblib",
    "threadpoolctl"
]

print("\nInstalling libraries...")

result = subprocess.run(
    command,
    capture_output=True,
    text=True
)

print("\nINSTALLATION RETURN CODE:")
print(result.returncode)

print("\nINSTALLATION OUTPUT:")
print(result.stdout)

if result.stderr:
    print("\nINSTALLATION MESSAGES:")
    print(result.stderr)

if result.returncode != 0:
    raise Exception("ML library installation failed.")

print("\nML LIBRARY INSTALLATION COMPLETED")
