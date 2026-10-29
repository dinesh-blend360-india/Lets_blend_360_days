CREATE TABLE sales (
    order_id VARCHAR(50),
    amount NUMERIC(12,2),
    qty INTEGER,
    order_status VARCHAR(50),
    region VARCHAR(50)
);

COPY sales(order_id, amount, qty, order_status, region)
FROM '/docker-entrypoint-initdb.d/sales.csv'
DELIMITER ','
CSV HEADER;