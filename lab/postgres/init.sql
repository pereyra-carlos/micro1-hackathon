CREATE TABLE orders (
    id serial PRIMARY KEY,
    item text NOT NULL,
    status text NOT NULL DEFAULT 'paid'
);

CREATE TABLE reports (
    id serial PRIMARY KEY,
    job_id text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO orders (item, status) VALUES
    ('keyboard', 'paid'),
    ('mouse', 'paid'),
    ('monitor', 'shipped'),
    ('laptop', 'paid'),
    ('webcam', 'refunded'),
    ('headset', 'paid'),
    ('dock', 'shipped'),
    ('cable', 'paid'),
    ('desk', 'paid'),
    ('chair', 'shipped'),
    ('lamp', 'paid'),
    ('stand', 'paid');

-- Application role: the api and worker connect as a regular (non-superuser)
-- user, as a production service would, so connection-slot exhaustion can
-- actually lock them out.
CREATE ROLE svc LOGIN PASSWORD 'svc_password'; -- synthetic lab credential
GRANT CONNECT ON DATABASE shop TO svc;
GRANT USAGE ON SCHEMA public TO svc;
GRANT SELECT ON orders TO svc;
GRANT SELECT, INSERT ON reports TO svc;
GRANT USAGE ON SEQUENCE reports_id_seq TO svc;

-- Batch role: an unprivileged client used by fault injection to leak
-- long-running sessions.
CREATE ROLE batch LOGIN PASSWORD 'batch_password'; -- synthetic lab credential
GRANT CONNECT ON DATABASE shop TO batch;

-- Read-only role used by the diagnostic agent: even if a query slips past the
-- agent's SELECT-only filter, the database itself refuses writes. It may use
-- reserved connection slots so diagnosis stays possible when regular slots
-- are exhausted -- mirroring real ops break-glass access.
CREATE ROLE readonly LOGIN PASSWORD 'readonly_password'; -- synthetic lab credential
GRANT CONNECT ON DATABASE shop TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
GRANT pg_use_reserved_connections TO readonly;
GRANT pg_monitor TO readonly; -- full pg_stat_activity visibility, as a real observability account would have
