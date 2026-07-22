"""
scripts/backfill.py
======================
Récupère l'historique de qualité de l'air pour chaque ville, via l'endpoint
"Air Pollution History" d'OpenWeatherMap.

Un fichier JSON brut est sauvegardé PAR VILLE ET PAR APPEL dans data/raw/
(jamais modifié ensuite — c'est la zone de sauvegarde).

Usage :
    python scripts/backfill.py --months 3
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta, timezone

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import VILLES, API_KEY, RAW_DIR, safe_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5/air_pollution/history"


def fetch_history(ville, start_unix, end_unix):
    """Appelle l'API pour UNE ville sur une période donnée. Renvoie le JSON brut ou None si échec."""
    params = {
        "lat": ville["lat"],
        "lon": ville["lon"],
        "start": start_unix,
        "end": end_unix,
        "appid": API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[backfill] Échec pour '{ville['nom']}' : {e}")
        return None


def save_raw(ville, data, start_unix, end_unix):
    """Sauvegarde le JSON brut, sans le modifier, dans data/raw/{ville}/."""
    safe = safe_name(ville["nom"])
    ville_dir = os.path.join(RAW_DIR, safe)
    os.makedirs(ville_dir, exist_ok=True)

    filename = os.path.join(ville_dir, f"{safe}_backfill_{start_unix}_{end_unix}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename


def run_backfill(months=3):
    if not API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY manquante — vérifie ton fichier .env")

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=months * 30)

    start_unix = int(start_dt.timestamp())
    end_unix = int(end_dt.timestamp())

    logger.info(f"Backfill du {start_dt.date()} au {end_dt.date()} ({months} mois) pour {len(VILLES)} villes")

    resultats = []
    for ville in VILLES:
        logger.info(f"Récupération : {ville['nom']}...")
        data = fetch_history(ville, start_unix, end_unix)

        if data is None:
            resultats.append((ville["nom"], "ÉCHEC"))
            continue

        nb_points = len(data.get("list", []))
        filename = save_raw(ville, data, start_unix, end_unix)
        logger.info(f"  {nb_points} points -> {filename}")
        resultats.append((ville["nom"], f"OK ({nb_points} points)"))

        time.sleep(1)

    print("\n=== Résumé du backfill ===")
    for nom, statut in resultats:
        print(f"  {nom}: {statut}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=3, help="Nombre de mois d'historique à récupérer")
    args = parser.parse_args()

    run_backfill(months=args.months)
