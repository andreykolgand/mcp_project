CREATE TABLE employees (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    birth_date DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE employees ADD CONSTRAINT check_gender CHECK (gender IN ('М', 'Ж'));
ALTER TABLE employees ADD CONSTRAINT check_birth_date CHECK (birth_date <= CURRENT_DATE);
ALTER TABLE employees ADD CONSTRAINT check_hire_logic CHECK (hire_date >= birth_date);

COMMENT ON TABLE employees IS 'Справочник сотрудников организации';
