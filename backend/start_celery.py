#!/usr/bin/env python3
"""
Celery Worker Startup Script
Usage: python start_celery.py [worker|beat|flower]
"""

import sys
import os
import subprocess
from app.config import settings

def start_worker():
    """Start Celery worker"""
    cmd = [
        "celery",
        "-A", "app.celery_app",
        "worker",
        "--loglevel=info",
        f"--concurrency={settings.max_concurrent_backtests}",
        "--queues=backtest,strategy,analytics",
        "--pool=threads"  # Use threads for async compatibility
    ]
    
    if not settings.is_production:
        cmd.extend(["--reload"])  # Auto-reload in development
    
    print(f"Starting Celery worker with command: {' '.join(cmd)}")
    subprocess.run(cmd)

def start_beat():
    """Start Celery beat scheduler"""
    cmd = [
        "celery",
        "-A", "app.celery_app",
        "beat",
        "--loglevel=info"
    ]
    
    print(f"Starting Celery beat with command: {' '.join(cmd)}")
    subprocess.run(cmd)

def start_flower():
    """Start Flower monitoring"""
    cmd = [
        "celery",
        "-A", "app.celery_app",
        "flower",
        "--port=5555"
    ]
    
    print(f"Starting Flower monitoring with command: {' '.join(cmd)}")
    print("Flower will be available at: http://localhost:5555")
    subprocess.run(cmd)

def start_all():
    """Start all Celery services in development"""
    print("Starting all Celery services for development...")
    
    # In production, these should be separate services
    import multiprocessing
    
    worker_process = multiprocessing.Process(target=start_worker)
    beat_process = multiprocessing.Process(target=start_beat)
    flower_process = multiprocessing.Process(target=start_flower)
    
    try:
        worker_process.start()
        beat_process.start()
        flower_process.start()
        
        # Wait for all processes
        worker_process.join()
        beat_process.join()
        flower_process.join()
        
    except KeyboardInterrupt:
        print("\nShutting down Celery services...")
        worker_process.terminate()
        beat_process.terminate()
        flower_process.terminate()

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python start_celery.py [worker|beat|flower|all]")
        print("\nCommands:")
        print("  worker  - Start Celery worker for task processing")
        print("  beat    - Start Celery beat for scheduled tasks")
        print("  flower  - Start Flower for monitoring")
        print("  all     - Start all services (development only)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "worker":
        start_worker()
    elif command == "beat":
        start_beat()
    elif command == "flower":
        start_flower()
    elif command == "all":
        start_all()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 