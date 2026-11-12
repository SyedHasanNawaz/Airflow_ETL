"""
Airflow ETL Pipeline for Frankfurter Currency Rates to MongoDB.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import os
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
import pymongo
import requests

API_URL = "https://api.frankfurter.dev/v2/rates?base=EUR&quotes=USD,GBP,JPY"
COLLECTION_NAME = "exchange_rates"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def extract_currency_rates(**context):
    """
    Task 1 (Extract):
    Calls the Frankfurter API, extracts exchange rate data, ensures one row per
    target currency, and pushes to named XCom 'rates_raw'.
    """
    logging.info(f"Extracting exchange rate data from {API_URL}")
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    logging.info(f"Received API payload: {data}")

    raw_records = []
    if isinstance(data, list):
        # API v2 format: list of dicts: [{'date': '...', 'base': 'EUR', 'quote': 'USD', 'rate': 1.15}, ...]
        for item in data:
            raw_records.append({
                "base": item.get("base"),
                "target": item.get("quote"),
                "rate": item.get("rate"),
                "date": item.get("date"),
            })
    elif isinstance(data, dict):
        # API v1 format: {'base': 'EUR', 'date': '...', 'rates': {'USD': 1.15, ...}}
        base = data.get("base", "EUR")
        date_val = data.get("date")
        rates = data.get("rates", {})
        for target, rate in rates.items():
            raw_records.append({
                "base": base,
                "target": target,
                "rate": rate,
                "date": date_val,
            })
    else:
        raise ValueError(f"Unexpected response format from API: {type(data)}")

    logging.info(f"Extracted {len(raw_records)} currency rate records: {raw_records}")

    # Push via named XCom 'rates_raw'
    ti = context["ti"]
    ti.xcom_push(key="rates_raw", value=raw_records)
    return raw_records


def transform_currency_rates(**context):
    """
    Task 2 (Transform):
    Pulls 'rates_raw' from named XCom, enriches each record with source and
    retrieved_at ISO timestamp, parses rate_date, and validates exact schema.
    Pushes to named XCom 'rates_transformed'.
    """
    ti = context["ti"]
    raw_records = ti.xcom_pull(task_ids="extract", key="rates_raw")

    if not raw_records:
        raise ValueError("No records pulled from XCom 'rates_raw'")

    logging.info(f"Pulling {len(raw_records)} records from named XCom 'rates_raw'")

    transformed_records = []
    # Current UTC retrieval timestamp in ISO format: YYYY-MM-DDTHH:MM:SS
    retrieval_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    for item in raw_records:
        base = item.get("base") or item.get("base_currency")
        target = item.get("target") or item.get("target_currency")
        rate = float(item.get("rate") or item.get("exchange_rate"))
        rate_date = str(item.get("date") or item.get("rate_date"))

        record = {
            "base_currency": str(base),
            "target_currency": str(target),
            "exchange_rate": rate,
            "rate_date": rate_date,
            "source": "Frankfurter API",
            "retrieved_at": retrieval_iso,
        }
        transformed_records.append(record)

    logging.info(f"Successfully transformed {len(transformed_records)} records: {transformed_records}")

    # Push via named XCom 'rates_transformed'
    ti.xcom_push(key="rates_transformed", value=transformed_records)
    return transformed_records


def load_currency_rates(**context):
    """
    Task 3 (Load):
    Pulls 'rates_transformed' from named XCom, ensures compound unique index on
    base_currency + target_currency + rate_date, and upserts into MongoDB.
    """
    ti = context["ti"]
    transformed_records = ti.xcom_pull(task_ids="transform", key="rates_transformed")

    if not transformed_records:
        raise ValueError("No records pulled from XCom 'rates_transformed'")

    logging.info(f"Pulling {len(transformed_records)} records from named XCom 'rates_transformed'")

    # Retrieve connection settings from Airflow connection 'mongo_default'
    try:
        conn = BaseHook.get_connection("mongo_default")
        user = conn.login or os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
        password = conn.password or os.getenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")
        host = conn.host or os.getenv("MONGO_HOST", "mongo")
        port = conn.port or int(os.getenv("MONGO_PORT", 27017))
        db_name = conn.schema or os.getenv("MONGO_DB", "currency_db")
    except Exception as e:
        logging.warning(f"Could not load mongo_default from Airflow meta-db: {e}. Falling back to environment variables.")
        user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
        password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")
        host = os.getenv("MONGO_HOST", "mongo")
        port = int(os.getenv("MONGO_PORT", 27017))
        db_name = os.getenv("MONGO_DB", "currency_db")

    mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}?authSource=admin"
    logging.info(f"Connecting to MongoDB at {host}:{port}, db: {db_name}, collection: {COLLECTION_NAME}")

    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    collection = db[COLLECTION_NAME]

    # Ensure compound unique index: base_currency + target_currency + rate_date
    index_keys = [
        ("base_currency", pymongo.ASCENDING),
        ("target_currency", pymongo.ASCENDING),
        ("rate_date", pymongo.ASCENDING)
    ]
    index_name = collection.create_index(index_keys, unique=True, name="idx_base_target_date_unique")
    logging.info(f"Verified unique index: {index_name}")

    # Upsert each record
    upserted_count = 0
    modified_count = 0
    for record in transformed_records:
        filter_query = {
            "base_currency": record["base_currency"],
            "target_currency": record["target_currency"],
            "rate_date": record["rate_date"]
        }
        update_doc = {"$set": record}
        result = collection.update_one(filter_query, update_doc, upsert=True)
        if result.upserted_id:
            upserted_count += 1
            logging.info(f"Inserted new record: {record}")
        else:
            modified_count += 1
            logging.info(f"Updated existing record: {record}")

    total_in_db = collection.count_documents({})
    logging.info(f"Load complete. Upserted: {upserted_count}, Modified: {modified_count}, Total collection records: {total_in_db}")

    return {
        "upserted": upserted_count,
        "modified": modified_count,
        "total_in_collection": total_in_db
    }


with DAG(
    dag_id="currency_etl",
    default_args=default_args,
    description="Daily ETL pipeline fetching exchange rates from Frankfurter API to MongoDB",
    schedule="@daily",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    tags=["etl", "currency", "frankfurter", "mongodb"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract_currency_rates,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform_currency_rates,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load_currency_rates,
    )

    extract_task >> transform_task >> load_task
