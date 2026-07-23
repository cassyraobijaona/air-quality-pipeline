"""
scripts/extract_current.py
=============================
Récupère la qualité de l'air ACTUELLE pour une ville, via l'endpoint
"Air Pollution" (temps réel) d'OpenWeatherMap.

Sauvegarde un fichier JSON brut dans data/raw/{ville}/ (même format que
le backfill), pour que clean.py puisse tout relire ensemble.

Conçu pour être appelé par le DAG Airflow, une fois par ville et par heure.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import VILLES, RAW_DIR, safe_name

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/air_pollution"


def extract_current(ville_nom: str):
    """Récupère la qualité de l'air actuelle pour une ville (par son nom) et sauvegarde le JSON brut."""
    ville = next((v for v in VILLES if v["nom"] == ville_nom), None)
    if ville is None:
        raise ValueError(f"Ville inconnue dans config.py : {ville_nom}")

    if not API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY manquante — vérifie ton fichier .env")

    params = {"lat": ville["lat"], "lon": ville["lon"], "appid": API_KEY}

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[extract_current] Échec pour '{ville_nom}' : {e}")
        print(f"ÉCHEC pour {ville_nom} : {e}")
        return None

    safe = safe_name(ville["nom"])
    ville_dir = os.path.join(RAW_DIR, safe)
    os.makedirs(ville_dir, exist_ok=True)

    now_unix = int(datetime.now(timezone.utc).timestamp())
    filename = os.path.join(ville_dir, f"{safe}_current_{now_unix}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK pour {ville_nom} -> {filename}")
    return filename


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ville", required=True)
    args = parser.parse_args()
    extract_current(args.ville)
