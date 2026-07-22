"""
scripts/load_warehouse.py
============================
Charge data/clean/qualite_air_clean.csv dans le data warehouse (PostgreSQL/Supabase),
selon un schéma en étoile :
  - dim_temps : une ligne par heure distincte
  - dim_ville : une ligne par ville
  - fait_qualite_air : les mesures, avec FK vers les 2 dimensions

Rejouable : les tables sont recréées à chaque exécution (DROP puis CREATE),
pour rester cohérent avec clean/ qui est lui-même reconstruit à chaque run.

Usage :
    python scripts/load_warehouse.py
"""

import os
import sys
import logging

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import CLEAN_DIR

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CLEAN_CSV = os.path.join(CLEAN_DIR, "qualite_air_clean.csv")

DDL = """
DROP TABLE IF EXISTS fait_qualite_air;
DROP TABLE IF EXISTS dim_temps;
DROP TABLE IF EXISTS dim_ville;

CREATE TABLE dim_ville (
    id_ville   SERIAL PRIMARY KEY,
    nom        VARCHAR(100) NOT NULL,
    pays       VARCHAR(10) NOT NULL,
    latitude   DOUBLE PRECISION NOT NULL,
    longitude  DOUBLE PRECISION NOT NULL,
    UNIQUE (nom)
);

CREATE TABLE dim_temps (
    id_temps      BIGINT PRIMARY KEY,
    date          DATE NOT NULL,
    heure         SMALLINT NOT NULL,
    jour          SMALLINT NOT NULL,
    mois          SMALLINT NOT NULL,
    annee         SMALLINT NOT NULL,
    jour_semaine  VARCHAR(15) NOT NULL,
    est_weekend   BOOLEAN NOT NULL
);

CREATE TABLE fait_qualite_air (
    id         SERIAL PRIMARY KEY,
    id_temps   BIGINT NOT NULL REFERENCES dim_temps(id_temps),
    id_ville   INTEGER NOT NULL REFERENCES dim_ville(id_ville),
    aqi        SMALLINT,
    co         DOUBLE PRECISION,
    no         DOUBLE PRECISION,
    no2        DOUBLE PRECISION,
    o3         DOUBLE PRECISION,
    so2        DOUBLE PRECISION,
    pm2_5      DOUBLE PRECISION,
    pm10       DOUBLE PRECISION,
    nh3        DOUBLE PRECISION,
    UNIQUE (id_temps, id_ville)
);
"""


def get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL manquante — vérifie ton fichier .env")
    return create_engine(db_url)


def build_dim_ville(df: pd.DataFrame) -> pd.DataFrame:
    dim = (
        df[["ville", "pays", "latitude", "longitude"]]
        .drop_duplicates(subset=["ville"])
        .rename(columns={"ville": "nom"})
        .reset_index(drop=True)
    )
    return dim


def build_dim_temps(df: pd.DataFrame) -> pd.DataFrame:
    dt = pd.to_datetime(df["timestamp"])
    dim = pd.DataFrame({
        "id_temps": df["timestamp_unix"],
        "date": dt.dt.date,
        "heure": dt.dt.hour,
        "jour": dt.dt.day,
        "mois": dt.dt.month,
        "annee": dt.dt.year,
        "jour_semaine": dt.dt.day_name(),
        "est_weekend": dt.dt.dayofweek >= 5,
    }).drop_duplicates(subset=["id_temps"]).reset_index(drop=True)
    return dim


def load_warehouse():
    if not os.path.exists(CLEAN_CSV):
        raise RuntimeError(f"{CLEAN_CSV} introuvable — lance clean.py avant.")

    logger.info(f"Lecture de {CLEAN_CSV}...")
    df = pd.read_csv(CLEAN_CSV)
    logger.info(f"  {len(df)} lignes chargées")

    engine = get_engine()

    logger.info("(Re)création des tables...")
    with engine.begin() as conn:
        for statement in DDL.strip().split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

    dim_ville = build_dim_ville(df)
    dim_temps = build_dim_temps(df)

    logger.info(f"Chargement dim_ville ({len(dim_ville)} lignes)...")
    dim_ville[["nom", "pays", "latitude", "longitude"]].to_sql(
        "dim_ville", engine, if_exists="append", index=False
    )

    dim_ville_db = pd.read_sql("SELECT id_ville, nom FROM dim_ville", engine)
    fait = df.merge(dim_ville_db, left_on="ville", right_on="nom", how="left")
    fait = fait.rename(columns={"timestamp_unix": "id_temps"})[[
        "id_temps", "id_ville", "aqi", "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"
    ]]

    logger.info(f"Chargement dim_temps ({len(dim_temps)} lignes)...")
    dim_temps.to_sql("dim_temps", engine, if_exists="append", index=False)

    logger.info(f"Chargement fait_qualite_air ({len(fait)} lignes)...")
    fait.to_sql("fait_qualite_air", engine, if_exists="append", index=False)

    with engine.connect() as conn:
        nb_fait = conn.execute(text("SELECT COUNT(*) FROM fait_qualite_air")).scalar()
        nb_villes = conn.execute(text("SELECT COUNT(*) FROM dim_ville")).scalar()
        nb_temps = conn.execute(text("SELECT COUNT(*) FROM dim_temps")).scalar()

    print("\n=== Warehouse chargé ===")
    print(f"dim_ville        : {nb_villes} lignes")
    print(f"dim_temps        : {nb_temps} lignes")
    print(f"fait_qualite_air : {nb_fait} lignes")


if __name__ == "__main__":
    load_warehouse()
