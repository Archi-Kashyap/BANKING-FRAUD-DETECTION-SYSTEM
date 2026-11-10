#!/usr/bin/env python3
"""
Unified Process Orchestrator for FraudGuard Threat Analysis System.
Starts the FastAPI backend (api.py on port 8001) and Streamlit frontend (app.py on port 8503)
concurrently, with API health-check polling and clean multi-process lifecycle management.
"""

import argparse
import atexit
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    requests = None
    import urllib.request
    import json


# Global process references and OS job handle for bulletproof shutdown
_api_proc: subprocess.Popen | None = None
_streamlit_proc: subprocess.Popen | None = None
_shutting_down = False
_job_handle = None


def init_windows_job_object() -> None:
    """Initialize a Windows Job Object configured to kill child processes if parent exits."""
    global _job_handle
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoCounters", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryLimit", ctypes.c_size_t),
                ("PeakJobMemoryLimit", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        res = kernel32.SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if res:
            _job_handle = job
    except Exception:
        pass


def assign_to_job(proc: subprocess.Popen) -> None:
    """Assign a subprocess to the Windows Job Object if active."""
    global _job_handle
    if sys.platform != "win32" or not _job_handle or not proc:
        return
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.AssignProcessToJobObject(_job_handle, int(proc._handle))
    except Exception:
        pass


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is already open/bound on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def kill_proc_tree(pid: int) -> None:
    """Forcefully kill a process and its child processes across platforms."""
    if not pid:
        return
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass


def shutdown() -> None:
    """Gracefully terminate child processes; force kill if unresponsive."""
    global _shutting_down, _api_proc, _streamlit_proc
    if _shutting_down:
        return
    _shutting_down = True

    print("\n[FraudGuard Launcher] Initiating graceful shutdown of child services...", flush=True)

    targets = [
        ("Streamlit Dashboard", _streamlit_proc),
        ("FastAPI Backend", _api_proc),
    ]

    # Step 1: Send termination signal to process tree
    for name, proc in targets:
        if proc and proc.poll() is None:
            print(f"[FraudGuard Launcher] Terminating {name} (PID: {proc.pid})...", flush=True)
            try:
                if sys.platform == "win32":
                    kill_proc_tree(proc.pid)
                else:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except Exception:
                        proc.terminate()
            except Exception as exc:
                print(f"[FraudGuard Launcher] Note: Failed to terminate {name}: {exc}", flush=True)

    # Step 2: Wait briefly for clean termination; force kill if unresponsive
    for name, proc in targets:
        if proc:
            try:
                proc.wait(timeout=3.0)
                print(f"[FraudGuard Launcher] {name} terminated cleanly.", flush=True)
            except (subprocess.TimeoutExpired, Exception):
                print(f"[FraudGuard Launcher] {name} did not stop within 3s; killing process tree...", flush=True)
                kill_proc_tree(proc.pid)
                try:
                    proc.wait(timeout=2.0)
                except Exception:
                    pass

    print("[FraudGuard Launcher] All child services stopped.", flush=True)


def _signal_handler(signum, frame):
    print(f"\n[FraudGuard Launcher] Received signal {signum}. Shutting down...", flush=True)
    shutdown()
    sys.exit(0)


def poll_api_health(health_url: str, timeout: float, api_proc: subprocess.Popen) -> bool:
    """
    Poll the FastAPI health endpoint until it returns HTTP 200 OK
    or the timeout expires.
    """
    start_time = time.time()
    poll_interval = 0.5
    print(f"[FraudGuard Launcher] Waiting for FastAPI backend at {health_url} (timeout: {timeout}s)...", flush=True)

    while time.time() - start_time < timeout:
        # Check if the process died unexpectedly
        exit_code = api_proc.poll()
        if exit_code is not None:
            print(f"[FraudGuard Launcher] ERROR: FastAPI server crashed prematurely with exit code {exit_code}!", flush=True)
            return False

        try:
            if requests:
                resp = requests.get(health_url, timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    model_name = data.get("model", "ready")
                    print(f"[FraudGuard Launcher] FastAPI is ONLINE and healthy! [model: {model_name}]", flush=True)
                    return True
            else:
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode("utf-8"))
                        model_name = body.get("model", "ready")
                        print(f"[FraudGuard Launcher] FastAPI is ONLINE and healthy! [model: {model_name}]", flush=True)
                        return True
        except Exception:
            pass

        time.sleep(poll_interval)

    print(f"[FraudGuard Launcher] ERROR: Timed out after {timeout}s waiting for FastAPI health check.", flush=True)
    return False


def wait_for_streamlit_ready(port: int, timeout: float = 15.0, st_proc: subprocess.Popen = None) -> bool:
    """Wait for Streamlit port to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if st_proc and st_proc.poll() is not None:
            return False
        if is_port_in_use(port, "127.0.0.1"):
            return True
        time.sleep(0.5)
    return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Unified Process Orchestrator for FraudGuard (FastAPI + Streamlit)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="FastAPI host address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8001,
        help="FastAPI backend port (default: 8001)",
    )
    parser.add_argument(
        "--streamlit-port",
        "--port",
        dest="streamlit_port",
        type=int,
        default=8503,
        help="Streamlit frontend port (default: 8503)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level (default: info)",
    )
    parser.add_argument(
        "--health-timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds to wait for FastAPI health check (default: 30.0)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run Streamlit in headless mode without automatically launching browser",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=False,
        help="Alias for --headless",
    )
    return parser.parse_args()


def main():
    global _api_proc, _streamlit_proc

    args = parse_args()
    headless_mode = args.headless or args.no_browser

    project_root = Path(__file__).resolve().parent
    api_script = project_root / "api.py"
    app_script = project_root / "app.py"

    if not api_script.exists():
        print(f"[FraudGuard Launcher] ERROR: api.py not found at {api_script}", flush=True)
        sys.exit(1)
    if not app_script.exists():
        print(f"[FraudGuard Launcher] ERROR: app.py not found at {app_script}", flush=True)
        sys.exit(1)

    # Pre-flight port availability check
    if is_port_in_use(args.api_port, args.host):
        print(
            f"[FraudGuard Launcher] ERROR: Port {args.api_port} is already in use on {args.host}.\n"
            f"Please terminate any existing process or choose a different port using --api-port.",
            flush=True,
        )
        sys.exit(1)

    if is_port_in_use(args.streamlit_port, "127.0.0.1"):
        print(
            f"[FraudGuard Launcher] ERROR: Port {args.streamlit_port} is already in use on 127.0.0.1.\n"
            f"Please terminate any existing process or choose a different port using --port.",
            flush=True,
        )
        sys.exit(1)

    # Initialize kernel-level process isolation/cleanup
    init_windows_job_object()

    # Register cleanup handlers
    atexit.register(shutdown)
    for sig in ("SIGINT", "SIGTERM", "SIGBREAK", "SIGHUP"):
        if hasattr(signal, sig):
            try:
                signal.signal(getattr(signal, sig), _signal_handler)
            except Exception:
                pass

    env = os.environ.copy()
    api_base_url = f"http://{args.host}:{args.api_port}"
    env["API_URL"] = api_base_url
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    health_url = f"{api_base_url}/health"

    print("=" * 64, flush=True)
    print("  FRAUDGUARD MULTI-AGENT THREAT ANALYSIS SYSTEM", flush=True)
    print("  Unified Process Orchestrator (FastAPI + Streamlit)", flush=True)
    print("=" * 64, flush=True)
    print(f"  FastAPI Target:     {api_base_url} (Health: {health_url})", flush=True)
    print(f"  Streamlit Target:   http://localhost:{args.streamlit_port}", flush=True)
    print(f"  Headless Mode:      {'Enabled (No Browser)' if headless_mode else 'Disabled (Auto Launch Browser)'}", flush=True)
    print("=" * 64, flush=True)

    # 1. Start FastAPI child process
    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api:api",
        "--host",
        args.host,
        "--port",
        str(args.api_port),
        "--log-level",
        args.log_level,
    ]

    popen_kwargs = {"cwd": str(project_root), "env": env}
    if sys.platform != "win32":
        popen_kwargs["preexec_fn"] = os.setsid

    print(f"[FraudGuard Launcher] Starting FastAPI backend: {' '.join(api_cmd)}", flush=True)
    try:
        _api_proc = subprocess.Popen(api_cmd, **popen_kwargs)
        assign_to_job(_api_proc)
    except Exception as exc:
        print(f"[FraudGuard Launcher] FATAL: Failed to launch FastAPI process: {exc}", flush=True)
        sys.exit(1)

    # 2. Wait for FastAPI health check before launching Streamlit / browser
    is_healthy = poll_api_health(health_url, timeout=args.health_timeout, api_proc=_api_proc)
    if not is_healthy:
        print("[FraudGuard Launcher] Startup aborted due to FastAPI health check failure.", flush=True)
        shutdown()
        sys.exit(1)

    # 3. Start Streamlit child process
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(args.streamlit_port),
        "--server.headless",
        "true" if headless_mode else "false",
    ]

    print(f"[FraudGuard Launcher] Starting Streamlit dashboard: {' '.join(streamlit_cmd)}", flush=True)
    try:
        _streamlit_proc = subprocess.Popen(streamlit_cmd, **popen_kwargs)
        assign_to_job(_streamlit_proc)
    except Exception as exc:
        print(f"[FraudGuard Launcher] FATAL: Failed to launch Streamlit process: {exc}", flush=True)
        shutdown()
        sys.exit(1)

    # Check if Streamlit binds
    if wait_for_streamlit_ready(args.streamlit_port, timeout=15.0, st_proc=_streamlit_proc):
        print(f"[FraudGuard Launcher] Streamlit dashboard is READY at http://localhost:{args.streamlit_port}", flush=True)
    else:
        print(f"[FraudGuard Launcher] Note: Streamlit initializing on port {args.streamlit_port}...", flush=True)

    print("\n" + "=" * 64, flush=True)
    print("  SERVICES OPERATIONAL", flush=True)
    print(f"  - Backend API:       {api_base_url}", flush=True)
    print(f"  - API Documentation: {api_base_url}/docs", flush=True)
    print(f"  - Frontend Console:  http://localhost:{args.streamlit_port}", flush=True)
    print("  Press Ctrl+C at any time to shut down both services cleanly.", flush=True)
    print("=" * 64 + "\n", flush=True)

    # 4. Supervision loop: monitor processes until termination or Ctrl+C
    try:
        while True:
            api_exit = _api_proc.poll()
            if api_exit is not None:
                print(f"[FraudGuard Launcher] FastAPI exited with status {api_exit}. Shutting down...", flush=True)
                break

            st_exit = _streamlit_proc.poll()
            if st_exit is not None:
                print(f"[FraudGuard Launcher] Streamlit exited with status {st_exit}. Shutting down...", flush=True)
                break

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[FraudGuard Launcher] Keyboard interrupt detected (Ctrl+C).", flush=True)
    finally:
        shutdown()


if __name__ == "__main__":
    main()
