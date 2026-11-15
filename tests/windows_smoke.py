# Python 3.11+ | tests/windows_smoke.py | Windows/Linux display | demo UI smoke test
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tkinter as tk
import app

root = tk.Tk()
errors = []
def callback_error(exc, value, traceback):
    errors.append(str(value))
    app_instance.close()
root.report_callback_exception = callback_error
app_instance = app.Application(root, demo=True)
def arm():
    app_instance.toggle_arm()
    if not app_instance.armed.is_set():
        errors.append('Demo did not arm')
    root.after(2200, check)
def check():
    try:
        assert app_instance.preview.cget('image'), 'No processed demo frame'
        assert 'SIMULAÇÃO' in app_instance.status.cget('text'), app_instance.status.cget('text')
    except Exception as exc:
        errors.append(str(exc))
    finally:
        app_instance.close()
root.after(300, arm)
root.mainloop()
if errors:
    raise RuntimeError('; '.join(errors))
print('Demo UI opens, arms, processes frames and closes without native game input.')
