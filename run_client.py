"""ArtizBoard Client — Entry point for flet pack / flet build.

Usage: python run_client.py
Build:  flet pack run_client.py --name "ArtizBoard Client"
        flet build apk run_client.py --name "ArtizBoard Client"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.client.__main__ import main

if __name__ == "__main__":
    import flet
    flet.app(target=main)
