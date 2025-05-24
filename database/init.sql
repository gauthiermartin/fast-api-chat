CREATE TABLE IF NOT EXISTS insurance_claims (
    generated_id SERIAL PRIMARY KEY,
    policy_id VARCHAR(255),
    claim_id VARCHAR(255),
    customer_age INTEGER,
    customer_gender VARCHAR(255),
    customer_state VARCHAR(255),
    vehicle_make VARCHAR(255),
    vehicle_model VARCHAR(255),
    vehicle_year INTEGER,
    claim_date TIMESTAMP,
    claim_type VARCHAR(255),
    claim_amount FLOAT,
    deductible SMALLINT,
    claim_status VARCHAR(255),
    annual_premium FLOAT,
    is_fraud BOOLEAN
);
