
import sys
import os
import importlib.util

print("======================================")
print("QGIS PYTHON ENVIRONMENT DIAGNOSTICS")
print("======================================")

print("\nPYTHON INFORMATION")
print("--------------------------------------")
print("Executable:", sys.executable)
print("Version:", sys.version)
print("Prefix:", sys.prefix)
print("Base prefix:", sys.base_prefix)

print("\nPYTHON MODULE LOCATIONS")
print("--------------------------------------")

modules = [
    "pip",
    "setuptools",
    "wheel",
    "numpy",
    "scipy",
    "sklearn",
    "joblib",
    "threadpoolctl"
]

for module in modules:
    spec = importlib.util.find_spec(module)

    if spec is None:
        print(module, ": NOT FOUND")
    else:
        print(module, ":", spec.origin)

print("\nPIP INFORMATION")
print("--------------------------------------")

try:
    import pip
    print("Pip version:", pip.__version__)
except Exception as error:
    print("Pip import error:", repr(error))

print("\nPYTHON ENVIRONMENT VARIABLES")
print("--------------------------------------")
print("PYTHONHOME:", os.environ.get("PYTHONHOME"))
print("PYTHONPATH:", os.environ.get("PYTHONPATH"))

print("\nDIAGNOSTICS COMPLETED")
