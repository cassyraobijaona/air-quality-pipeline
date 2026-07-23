"""
dags/air_quality_pipeline_dag.py
===================================
Pipeline horaire de qualité de l'air.

  extract_antananarivo  \
  extract_delhi          \
  extract_paris           >----  clean_task  ---->  load_warehouse_task
  extract_los_angeles    /
  extract_beijing        /

- 5 tâches d'extraction en parallèle (une par ville), tolérantes aux pannes
- clean_task reconstruit data/clean/qualite_air_clean.csv depuis TOUT data/raw/
- load_warehouse_task recharge le data warehouse Supabase
"""

import os
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

CONTAINER_DIR = "/opt/airflow"
LOCAL_DIR = os.path.expanduser("~/air-quality-pipeline")
PROJECT_DIR = CONTAINER_DIR if os.path.isdir(os.path.join(CONTAINER_DIR, "scripts")) else LOCAL_DIR
sys.path.append(PROJECT_DIR)

from scripts.config import VILLES, safe_name
from scripts.extract_current import extract_current
from scripts.clean import build_clean_csv
from scripts.load_warehouse import load_warehouse

default_args = {
    "start_date": datetime(2026, 7, 1),
    "retries": 1,
}

with DAG(
    dag_id="air_quality_pipeline_dag",
    schedule="@hourly",
    default_args=default_args,
    catchup=False,
    tags=["etl", "qualite-air", "warehouse"],
) as dag:

    extract_tasks = []
    for ville in VILLES:
        safe_id = safe_name(ville["nom"])
        t = PythonOperator(
            task_id=f"extract_{safe_id}",
            python_callable=extract_current,
            op_kwargs={"ville_nom": ville["nom"]},
        )
        extract_tasks.append(t)

    clean_task = PythonOperator(
        task_id="clean_task",
        python_callable=build_clean_csv,
    )

    load_warehouse_task = PythonOperator(
        task_id="load_warehouse_task",
        python_callable=load_warehouse,
    )

    extract_tasks >> clean_task >> load_warehouse_task
