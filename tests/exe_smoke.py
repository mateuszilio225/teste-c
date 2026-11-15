# Python 3.11+ | tests/exe_smoke.py | Windows | native demo startup validation
from pathlib import Path
import subprocess
import sys
import time

exe = Path(sys.argv[1]).resolve()
process = subprocess.Popen([str(exe), '--demo'], cwd=str(exe.parent))
try:
    time.sleep(6)
    if process.poll() is not None:
        raise RuntimeError(f'Executable exited during demo startup: {process.returncode}')
    print('Packaged executable remains running after demo startup.')
finally:
    if process.poll() is None:
        process.terminate()
    process.wait(timeout=10)
