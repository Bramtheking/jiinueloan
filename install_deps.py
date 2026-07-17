import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "a2wsgi==1.9.0"],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)
