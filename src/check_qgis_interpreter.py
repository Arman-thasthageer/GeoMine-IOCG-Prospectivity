
import os
import subprocess

print("======================================")
print("QGIS PYTHON INTERPRETER CHECK")
print("======================================")

interpreters = [
    r"C:\Program Files\QGIS 3.44.15\apps\Python312\python.exe",
    r"C:\Program Files\QGIS 3.44.15\bin\python3.exe"
]

for interpreter in interpreters:

    print("\nChecking:")
    print(interpreter)

    if not os.path.exists(interpreter):
        print("STATUS: FILE NOT FOUND")
        continue

    print("STATUS: FILE EXISTS")

    try:
        result = subprocess.run(
            [interpreter, "--version"],
            capture_output=True,
            text=True,
            timeout=15
        )

        print("Return code:", result.returncode)
        print("Output:", result.stdout.strip())
        print("Error:", result.stderr.strip())

    except Exception as error:
        print("Execution error:", repr(error))

print("\nINTERPRETER CHECK COMPLETED")
