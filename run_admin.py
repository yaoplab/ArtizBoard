"""ArtizBoard Admin — Entry point for flet pack / flet build.

Usage: python run_admin.py
Build:  flet pack run_admin.py --name "ArtizBoard Admin"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.admin.__main__ import main

if __name__ == "__main__":
    import flet
    flet.app(target=main)
