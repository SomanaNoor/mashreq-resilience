
import subprocess
import sys
import time
import socket
import os
import signal
import webbrowser

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port=8501):
    port = start_port
    while is_port_in_use(port):
        print(f"Port {port} is in use, trying {port+1}...")
        port += 1
    return port

def check_dependencies():
    required = ['streamlit', 'fastapi', 'uvicorn', 'pandas', 'plotly']
    missing = []
    print("Checking dependencies...")
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ MISSING DEPENDENCIES: {', '.join(missing)}")
        print("Please run: pip install -r requirements.txt")
        return False
    print("✅ Dependencies OK")
    return True

def main():
    print("="*50)
    print("   MASHREQ AI - ROBUST LAUNCHER")
    print("="*50)

    if not check_dependencies():
        print("Press Enter to exit... (SKIPPED)")
        sys.exit(1)

    # Kill old python processes (Windows only)
    # Skipped to avoid self-termination
    if False and os.name == 'nt':
        print("Cleaning up old processes...", flush=True)
        os.system("taskkill /f /im python.exe >nul 2>&1")

    # Change to src directory
    src_dir = os.path.join(os.getcwd(), 'src')
    print(f"DEBUG: src_dir is {src_dir}", flush=True)
    if not os.path.exists(src_dir):
        print(f"❌ Error: 'src' directory not found in {os.getcwd()}", flush=True)
        print("Press Enter to exit... (SKIPPED)", flush=True)
        sys.exit(1)
    
    os.chdir(src_dir)
    print("DEBUG: Changed directory to src", flush=True)

    # Find ports
    print("DEBUG: Finding API port...", flush=True)
    api_port = find_free_port(8000)
    print(f"DEBUG: Found API port {api_port}. Finding Dash port...", flush=True)
    dash_port = find_free_port(8501)
    if dash_port == api_port:
        dash_port = find_free_port(api_port + 1)
    print(f"DEBUG: Found Dash port {dash_port}", flush=True)

    print(f"🚀 Starting API on port {api_port}...", flush=True)
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(api_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(f"🚀 Starting Dashboard on port {dash_port}...")
    dash_cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard.py",
        "--server.port", str(dash_port),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    dash_process = subprocess.Popen(
        dash_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("\nWaiting for services to initialize...")
    time.sleep(5)

    # Check if they died
    if api_process.poll() is not None:
        print("\n❌ API FAILED TO START!")
        print(api_process.stderr.read())
        print("Press Enter to exit... (SKIPPED)")
        sys.exit(1)

    if dash_process.poll() is not None:
        print("\n❌ DASHBOARD FAILED TO START!")
        print(dash_process.stderr.read())
        print("Press Enter to exit... (SKIPPED)")
        sys.exit(1)

    url = f"http://127.0.0.1:{dash_port}"
    print(f"\n✅ SYSTEM RUNNING AT: {url}")
    webbrowser.open(url)

    print("\nPress Ctrl+C to stop the servers.")
    
    try:
        while True:
            time.sleep(1)
            if dash_process.poll() is not None:
                print("Dashboard crashed!")
                print(dash_process.stderr.read())
                break
    except KeyboardInterrupt:
        print("\nStopping...")
        api_process.terminate()
        dash_process.terminate()

if __name__ == "__main__":
    main()
