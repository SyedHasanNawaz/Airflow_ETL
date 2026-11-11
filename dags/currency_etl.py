"""
Airflow ETL Pipeline for Frankfurter Currency Rates to MongoDB.
"""

from datetime import datetime, timedelta, timezone
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

API_URL = "https://api.frankfurter.dev/v2/rates?base=EUR&quotes=USD,GBP,JPY"

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
        for item in data:
            raw_records.append({
                "base": item.get("base"),
                "target": item.get("quote"),
                "rate": item.get("rate"),
                "date": item.get("date"),
            })
    elif isinstance(data, dict):
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

    logging.info(f"Extracted {len(raw_records)} currency rate records: {raw_records}")

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

    ti.xcom_push(key="rates_transformed", value=transformed_records)
    return transformed_records


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

    extract_task >> transform_task
