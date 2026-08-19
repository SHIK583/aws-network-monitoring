# AWS Multi-Instance Network Monitoring & Diagnostics System

A self-built monitoring system spanning two EC2 instances: a Python agent on each runs Linux network diagnostics, both report into a shared PostgreSQL database, and results are visualized in a live Grafana dashboard showing both instances side by side — built from scratch to understand AWS networking, Docker, SQL, and monitoring at a hands-on level, rather than relying on managed services.

## Live Dashboard

![Grafana Dashboard](dashboard-screenshot.png)

Real-time panels showing ping latency and disk usage over time, with a separate line per monitored instance — built directly on top of the PostgreSQL data collected by the Python agents running on each server.

## What it does

A Python agent runs on each EC2 instance and periodically executes diagnostic checks — `ping`, `df -h` (disk usage), `ss -tulwn` (open ports), and `traceroute` — parsing and storing the results in a central PostgreSQL database running in Docker. Every instance registers itself and its checks are linked back to it via a foreign key, so the dashboard can break out metrics per server. This creates a queryable, visualized history of network health and system metrics across multiple nodes.

## Architecture

- **AWS VPC** — custom-built network (not the default VPC) with a public subnet, Internet Gateway, and route table, configured manually to understand each networking layer
- **Two EC2 instances** (`netmon-agent-1`, `netmon-agent-2`) — Ubuntu 24.04 LTS servers in the same VPC/subnet; instance 1 also hosts the database and dashboard containers
- **EC2 Instance Connect Endpoint** — used for secure remote access over HTTPS (port 443) rather than direct SSH (port 22), after diagnosing that outbound SSH was blocked at the network/device level in my environment
- **Docker** — containerized PostgreSQL and Grafana, networked together via a shared Docker network
- **PostgreSQL** — stores diagnostic results in a normalized schema:
  - `instances` — registered servers being monitored
  - `network_checks` — ping/traceroute results (latency, target, raw output, timestamp)
  - `system_metrics` — disk usage and open ports over time
- **Python agent** — runs on each instance, collects diagnostics via `subprocess`, parses key metrics with regex, and writes to PostgreSQL via `psycopg2` (instance 2 connects to instance 1's database over the private VPC network)
- **systemd** — each agent runs as a persistent background service with automatic restart on failure
- **Grafana** — provides a live dashboard of latency and disk usage trends, split by instance

## Skills demonstrated

- AWS networking fundamentals: VPC, subnets, Internet Gateways, route tables, security groups
- Linux system administration and diagnostic tooling (`ping`, `df`, `ss`, `traceroute`, `ip`)
- Docker containerization and container-to-container networking
- SQL schema design with foreign key relationships
- Python scripting for automation and data collection across multiple hosts
- Linux service management (`systemd`) for persistent, self-healing background processes
- Real-world troubleshooting: diagnosed and resolved an SSH connectivity block caused by corporate network security policy, using AWS's HTTPS-based EC2 Instance Connect Endpoint as a workaround
- Data visualization and observability: connected Grafana to PostgreSQL via Docker networking to build live, multi-host monitoring dashboards
- Failure simulation and detection: used `iptables` to simulate a network outage and verified it was captured in collected data

## Sample data

```sql
SELECT id, check_type, target, latency_ms, checked_at FROM network_checks;

 id | check_type | target  | latency_ms |         checked_at
----+------------+---------+------------+----------------------------
  1 | ping       | 8.8.8.8 |       1.67 | 2026-07-26 05:43:31.635775
  2 | ping       | 8.8.8.8 |       1.63 | 2026-07-26 05:44:34.658253
  4 | traceroute | 8.8.8.8 |            | 2026-07-26 06:04:03.850037
```

## Setup

1. Provision a VPC with a public subnet, Internet Gateway, and route table
2. Launch an EC2 instance (Ubuntu 24.04) inside the subnet, with a security group allowing inbound SSH
3. Install Docker: `sudo apt install -y docker.io`
4. Run PostgreSQL in Docker:
   ```bash
   docker run -d --name netmon-db \
     -e POSTGRES_DB=netmon -e POSTGRES_USER=netmon -e POSTGRES_PASSWORD=netmon_pw \
     -p 5432:5432 postgres:15
   ```
5. Create the schema (see `schema.sql`)
6. Install dependencies: `pip3 install psycopg2-binary`
7. Run the agent: `python3 agent.py`
8. Run Grafana in Docker and connect it to Postgres:
   ```bash
   docker network create netmon-net
   docker network connect netmon-net netmon-db
   docker run -d --name netmon-grafana -p 3000:3000 grafana/grafana:latest
   docker network connect netmon-net netmon-grafana
   ```
   Then in Grafana (`http://<public-ip>:3000`), add a PostgreSQL data source with host `netmon-db:5432`, database `netmon`.
9. Set up the agent as a persistent service so it survives disconnects and reboots:
   ```bash
   sudo cp netmon-agent-db-host.service /etc/systemd/system/netmon-agent.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now netmon-agent
   ```

### Adding another instance to monitor

1. Launch a second EC2 instance in the same VPC/subnet/security group
2. Open port 5432 in the security group, scoped to the VPC CIDR only (e.g. `10.0.0.0/16`) so only instances inside the VPC can reach Postgres
3. Copy `agent.py` to the new instance, install `psycopg2-binary` the same way
4. Copy `netmon-agent-remote.service` to `/etc/systemd/system/netmon-agent.service`, updating the `NETMON_DB_HOST` value to the first instance's **private** IP
5. Enable and start it the same way as step 9 above — it will register itself in the `instances` table automatically and start reporting into the shared database

## Roadmap

- [x] Run the agent as a persistent background service (systemd)
- [x] Simulate a network failure with `iptables` and observe detection in the data
- [x] Add a second EC2 instance to monitor multiple nodes
- [ ] Add alerting (Slack/email) when latency or disk usage crosses a threshold
- [ ] Move infrastructure provisioning to Terraform

## Why I built this

I wanted hands-on experience with AWS networking and Docker beyond default/managed setups — building the VPC, security groups, and connectivity from scratch instead of relying on AWS defaults, and solving real infrastructure problems (like a corporate SSH block) along the way.
