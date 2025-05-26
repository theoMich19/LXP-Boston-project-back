-- Script d'initialisation pour TalentBridge
-- Ce script crée le schéma de base de données

-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table Companies (doit être créée en premier à cause des FK)
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'hr', 'candidate')),
    company_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

-- Table Job_offers
CREATE TABLE IF NOT EXISTS job_offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    company_id UUID NOT NULL,
    created_by UUID NOT NULL,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_offers_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_offers_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_salary_range CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

-- Table Tags
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table de liaison Job_offer_tags (relation many-to-many)
CREATE TABLE IF NOT EXISTS job_offer_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_offer_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_offer_tags_job_offer FOREIGN KEY (job_offer_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_offer_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    CONSTRAINT unique_job_offer_tag UNIQUE (job_offer_id, tag_id)
);

-- Table CVs
CREATE TABLE IF NOT EXISTS cvs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    parsed_data JSONB,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cvs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_job_offers_company ON job_offers(company_id);
CREATE INDEX IF NOT EXISTS idx_job_offers_status ON job_offers(status);
CREATE INDEX IF NOT EXISTS idx_job_offers_salary_min ON job_offers(salary_min);
CREATE INDEX IF NOT EXISTS idx_job_offers_salary_max ON job_offers(salary_max);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_job_offer_tags_job_offer ON job_offer_tags(job_offer_id);
CREATE INDEX IF NOT EXISTS idx_job_offer_tags_tag ON job_offer_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_cvs_user ON cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_cvs_parsed_data ON cvs USING GIN (parsed_data);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Application des triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_offers_updated_at BEFORE UPDATE ON job_offers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Données de test (optionnel)
INSERT INTO companies (name, city, country, email, phone) VALUES
('TechCorp', 'Paris', 'France', 'contact@techcorp.fr', '+33123456789'),
('StartupInc', 'Lyon', 'France', 'hello@startupinc.fr', '+33987654321')
ON CONFLICT (email) DO NOTHING;

-- Tags de test
INSERT INTO tags (name, description) VALUES
('JavaScript', 'Développement JavaScript/TypeScript'),
('React', 'Bibliothèque React.js'),
('Python', 'Langage de programmation Python'),
('DevOps', 'Développement et opérations'),
('Remote', 'Travail à distance'),
('Senior', 'Niveau senior (5+ ans)'),
('Junior', 'Niveau junior (0-2 ans)'),
('Full-time', 'Temps plein'),
('Part-time', 'Temps partiel'),
('Startup', 'Environnement startup')
ON CONFLICT (name) DO NOTHING;