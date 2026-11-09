CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id integer PRIMARY KEY,
    data_pedido date NOT NULL,
    regiao varchar NOT NULL,
    categoria varchar NOT NULL,
    valor numeric NOT NULL CHECK (valor >= 0),
    status varchar NOT NULL CHECK (status IN ('entregue', 'cancelado', 'em_atraso'))
);

CREATE TABLE IF NOT EXISTS monitor_runs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slot date NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    status text NOT NULL CHECK (status IN ('completed', 'failed')),
    report jsonb,
    CHECK ((status = 'completed') = (report IS NOT NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS monitor_completed_per_day
    ON monitor_runs (slot) WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS pedidos_data_idx ON pedidos (data_pedido);
