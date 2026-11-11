"""
Airflow ETL Pipeline for Frankfurter Currency Rates to MongoDB.
"""

from datetime import datetime, timedelta
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
