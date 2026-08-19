import subprocess
import psycopg2
import re
import socket
import time
import os

# DB_HOST defaults to localhost (for the instance running Postgres itself).
# On other instances, set the environment variable before running, e.g.:
#   export NETMON_DB_HOST=10.0.1.227
DB_HOST = os.environ.get("NETMON_DB_HOST", "localhost")
DB_NAME = "netmon"
DB_USER = "netmon"
DB_PASSWORD = "netmon_pw"


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return result.stdout


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def ensure_instance_registered(conn, name):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO instances (name, role) VALUES (%s, %s) "
        "ON CONFLICT (name) DO NOTHING",
        (name, "agent")
    )
    conn.commit()
    cur.close()


def record_ping(conn, instance_name, target="8.8.8.8"):
    output = run_cmd(f"ping -c 4 {target}")
    match = re.search(r"time=([\d.]+)", output)
    latency = float(match.group(1)) if match else None

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO network_checks (instance_id, check_type, target, latency_ms, raw_output) "
        "VALUES ((SELECT id FROM instances WHERE name=%s), 'ping', %s, %s, %s)",
        (instance_name, target, latency, output)
    )
    conn.commit()
    cur.close()
    print(f"Recorded ping to {target}: latency={latency}ms")


def record_disk_usage(conn, instance_name):
    output = run_cmd("df -h / | tail -1")
    match = re.search(r"(\d+)%", output)
    usage_pct = float(match.group(1)) if match else None

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO system_metrics (instance_id, disk_usage_pct) "
        "VALUES ((SELECT id FROM instances WHERE name=%s), %s)",
        (instance_name, usage_pct)
    )
    conn.commit()
    cur.close()
    print(f"Recorded disk usage: {usage_pct}%")


def record_open_ports(conn, instance_name):
    output = run_cmd("ss -tulwn")

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO system_metrics (instance_id, open_ports) "
        "VALUES ((SELECT id FROM instances WHERE name=%s), %s)",
        (instance_name, output)
    )
    conn.commit()
    cur.close()
    print("Recorded open ports")


def record_traceroute(conn, instance_name, target="8.8.8.8"):
    output = run_cmd(f"traceroute -m 10 {target}")

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO network_checks (instance_id, check_type, target, raw_output) "
        "VALUES ((SELECT id FROM instances WHERE name=%s), 'traceroute', %s, %s)",
        (instance_name, target, output)
    )
    conn.commit()
    cur.close()
    print(f"Recorded traceroute to {target}")


def main():
    instance_name = socket.gethostname()
    conn = get_db_connection()
    ensure_instance_registered(conn, instance_name)

    while True:
        record_ping(conn, instance_name)
        record_disk_usage(conn, instance_name)
        record_open_ports(conn, instance_name)
        record_traceroute(conn, instance_name)
        time.sleep(60)


if __name__ == "__main__":
    main()
