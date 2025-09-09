#!/usr/bin/env python3
"""
Startup script for LangExtract services
Runs both the main backend and speech-to-text microservice
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, cwd=None, background=False):
    """Run a command in the background or foreground"""
    if background:
        return subprocess.Popen(cmd, cwd=cwd, shell=True)
    else:
        return subprocess.run(cmd, cwd=cwd, shell=True)

def main():
    print("🚀 Starting LangExtract Services...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    backend_dir = project_root / "monorepo" / "backend"
    speech_dir = project_root / "monorepo" / "speechToText"
    frontend_dir = project_root / "monorepo" / "frontend"
    
    processes = []
    
    try:
        # Start speech-to-text service
        print("🎤 Starting Speech-to-Text service on port 8001...")
        speech_process = run_command(
            "python app.py",
            cwd=speech_dir,
            background=True
        )
        processes.append(("Speech-to-Text", speech_process))
        
        # Wait a bit for speech service to start
        time.sleep(3)
        
        # Start main backend service
        print("🔧 Starting Main Backend service on port 8000...")
        backend_process = run_command(
            "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload",
            cwd=backend_dir,
            background=True
        )
        processes.append(("Main Backend", backend_process))
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        # Start frontend development server
        print("🌐 Starting Frontend development server on port 5173...")
        frontend_process = run_command(
            "npm run dev",
            cwd=frontend_dir,
            background=True
        )
        processes.append(("Frontend", frontend_process))
        
        print("\n✅ All services started!")
        print("📱 Frontend: http://localhost:5173")
        print("🔧 Backend API: http://localhost:8000")
        print("🎤 Speech-to-Text: http://localhost:8001")
        print("\nPress Ctrl+C to stop all services...")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        
        # Stop all processes
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️  {name} force stopped")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("👋 All services stopped!")

if __name__ == "__main__":
    main()
