"""
scripts/clean.py
===================
Lit TOUS les fichiers JSON bruts dans data/raw/, les transforme en un
unique CSV propre dans data/clean/ : une ligne par ville et par heure,
triée chronologiquement, sans doublons.

Reconstruit ENTIÈREMENT clean/ à chaque exécution à partir de raw/
(raw/ n'est jamais modifié).

Usage :
    python scripts/clean.py
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime, timezone

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import VILLES, RAW_DIR, CLEAN_DIR, safe_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CLEAN_FILENAME = "qualite_air_clean.csv"


def load_raw_files_for_ville(ville: dict) -> list[dict]:
    """Lit tous les fichiers JSON bruts d'une ville et les transforme en lignes plates."""
    safe = safe_name(ville["nom"])
    ville_dir = os.path.join(RAW_DIR, safe)

    if not os.path.isdir(ville_dir):
        logger.warning(f"[clean] Aucun dossier brut trouvé pour '{ville['nom']}' ({ville_dir})")
        return []

    fichiers = glob.glob(os.path.join(ville_dir, "*.json"))
    lignes = []

    for fichier in fichiers:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)

        for point in data.get("list", []):
            dt_unix = point.get("dt")
            main = point.get("main", {})
            comp = point.get("components", {})

            lignes.append({
                "ville": ville["nom"],
                "pays": ville["pays"],
                "latitude": ville["lat"],
                "longitude": ville["lon"],
                "timestamp_unix": dt_unix,
                "timestamp": datetime.fromtimestamp(dt_unix, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "aqi": main.get("aqi"),
                "co": comp.get("co"),
                "no": comp.get("no"),
                "no2": comp.get("no2"),
                "o3": comp.get("o3"),
                "so2": comp.get("so2"),
                "pm2_5": comp.get("pm2_5"),
                "pm10": comp.get("pm10"),
                "nh3": comp.get("nh3"),
            })

    return lignes


def build_clean_csv() -> str:
    toutes_les_lignes = []

    for ville in VILLES:
        logger.info(f"Lecture des fichiers bruts : {ville['nom']}...")
        lignes = load_raw_files_for_ville(ville)
        logger.info(f"  {len(lignes)} points lus")
        toutes_les_lignes.extend(lignes)

    if not toutes_les_lignes:
        raise RuntimeError("Aucune donnée brute trouvée. As-tu lancé backfill.py avant ?")

    df = pd.DataFrame(toutes_les_lignes)

    avant = len(df)
    df = df.drop_duplicates(subset=["ville", "timestamp_unix"])
    apres = len(df)
    if avant != apres:
        logger.info(f"  {avant - apres} doublon(s) supprimé(s)")

    df = df.sort_values(["ville", "timestamp_unix"]).reset_index(drop=True)

    os.makedirs(CLEAN_DIR, exist_ok=True)
    output_path = os.path.join(CLEAN_DIR, CLEAN_FILENAME)
    df.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(f"clean/ reconstruit -> {output_path} ({len(df)} lignes)")
    print(f"\n=== Résumé ===")
    print(f"Total : {len(df)} lignes")
    print(df.groupby("ville").size())

    return output_path


if __name__ == "__main__":
    build_clean_csv()
