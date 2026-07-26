# AWS Network Monitoring & Diagnostics Agent

A self-built monitoring system that runs Linux network diagnostics on an AWS EC2 instance and stores results in a PostgreSQL database — built from scratch to understand AWS networking, Docker, and SQL at a hands-on level, rather than relying on managed services.

## What it does

A Python agent runs on an EC2 instance and periodically executes diagnostic checks — `ping`, `df -h` (disk usage), `ss -tulwn` (open ports), and `traceroute` — parsing and storing the results in a PostgreSQL database running in Docker. This creates a queryable history of network health and system metrics over time.

## Architecture

- **AWS VPC** — custom-built network (not the default VPC) with a public subnet, Internet Gateway, and route table, configured manually to understand each networking layer
- **EC2 instance** — Ubuntu 24.04 LTS server hosting the agent and database
- **EC2 Instance Connect Endpoint** — used for secure remote access over HTTPS (port 443) rather than direct SSH (port 22), after diagnosing that outbound SSH was blocked at the network/device level in my environment
- **Docker** — containerized PostgreSQL database
- **PostgreSQL** — stores diagnostic results in a normalized schema:
  - `instances` — registered servers being monitored
  - `network_checks` — ping/traceroute results (latency, target, raw output, timestamp)
  - `system_metrics` — disk usage and open ports over time
- **Python agent** — collects diagnostics via `subprocess`, parses key metrics with regex, and writes to PostgreSQL via `psycopg2`

## Skills demonstrated

- AWS networking fundamentals: VPC, subnets, Internet Gateways, route tables, security groups
- Linux system administration and diagnostic tooling (`ping`, `df`, `ss`, `traceroute`, `ip`)
- Docker containerization
- SQL schema design with foreign key relationships
- Python scripting for automation and data collection
- Real-world troubleshooting: diagnosed and resolved an SSH connectivity block caused by corporate network security policy, using AWS's HTTPS-based EC2 Instance Connect Endpoint as a workaround

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

## Roadmap

- [ ] Run the agent as a persistent background service (systemd)
- [ ] Simulate a network failure with `iptables` and observe detection in the data
- [ ] Add a second/third EC2 instance to monitor multiple nodes
- [ ] Build a simple dashboard for visualizing latency/disk trends over time

## Why I built this

I wanted hands-on experience with AWS networking and Docker beyond default/managed setups — building the VPC, security groups, and connectivity from scratch instead of relying on AWS defaults, and solving real infrastructure problems (like a corporate SSH block) along the way.
