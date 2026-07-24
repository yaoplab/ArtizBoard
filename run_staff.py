"""ArtizBoard Staff — Entry point for flet pack / flet build.

Usage: python run_staff.py
Build:  flet pack run_staff.py --name "ArtizBoard Staff"
        flet build apk run_staff.py --name "ArtizBoard Staff"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.staff.__main__ import main

if __name__ == "__main__":
    import flet
    flet.app(target=main)
