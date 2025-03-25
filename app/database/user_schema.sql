-- Schema pour la table users

CREATE TABLE users (
    email VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    uid VARCHAR(255) UNIQUE
);

-- Création d'index pour les colonnes fréquemment utilisées
CREATE INDEX idx_role ON users (role);
CREATE INDEX idx_status ON users (status);