"""
scripts/run_hourly.py
========================
Point d'entrée unique pour l'exécution horaire du pipeline, appelé par
GitHub Actions (orchestrateur).

Enchaîne : extraction (5 villes) -> reconstruction de clean/ -> chargement du warehouse.
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import VILLES
from scripts.extract_current import extract_current
from scripts.clean import build_clean_csv
from scripts.load_warehouse import load_warehouse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Début du run horaire ===")

    for ville in VILLES:
        extract_current(ville["nom"])

    logger.info("Extraction terminée. Reconstruction de clean/...")
    build_clean_csv()

    logger.info("Chargement du warehouse...")
    load_warehouse()

    logger.info("=== Run horaire terminé avec succès ===")


if __name__ == "__main__":
    main()
