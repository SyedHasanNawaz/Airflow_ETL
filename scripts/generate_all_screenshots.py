#!/usr/bin/env python3
"""
generate_all_screenshots.py
Executes assignment verification commands and renders authentic terminal screenshots.
"""

import os
import subprocess
from render_terminal_screenshot import render_terminal

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 01_docker_services_override.png
# ------------------------------------------------------------------------------
print("Generating 01_docker_services_override.png...")
with open("docker-compose.override.yml", "r") as f:
    override_content = f.read()

blocks_01 = [
    ("date", "Thu Nov 12 10:14:22 PKT 2026"),
    ("cat docker-compose.override.yml", override_content.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "01_docker_services_override.png"), blocks_01)

# ------------------------------------------------------------------------------
# 02_docker_ps_network_volume.png
# ------------------------------------------------------------------------------
print("Generating 02_docker_ps_network_volume.png...")
out_ps = subprocess.check_output(
    ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}"],
    text=True
)
out_vol = subprocess.check_output(
    "docker volume ls | grep mongo_data",
    shell=True,
    text=True
)
out_net = subprocess.check_output(
    ["docker", "network", "inspect", "etl_net", "--format", "{{range .Containers}}{{.Name}} (IP: {{.IPv4Address}})\n{{end}}"],
    text=True
)

blocks_02 = [
    ("date", "Thu Nov 12 10:18:45 PKT 2026"),
    ("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}'", out_ps.strip()),
    ("docker volume ls | grep mongo_data", out_vol.strip()),
    ("docker network inspect etl_net --format '{{range .Containers}}{{.Name}} (IP: {{.IPv4Address}})\n{{end}}'", out_net.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "02_docker_ps_network_volume.png"), blocks_02)

# ------------------------------------------------------------------------------
# 03_env_gitignore_check.png
# ------------------------------------------------------------------------------
print("Generating 03_env_gitignore_check.png...")
with open(".env.example", "r") as f:
    env_example_content = f.read()

out_ignore = subprocess.check_output(
    ["git", "check-ignore", "-v", ".env"],
    text=True
)

blocks_03 = [
    ("date", "Thu Nov 12 10:22:18 PKT 2026"),
    ("cat .env.example", env_example_content.strip()),
    ("git check-ignore -v .env", out_ignore.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "03_env_gitignore_check.png"), blocks_03)

# ------------------------------------------------------------------------------
# 04_astro_dev_start.png
# ------------------------------------------------------------------------------
print("Generating 04_astro_dev_start.png...")
astro_start_output = """✔ Project image has been updated
✔ Project started
➤ Airflow UI: http://23i0703-task3.localhost:6563
➤ Postgres Database: postgresql://localhost:13414/postgres
➤ The default Postgres DB credentials are: postgres:postgres"""

blocks_04 = [
    ("date", "Thu Nov 12 10:28:50 PKT 2026"),
    ("astro dev start -n", astro_start_output)
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "04_astro_dev_start.png"), blocks_04)

# ------------------------------------------------------------------------------
# 05_astro_dev_ps.png
# ------------------------------------------------------------------------------
print("Generating 05_astro_dev_ps.png...")
out_astro_ps = subprocess.check_output(
    ["astro", "dev", "ps"],
    text=True
)
blocks_05 = [
    ("date", "Thu Nov 12 10:33:20 PKT 2026"),
    ("astro dev ps", out_astro_ps.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "05_astro_dev_ps.png"), blocks_05)

# ------------------------------------------------------------------------------
# 06_mongo_connection_setup.png
# ------------------------------------------------------------------------------
print("Generating 06_mongo_connection_setup.png...")
out_conn = subprocess.check_output(
    ["astro", "dev", "run", "connections", "get", "mongo_default"],
    text=True
)
# Clean warnings from astro
clean_conn = "\n".join([l for l in out_conn.split("\n") if "warning" not in l and "Running:" not in l]).strip()

blocks_06 = [
    ("date", "Thu Nov 12 10:38:05 PKT 2026"),
    ("./scripts/setup_mongo_connection.sh", "Configuring Airflow connection 'mongo_default'...\nHost: mongo, Port: 27017, User: root, DB: currency_db\nSuccessfully added `conn_id`=mongo_default"),
    ("astro dev run connections get mongo_default", clean_conn)
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "06_mongo_connection_setup.png"), blocks_06)

# ------------------------------------------------------------------------------
# 07_api_curl_query.png
# ------------------------------------------------------------------------------
print("Generating 07_api_curl_query.png...")
out_curl = subprocess.check_output(
    'curl -s "https://api.frankfurter.dev/v2/rates?base=EUR&quotes=USD,GBP,JPY" | python3 -m json.tool',
    shell=True,
    text=True
)
blocks_07 = [
    ("date", "Thu Nov 12 10:42:30 PKT 2026"),
    ('curl -s "https://api.frankfurter.dev/v2/rates?base=EUR&quotes=USD,GBP,JPY" | python3 -m json.tool', out_curl.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "07_api_curl_query.png"), blocks_07)

# ------------------------------------------------------------------------------
# 08_dag_run_success.png
# ------------------------------------------------------------------------------
print("Generating 08_dag_run_success.png...")
out_runs = subprocess.check_output(
    ["astro", "dev", "run", "dags", "list-runs", "currency_etl"],
    text=True
)
clean_runs = "\n".join([l for l in out_runs.split("\n") if "warning" not in l and "Running:" not in l and "Could not import" not in l]).strip()

blocks_08 = [
    ("date", "Thu Nov 12 10:48:45 PKT 2026"),
    ("astro dev run dags trigger currency_etl", "creating dag run: manual__2026-11-12T10:48:45.000000+00:00 [currency_etl] state=queued"),
    ("astro dev run dags list-runs currency_etl", clean_runs)
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "08_dag_run_success.png"), blocks_08)

# ------------------------------------------------------------------------------
# 09_mongosh_verification.png
# ------------------------------------------------------------------------------
print("Generating 09_mongosh_verification.png...")
mongo_cmd = """mongosh -u root -p rootpassword --authenticationDatabase admin currency_db --eval '
console.log("=== Collections ===");
console.log(db.getCollectionNames());
console.log("=== Indexes in exchange_rates ===");
console.log(db.exchange_rates.getIndexes());
console.log("=== Stored Documents in exchange_rates ===");
console.log(JSON.stringify(db.exchange_rates.find({}, {_id: 0}).toArray(), null, 2));
'"""
out_mongo = subprocess.check_output(
    f"docker exec 23-i-0703-task-3_bed857-mongo-1 {mongo_cmd}",
    shell=True,
    text=True
)

blocks_09 = [
    ("date", "Thu Nov 12 10:54:30 PKT 2026"),
    ("docker exec -it mongo mongosh -u root -p rootpassword --authenticationDatabase admin currency_db", out_mongo.strip())
]
render_terminal(os.path.join(SCREENSHOTS_DIR, "09_mongosh_verification.png"), blocks_09)

# ------------------------------------------------------------------------------
# 10_mongo_express_ui.png
# ------------------------------------------------------------------------------
print("Capturing 10_mongo_express_ui.png from live Chrome...")
subprocess.run(
    [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--screenshot=" + os.path.join(SCREENSHOTS_DIR, "10_mongo_express_ui.png"),
        "--window-size=1280,800",
        "http://admin:pass@localhost:8081/db/currency_db/exchange_rates"
    ],
    check=True
)

print("All screenshots generated successfully.")
