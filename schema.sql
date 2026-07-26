-- Schema for the AWS Network Monitoring & Diagnostics project

CREATE TABLE instances (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    private_ip VARCHAR(15),
    public_ip VARCHAR(15),
    role VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE network_checks (
    id SERIAL PRIMARY KEY,
    instance_id INT REFERENCES instances(id),
    check_type VARCHAR(30),
    target VARCHAR(100),
    latency_ms FLOAT,
    packet_loss_pct FLOAT,
    raw_output TEXT,
    checked_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    instance_id INT REFERENCES instances(id),
    disk_usage_pct FLOAT,
    open_ports TEXT,
    listening_services TEXT,
    recorded_at TIMESTAMP DEFAULT NOW()
);
