CREATE TABLE IF NOT EXISTS invoices (
    customer TEXT PRIMARY KEY,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    customer TEXT NOT NULL,
    kind TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO invoices (customer, status)
VALUES ('demo', 'vencida R$ 89,90')
ON CONFLICT (customer) DO NOTHING;
