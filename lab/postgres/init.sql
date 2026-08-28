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

-- Read-only role used by the diagnostic agent: even if a query slips past the
-- agent's SELECT-only filter, the database itself refuses writes.
CREATE ROLE readonly LOGIN PASSWORD 'readonly_password'; -- synthetic lab credential
GRANT CONNECT ON DATABASE shop TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
