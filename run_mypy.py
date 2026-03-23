import sys
import subprocess

with open("mypy_utf8_out.txt", "w", encoding="utf-8") as f:
    result = subprocess.run([sys.executable, "-m", "mypy", "agents/", "--ignore-missing-imports"], capture_output=True, text=True)
    f.write(result.stdout)
    f.write(result.stderr)
