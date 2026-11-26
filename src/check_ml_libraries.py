
import sys
import importlib

print("======================================")
print("ML LIBRARY AVAILABILITY CHECK")
print("======================================")

print("Python executable:", sys.executable)
print("Python version:", sys.version)

libraries = [
    "numpy",
    "pandas",
    "sklearn",
    "scipy",
    "joblib",
    "matplotlib"
]

missing = []

print("\nLIBRARY STATUS")
print("--------------------------------------")

for library in libraries:

    try:
        module = importlib.import_module(library)

        version = getattr(
            module,
            "__version__",
            "Version unavailable"
        )

        print(library, "| INSTALLED |", version)

    except ImportError:
        print(library, "| NOT INSTALLED")
        missing.append(library)

print("\nMISSING LIBRARIES:", missing)

if missing:
    print("\nINSTALLATION REQUIRED")
else:
    print("\nALL REQUIRED LIBRARIES AVAILABLE")

print("\nLIBRARY CHECK COMPLETED")
