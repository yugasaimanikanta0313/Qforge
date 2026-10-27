"""
QForge — Convenience Launcher
Run the FastAPI server with auto-reload from the project root.

Usage:
    D:\\QForge\\venv\\Scripts\\python.exe run.py
"""
import uvicorn
import sys
import os

# Ensure project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"],
        log_level="info",
    )
