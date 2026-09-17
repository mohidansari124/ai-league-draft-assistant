"""Start both local servers; Ctrl+C stops both. No shell or global installs needed."""
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def free_port(port):
    with socket.socket() as sock:
        try: sock.bind(("127.0.0.1", port))
        except OSError: return False
    return True

def main():
    node = shutil.which("node")
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    if not node and bundled.exists(): node = str(bundled)
    if not node: raise SystemExit("Install Node.js 24 LTS and reopen your terminal.")
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not vite.exists(): raise SystemExit("Install frontend dependencies first: cd frontend; pnpm install --frozen-lockfile")
    if not all(free_port(port) for port in (8000, 5173)):
        raise SystemExit("Port 8000 or 5173 is already in use. Stop the existing server before starting another copy.")
    children = []
    # Each child gets its own process group so Ctrl+C is handled by this supervisor.
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    def stop(*_): raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT / "backend", creationflags=flags))
        children.append(subprocess.Popen([node, str(vite), "--host", "127.0.0.1", "--port", "5173"], cwd=ROOT / "frontend", creationflags=flags))
        print("Draftwise: http://127.0.0.1:5173 | API docs: http://127.0.0.1:8000/docs", flush=True)
        print("Press Ctrl+C to stop both servers.", flush=True)
        while all(p.poll() is None for p in children): time.sleep(.5)
        if any(p.poll() not in (None, 0) for p in children): raise SystemExit("A server stopped unexpectedly. Check the output above.")
    except KeyboardInterrupt:
        print("Stopping Draftwise…", flush=True)
    finally:
        for child in children:
            if child.poll() is None: child.terminate()
        for child in children:
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired: child.kill(); child.wait()

if __name__ == "__main__": main()
