"""
scripts/config.py
====================
Configuration centrale du projet : villes suivies, chemins de stockage.
"""

import os

VILLES = [
    {"nom": "Antananarivo", "pays": "MG", "lat": -18.8792, "lon": 47.5079},
    {"nom": "Delhi",        "pays": "IN", "lat": 28.7041,  "lon": 77.1025},
    {"nom": "Paris",        "pays": "FR", "lat": 48.8566,  "lon": 2.3522},
    {"nom": "Los Angeles",  "pays": "US", "lat": 34.0522,  "lon": -118.2437},
    {"nom": "Beijing",      "pays": "CN", "lat": 39.9042,  "lon": 116.4074},
]


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")


def safe_name(ville_nom: str) -> str:
    return ville_nom.lower().replace(" ", "_")
