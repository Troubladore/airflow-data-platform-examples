-- Minimal Pagila-like schema for testing Bronze extraction
-- This creates a few tables with sample data to test connectivity

-- Create film table (simplified)
CREATE TABLE IF NOT EXISTS film (
    film_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    release_year INTEGER,
    length INTEGER,
    rating VARCHAR(10),
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create actor table (simplified)
CREATE TABLE IF NOT EXISTS actor (
    actor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create customer table (simplified)
CREATE TABLE IF NOT EXISTS customer (
    customer_id SERIAL PRIMARY KEY,
    store_id INTEGER,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    email VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    create_date DATE DEFAULT CURRENT_DATE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample film data
INSERT INTO film (title, description, release_year, length, rating) VALUES
('The Matrix', 'A computer hacker learns about the true nature of reality', 1999, 136, 'R'),
('Inception', 'A thief who enters dreams takes on a final job', 2010, 148, 'PG-13'),
('Interstellar', 'Explorers travel through a wormhole in search of a new home', 2014, 169, 'PG-13'),
('The Dark Knight', 'Batman faces his greatest challenge in the Joker', 2008, 152, 'PG-13'),
('Pulp Fiction', 'Interconnected stories of crime in Los Angeles', 1994, 154, 'R'),
('Fight Club', 'An insomniac office worker forms an underground fight club', 1999, 139, 'R'),
('Forrest Gump', 'The life story of a simple man with a big heart', 1994, 142, 'PG-13'),
('The Shawshank Redemption', 'Two imprisoned men bond over years', 1994, 142, 'R'),
('The Godfather', 'The aging patriarch of a crime dynasty transfers control', 1972, 175, 'R'),
('Goodfellas', 'The story of Henry Hill and his life in the mob', 1990, 146, 'R');

-- Insert sample actor data
INSERT INTO actor (first_name, last_name) VALUES
('Keanu', 'Reeves'),
('Leonardo', 'DiCaprio'),
('Matthew', 'McConaughey'),
('Christian', 'Bale'),
('John', 'Travolta'),
('Brad', 'Pitt'),
('Tom', 'Hanks'),
('Morgan', 'Freeman'),
('Al', 'Pacino'),
('Robert', 'De Niro');

-- Insert sample customer data
INSERT INTO customer (store_id, first_name, last_name, email) VALUES
(1, 'John', 'Doe', 'john.doe@example.com'),
(1, 'Jane', 'Smith', 'jane.smith@example.com'),
(2, 'Bob', 'Johnson', 'bob.johnson@example.com'),
(2, 'Alice', 'Williams', 'alice.williams@example.com'),
(1, 'Charlie', 'Brown', 'charlie.brown@example.com');

-- Create a view to verify data
CREATE VIEW bronze_test_summary AS
SELECT
    'film' as table_name, COUNT(*) as row_count FROM film
UNION ALL
SELECT
    'actor' as table_name, COUNT(*) as row_count FROM actor
UNION ALL
SELECT
    'customer' as table_name, COUNT(*) as row_count FROM customer;

-- Grant permissions (for testing)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;