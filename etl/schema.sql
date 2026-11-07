CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id integer PRIMARY KEY,
    data_pedido date NOT NULL,
    regiao varchar NOT NULL,
    categoria varchar NOT NULL,
    valor numeric NOT NULL CHECK (valor >= 0),
    status varchar NOT NULL CHECK (status IN ('entregue', 'cancelado', 'em_atraso'))
);
