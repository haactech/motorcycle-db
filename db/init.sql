CREATE TYPE brand_type AS ENUM ('KTM', 'YAMAHA');

CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand brand_type NOT NULL,
    street VARCHAR(100) NOT NULL,
    number VARCHAR(20) NOT NULL,
    district VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE motorcycles (
    id SERIAL PRIMARY KEY,
    brand brand_type NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1900),
    branch_id INTEGER REFERENCES branches(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name_1 VARCHAR(100) NOT NULL,
    last_name_2 VARCHAR(100),
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    birth_date DATE NOT NULL,
    street VARCHAR(100) NOT NULL,
    number VARCHAR(20) NOT NULL,
    district VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE client_interests (
    client_id INTEGER REFERENCES clients(id),
    motorcycle_id INTEGER REFERENCES motorcycles(id),
    interest_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (client_id, motorcycle_id)
);

INSERT INTO branches (name, brand, street, number, district, city, state) VALUES
    ('KTM Ferbel Coapa', 'KTM', 'Canal de Miramontes', '3000', 'Coyoacán', 'Coyoacán', 'CDMX'),
    ('KTM Ferbel Satélite', 'KTM', 'Periférico Blvd. Manuel Ávila Camacho', '1920', 'Satélite', 'Naucalpan', 'Estado de México'),
    ('Yamaha Ferbel Satélite', 'YAMAHA', 'Av. Patriotismo', '98', 'Escandón', 'Miguel Hidalgo', 'CDMX');

INSERT INTO motorcycles (brand, model, year, branch_id) VALUES
    ('KTM', 'Duke 390', 2024, 1),
    ('KTM', 'Adventure 390', 2024, 2),
    ('YAMAHA', 'MT-07', 2024, 3),
    ('YAMAHA', 'R7', 2024, 3);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_branches_updated_at
    BEFORE UPDATE ON branches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_motorcycles_updated_at
    BEFORE UPDATE ON motorcycles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();