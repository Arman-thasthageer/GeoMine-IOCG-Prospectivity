
import subprocess

python_exe = (
    r"C:\Program Files\QGIS 3.44.15"
    r"\apps\Python312\python.exe"
)

print("======================================")
print("STANDALONE QGIS PYTHON PIP CHECK")
print("======================================")

commands = [
    [python_exe, "-m", "pip", "--version"],
    [python_exe, "-m", "pip", "show", "numpy"],
    [python_exe, "-m", "pip", "show", "scipy"]
]

for command in commands:

    print("\nCommand:")
    print(" ".join(command))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        print("Return code:", result.returncode)
        print("Output:")
        print(result.stdout)

        if result.stderr:
            print("Error:")
            print(result.stderr)

    except Exception as error:
        print("Execution failed:", repr(error))

print("\nPIP VERIFICATION COMPLETED")
