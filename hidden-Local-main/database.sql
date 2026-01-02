CREATE DATABASE hidden_local;
USE hidden_local;
CREATE TABLE hidden_places (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100),
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
SHOW TABLES;
INSERT INTO hidden_places (name, city, category, description)
VALUES
('Aloo Paratha Aunty', 'Manali', 'Food', 'A small local stall known only to locals, serving fresh aloo parathas.'),
('Secret Waterfall', 'Kasol', 'Place', 'A hidden waterfall reachable only by a narrow forest path.'),
('Local Wool Market', 'Shimla', 'Market', 'Underrated market selling authentic local wool products.');
SELECT * FROM hidden_places;




