#!/usr/bin/env python3
"""
Service manager for agent system with detailed feedback and quick operations.
"""

import subprocess
import time
import os
import sys
import json
import psutil
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class ServiceManager:
    def __init__(self) -> None:
        self.project_dir = Path(__file__).parent.parent
        self.venv_dir = self.project_dir.parent / "venv"
        self.logs_dir = self.project_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.backend_pid_file = self.logs_dir / "backend.pid"
        self.frontend_pid_file = self.logs_dir / "frontend.pid"
        self.backend_log = self.logs_dir / "backend.log"
        self.frontend_log = self.logs_dir / "frontend.log"
        
        # ANSI color codes
        self.RED = '\033[0;31m'
        self.GREEN = '\033[0;32m'
        self.YELLOW = '\033[1;33m'
        self.BLUE = '\033[0;34m'
        self.NC = '\033[0m'  # No Color
    
    def _print(self, message: str, color: str = None):
        """Print with optional color"""
        if color:
            print(f"{color}{message}{self.NC}")
        else:
            print(message)
    
    def _get_pid(self, pid_file: Path) -> Optional[int]:
        """Get PID from file"""
        try:
            if pid_file.exists():
                return int(pid_file.read_text().strip())
        except:
            pass
        return None
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if process is running"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def _kill_process(self, pid: int, timeout: float = 5.0) -> bool:
        """Kill process gracefully, then forcefully if needed"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                # Force kill
                process.kill()
                process.wait(timeout=1.0)
                return True
        except psutil.NoSuchProcess:
            return True
        except Exception as e:
            self._print(f"Error killing process {pid}: {e}", self.RED)
            return False
    
    def _wait_for_port(self, port: int, timeout: float = 10.0) -> bool:
        """Wait for a port to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=0.5)
                return True
            except:
                time.sleep(0.5)
        return False
    
    def _check_backend_health(self) -> Tuple[bool, Optional[Dict]]:
        """Check backend health and return status"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                return True, response.json()
        except:
            pass
        return False, None
    
    def _check_frontend_health(self) -> bool:
        """Check if frontend is responding"""
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            return response.status_code < 500
        except:
            return False
    
    def start_backend(self) -> bool:
        """Start backend with detailed feedback"""
        # Check if already running
        pid = self._get_pid(self.backend_pid_file)
        if pid and self._is_process_running(pid):
            self._print(f"Backend already running (PID: {pid})", self.YELLOW)
            healthy, health_data = self._check_backend_health()
            if healthy:
                self._print("Backend health check: OK", self.GREEN)
                if health_data:
                    self._print(f"  Active agents: {health_data.get('active_agents', 'unknown')}")
                    self._print(f"  Database: {health_data.get('database', 'unknown')}")
            return True
        
        self._print("Starting backend...", self.GREEN)
        
        # Clear log
        self.backend_log.write_text("")
        
        # Start process
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_dir)
        
        process = subprocess.Popen(
            [str(self.venv_dir / "bin" / "python"), "-m", "uvicorn", "api.main:app", 
             "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(self.project_dir),
            env=env,
            stdout=open(self.backend_log, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if sys.platform != 'win32' else None
        )
        
        # Save PID
        self.backend_pid_file.write_text(str(process.pid))
        
        # Wait for startup
        self._print("Waiting for backend startup...", self.BLUE)
        start_time = time.time()
        startup_complete = False
        errors_found = []
        
        while time.time() - start_time < 10:
            # Check log for startup message
            try:
                log_content = self.backend_log.read_text()
                if "Application startup complete" in log_content:
                    startup_complete = True
                    break
                
                # Check for errors
                for line in log_content.splitlines():
                    if any(err in line for err in ["ERROR", "CRITICAL", "Exception", "Traceback"]):
                        errors_found.append(line)
                
                # Check if process died
                if not self._is_process_running(process.pid):
                    self._print("Backend process died during startup!", self.RED)
                    if errors_found:
                        self._print("Errors found:", self.RED)
                        for err in errors_found[-5:]:  # Last 5 errors
                            self._print(f"  {err}")
                    else:
                        self._print("Check logs for details:", self.YELLOW)
                        # Show last 10 lines of log
                        lines = log_content.splitlines()[-10:]
                        for line in lines:
                            self._print(f"  {line}")
                    return False
                    
            except:
                pass
            
            time.sleep(0.5)
        
        if startup_complete:
            self._print(f"Backend started successfully (PID: {process.pid})", self.GREEN)
            
            # Quick health check
            time.sleep(0.5)
            healthy, health_data = self._check_backend_health()
            if healthy:
                self._print("Health check: OK", self.GREEN)
            else:
                self._print("Health check: Backend started but not responding yet", self.YELLOW)
            
            if errors_found:
                self._print(f"Warnings found ({len(errors_found)}):", self.YELLOW)
                for err in errors_found[-3:]:
                    self._print(f"  {err}")
            
            return True
        else:
            self._print("Backend startup timeout - may still be starting", self.YELLOW)
            return True
    
    def start_frontend(self) -> bool:
        """Start frontend with detailed feedback"""
        # Check if already running
        pid = self._get_pid(self.frontend_pid_file)
        if pid and self._is_process_running(pid):
            self._print(f"Frontend already running (PID: {pid})", self.YELLOW)
            if self._check_frontend_health():
                self._print("Frontend health check: OK", self.GREEN)
            return True
        
        self._print("Starting frontend...", self.GREEN)
        
        # Check dependencies
        web_dir = self.project_dir / "web"
        if not (web_dir / "node_modules").exists():
            self._print("Installing frontend dependencies...", self.YELLOW)
            result = subprocess.run(
                ["npm", "install", "--legacy-peer-deps"],
                cwd=str(web_dir),
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self._print("Failed to install dependencies!", self.RED)
                self._print(result.stderr)
                return False
        
        # Clear log
        self.frontend_log.write_text("")
        
        # Start process
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=str(web_dir),
            env=os.environ.copy(),
            stdout=open(self.frontend_log, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if sys.platform != 'win32' else None
        )
        
        # Save PID
        self.frontend_pid_file.write_text(str(process.pid))
        
        # Wait for startup
        self._print("Waiting for frontend compilation...", self.BLUE)
        start_time = time.time()
        compiled = False
        
        while time.time() - start_time < 30:  # Frontend takes longer
            try:
                log_content = self.frontend_log.read_text()
                if any(msg in log_content for msg in ["Compiled successfully", "webpack compiled", "On Your Network"]):
                    compiled = True
                    break
                
                # Check if process died
                if not self._is_process_running(process.pid):
                    self._print("Frontend process died during startup!", self.RED)
                    # Show last 20 lines
                    lines = log_content.splitlines()[-20:]
                    for line in lines:
                        self._print(f"  {line}")
                    return False
                    
            except:
                pass
            
            time.sleep(1)
        
        if compiled:
            self._print(f"Frontend started successfully (PID: {process.pid})", self.GREEN)
            self._print("Frontend URL: http://localhost:3000", self.GREEN)
            return True
        else:
            self._print("Frontend compilation timeout - may still be compiling", self.YELLOW)
            return True
    
    def stop_backend(self) -> bool:
        """Stop backend"""
        pid = self._get_pid(self.backend_pid_file)
        if pid and self._is_process_running(pid):
            self._print(f"Stopping backend (PID: {pid})...", self.YELLOW)
            if self._kill_process(pid):
                self.backend_pid_file.unlink(missing_ok=True)
                self._print("Backend stopped", self.GREEN)
                return True
            else:
                self._print("Failed to stop backend", self.RED)
                return False
        else:
            self._print("Backend is not running", self.YELLOW)
            self.backend_pid_file.unlink(missing_ok=True)
            return True
    
    def stop_frontend(self) -> bool:
        """Stop frontend"""
        pid = self._get_pid(self.frontend_pid_file)
        if pid and self._is_process_running(pid):
            self._print(f"Stopping frontend (PID: {pid})...", self.YELLOW)
            if self._kill_process(pid):
                self.frontend_pid_file.unlink(missing_ok=True)
                self._print("Frontend stopped", self.GREEN)
                return True
            else:
                self._print("Failed to stop frontend", self.RED)
                return False
        else:
            self._print("Frontend is not running", self.YELLOW)
            self.frontend_pid_file.unlink(missing_ok=True)
            return True
    
    def restart_backend(self) -> bool:
        """Restart backend quickly"""
        self.stop_backend()
        time.sleep(0.5)  # Brief pause
        return self.start_backend()
    
    def restart_frontend(self) -> bool:
        """Restart frontend quickly"""
        self.stop_frontend()
        time.sleep(0.5)  # Brief pause
        return self.start_frontend()
    
    def status(self) -> None:
        """Show detailed status"""
        self._print("=== Agent System Status ===", self.GREEN)
        
        # Backend
        backend_pid = self._get_pid(self.backend_pid_file)
        if backend_pid and self._is_process_running(backend_pid):
            self._print(f"Backend:  Running (PID: {backend_pid})", self.GREEN)
            healthy, health_data = self._check_backend_health()
            if healthy:
                self._print("  Health: OK", self.GREEN)
                if health_data:
                    tm = health_data.get('task_manager', {})
                    self._print(f"  Running agents: {tm.get('running_agents', 0)}")
                    self._print(f"  Queued tasks: {tm.get('queued_tasks', 0)}")
            else:
                self._print("  Health: Not responding", self.YELLOW)
        else:
            self._print("Backend:  Stopped", self.RED)
        
        # Frontend
        frontend_pid = self._get_pid(self.frontend_pid_file)
        if frontend_pid and self._is_process_running(frontend_pid):
            self._print(f"Frontend: Running (PID: {frontend_pid})", self.GREEN)
            if self._check_frontend_health():
                self._print("  Health: OK", self.GREEN)
            else:
                self._print("  Health: Not responding", self.YELLOW)
        else:
            self._print("Frontend: Stopped", self.RED)
    
    def logs(self, service: str = "both", lines: int = 20) -> None:
        """Show recent logs"""
        if service in ["backend", "both"]:
            self._print(f"=== Backend Log (last {lines} lines) ===", self.GREEN)
            try:
                log_lines = self.backend_log.read_text().splitlines()[-lines:]
                for line in log_lines:
                    print(line)
            except:
                self._print("No backend log available", self.YELLOW)
        
        if service in ["frontend", "both"]:
            if service == "both":
                print()  # Separator
            self._print(f"=== Frontend Log (last {lines} lines) ===", self.GREEN)
            try:
                log_lines = self.frontend_log.read_text().splitlines()[-lines:]
                for line in log_lines:
                    print(line)
            except:
                self._print("No frontend log available", self.YELLOW)


def main() -> None:
    """CLI interface"""
    manager = ServiceManager()
    
    if len(sys.argv) < 2:
        print("Usage: service_manager.py {start|stop|restart|status|logs} [service] [options]")
        print("\nCommands:")
        print("  start [backend|frontend|all]    - Start services")
        print("  stop [backend|frontend|all]     - Stop services")
        print("  restart [backend|frontend|all]  - Restart services")
        print("  status                          - Show service status")
        print("  logs [backend|frontend|both] [lines] - Show logs")
        sys.exit(1)
    
    command = sys.argv[1]
    service = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    if command == "start":
        if service in ["backend", "all"]:
            manager.start_backend()
        if service in ["frontend", "all"]:
            if service == "all":
                print()  # Separator
            manager.start_frontend()
    
    elif command == "stop":
        if service in ["frontend", "all"]:
            manager.stop_frontend()
        if service in ["backend", "all"]:
            manager.stop_backend()
    
    elif command == "restart":
        if service in ["backend", "all"]:
            manager.restart_backend()
        if service in ["frontend", "all"]:
            if service == "all":
                print()  # Separator
            manager.restart_frontend()
    
    elif command == "status":
        manager.status()
    
    elif command == "logs":
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        manager.logs(service, lines)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()