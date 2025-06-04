-- Script d'initialisation pour TalentBridge
-- Ce script crée le schéma de base de données

-- Table Companies (doit être créée en premier à cause des FK)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('candidate', 'hr')),
    company_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

-- Table Job_offers
CREATE TABLE IF NOT EXISTS job_offers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    company_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_offers_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_offers_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_salary_range CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

-- Table Applications (candidatures)
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    job_offer_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'rejected', 'accepted')),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_applications_job_offer FOREIGN KEY (job_offer_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_job_application UNIQUE (user_id, job_offer_id)
);

-- Table Tags
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table de liaison Job_offer_tags (relation many-to-many)
CREATE TABLE IF NOT EXISTS job_offer_tags (
    id SERIAL PRIMARY KEY,
    job_offer_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_offer_tags_job_offer FOREIGN KEY (job_offer_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_offer_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    CONSTRAINT unique_job_offer_tag UNIQUE (job_offer_id, tag_id)
);

-- Table CVs
CREATE TABLE IF NOT EXISTS cvs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size VARCHAR(50),
    file_type VARCHAR(50),
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
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_offer ON applications(job_offer_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_applied_at ON applications(applied_at);
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
('StartupInc', 'Lyon', 'France', 'hello@startupinc.fr', '+33987654321'),
('DevSolutions', 'Marseille', 'France', 'info@devsolutions.fr', '+33456789123'),
('InnovateTech', 'Toulouse', 'France', 'contact@innovatetech.fr', '+33321654987'),
('CloudFirst', 'Nantes', 'France', 'hello@cloudfirst.fr', '+33789456123')
ON CONFLICT (email) DO NOTHING;

-- Utilisateurs de test
-- Mot de passe: "password123" hashé avec bcrypt (coût 12)
INSERT INTO users (email, password_hash, first_name, last_name, role, company_id, is_active) VALUES

-- HR users
('marie.dupont@techcorp.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Marie', 'Dupont', 'hr', (SELECT id FROM companies WHERE email = 'contact@techcorp.fr'), true),
('jean.martin@startupinc.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Jean', 'Martin', 'hr', (SELECT id FROM companies WHERE email = 'hello@startupinc.fr'), true),
('sophie.bernard@devsolutions.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Sophie', 'Bernard', 'hr', (SELECT id FROM companies WHERE email = 'info@devsolutions.fr'), true),
('pierre.leroy@innovatetech.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Pierre', 'Leroy', 'hr', (SELECT id FROM companies WHERE email = 'contact@innovatetech.fr'), true),

-- Candidates
('alice.dubois@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Alice', 'Dubois', 'candidate', NULL, true),
('thomas.moreau@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Thomas', 'Moreau', 'candidate', NULL, true),
('emma.laurent@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Emma', 'Laurent', 'candidate', NULL, true),
('lucas.simon@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Lucas', 'Simon', 'candidate', NULL, true),
('chloe.petit@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Chloé', 'Petit', 'candidate', NULL, true),
('maxime.roux@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Maxime', 'Roux', 'candidate', NULL, true),
('lea.garcia@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Léa', 'Garcia', 'candidate', NULL, true)
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
('Startup', 'Environnement startup'),
('Node.js', 'Runtime JavaScript côté serveur'),
('Docker', 'Conteneurisation avec Docker'),
('AWS', 'Amazon Web Services'),
('PostgreSQL', 'Base de données PostgreSQL'),
('Git', 'Contrôle de version'),
('Angular', 'Framework Angular'),
('Vue.js', 'Framework Vue.js'),
('MongoDB', 'Base de données MongoDB'),
('Kubernetes', 'Orchestration de conteneurs'),
('Machine Learning', 'Apprentissage automatique')
ON CONFLICT (name) DO NOTHING;

-- Offres d'emploi de test
INSERT INTO job_offers (title, description, company_id, created_by, salary_min, salary_max, status) VALUES
-- Offres chez TechCorp (créées par Marie Dupont)
('Développeur Frontend React Senior',
'Nous recherchons un développeur Frontend Senior avec une solide expérience en React.js pour rejoindre notre équipe de développement.

Responsabilités:
- Développer des interfaces utilisateur modernes et réactives
- Collaborer avec l''équipe UX/UI pour implémenter les designs
- Optimiser les performances des applications
- Mentorer les développeurs junior

Compétences requises:
- 5+ années d''expérience en développement Frontend
- Expertise en React.js, TypeScript, Redux
- Connaissance des outils modernes (Webpack, Babel, etc.)
- Expérience avec les tests unitaires (Jest, RTL)

Avantages:
- Télétravail possible 3 jours/semaine
- Formation continue
- Mutuelle premium
- Tickets restaurant',
(SELECT id FROM companies WHERE email = 'contact@techcorp.fr'),
(SELECT id FROM users WHERE email = 'marie.dupont@techcorp.fr'),
55000.00, 70000.00, 'active'),

('DevOps Engineer',
'Rejoignez notre équipe infrastructure en tant qu''Ingénieur DevOps pour automatiser et optimiser nos processus de déploiement.

Missions:
- Gérer l''infrastructure cloud (AWS/Azure)
- Mettre en place et maintenir les pipelines CI/CD
- Monitoring et observabilité des applications
- Automatisation des déploiements

Profil recherché:
- 3+ ans d''expérience en DevOps/Infrastructure
- Maîtrise de Docker, Kubernetes
- Connaissance des outils CI/CD (Jenkins, GitLab CI)
- Scripting (Python, Bash)
- Expérience cloud (AWS, Azure)

Environnement technique:
- AWS/Azure, Terraform
- Kubernetes, Docker
- Prometheus, Grafana
- GitLab, Jenkins',
(SELECT id FROM companies WHERE email = 'contact@techcorp.fr'),
(SELECT id FROM users WHERE email = 'marie.dupont@techcorp.fr'),
50000.00, 65000.00, 'active'),

-- Offres chez StartupInc (créées par Jean Martin)
('Full-Stack Developer JavaScript',
'Startup en forte croissance recherche un développeur Full-Stack passionné pour développer notre plateforme SaaS.

Ce que tu feras:
- Développement frontend avec React/Next.js
- Développement backend avec Node.js/Express
- Architecture et design de nouvelles fonctionnalités
- Participation aux décisions techniques

Stack technique:
- Frontend: React, Next.js, TypeScript
- Backend: Node.js, Express, PostgreSQL
- Infrastructure: Docker, AWS
- Outils: Git, Jira, Slack

Profil:
- 2-4 ans d''expérience en développement web
- Passion pour les nouvelles technologies
- Esprit startup et autonomie
- Bon niveau d''anglais',
 (SELECT id FROM companies WHERE email = 'hello@startupinc.fr'),
 (SELECT id FROM users WHERE email = 'jean.martin@startupinc.fr'),
 42000.00, 55000.00, 'active'),

('Lead Developer Python',
 'Nous cherchons un Lead Developer Python pour diriger notre équipe technique et faire évoluer notre architecture.

 Responsabilités:
 - Management technique d''une équipe de 5 développeurs
 - Architecture et évolution de notre plateforme Python/Django
 - Code review et bonnes pratiques
 - Recrutement et formation

 Compétences techniques:
 - 6+ ans d''expérience Python/Django
 - Expérience en management d''équipe
 - Architecture microservices
 - Bases de données (PostgreSQL, Redis)
 - Méthodes Agiles

 Startup benefits:
 - Equity package
 - Budget formation 2k€/an
 - MacBook Pro + setup home office
 - Team building réguliers
 - Horaires flexibles',
 (SELECT id FROM companies WHERE email = 'hello@startupinc.fr'),
 (SELECT id FROM users WHERE email = 'jean.martin@startupinc.fr'),
 60000.00, 75000.00, 'active'),

-- Offres chez DevSolutions (créées par Sophie Bernard)
('Développeur Backend Java Spring Boot',
 'Entreprise de conseil recherche un développeur Backend Java pour des missions client variées.

 Missions:
 - Développement d''applications Java/Spring Boot
 - Intégration avec des APIs externes
 - Optimisation des performances
 - Documentation technique

 Technologies:
 - Java 11+, Spring Boot, Spring Security
 - Bases de données relationnelles
 - Maven/Gradle, Git
 - Tests unitaires et d''intégration

 Profil:
 - 3-5 ans d''expérience Java/Spring
 - Rigoureux et méthodique
 - Capacité d''adaptation (missions client)
 - Certifications Java appréciées',
 (SELECT id FROM companies WHERE email = 'info@devsolutions.fr'),
 (SELECT id FROM users WHERE email = 'sophie.bernard@devsolutions.fr'),
 45000.00, 58000.00, 'active'),

-- Offres chez InnovateTech (créées par Pierre Leroy)
('Data Scientist Machine Learning',
 'Scale-up tech recherche un Data Scientist pour développer nos algorithmes de machine learning.

 Missions:
 - Développement de modèles ML/IA
 - Analyse de données massives
 - Déploiement de modèles en production
 - Collaboration avec les équipes produit

 Compétences:
 - Python (Pandas, Scikit-learn, TensorFlow)
 - Statistiques et mathématiques
 - SQL, bases de données
 - MLOps (Docker, Kubernetes)
 - Cloud (AWS/GCP)

 Formation:
 - Master/Doctorat en Data Science, Mathématiques ou équivalent
 - 2+ ans d''expérience en ML
 - Publications ou projets personnels appréciés

 Environnement:
 - Équipe R&D de 10 personnes
 - Infrastructure cloud dédiée
 - Participation à des conférences
 - Open source encouragé',
 (SELECT id FROM companies WHERE email = 'contact@innovatetech.fr'),
 (SELECT id FROM users WHERE email = 'pierre.leroy@innovatetech.fr'),
 55000.00, 70000.00, 'active'),

('Mobile Developer React Native',
 'Développeur Mobile React Native pour créer les apps de demain.

 Projets:
 - Développement d''applications mobiles iOS/Android
 - Intégration avec des APIs REST/GraphQL
 - Optimisation des performances
 - Publication sur les stores

 Stack:
 - React Native, TypeScript
 - Redux/Context API
 - Firebase, AWS Amplify
 - CodePush, Flipper
 - Jest, Detox

 Expérience:
 - 2+ ans en développement mobile
 - Apps publiées sur les stores
 - Connaissance native (Swift/Kotlin) appréciée
 - UX/UI sense

 Avantages:
 - Projets innovants
 - iPhone/Android fournis
 - Télétravail 100% possible
 - Budget conférences/formations',
 (SELECT id FROM companies WHERE email = 'contact@innovatetech.fr'),
 (SELECT id FROM users WHERE email = 'pierre.leroy@innovatetech.fr'),
 45000.00, 60000.00, 'active'),

-- Offre en remote chez CloudFirst
('Senior Software Engineer (Remote)',
 'Poste 100% remote pour développeur expérimenté dans une entreprise internationale.

 What you''ll do:
 - Design and implement scalable software solutions
 - Collaborate with distributed teams across time zones
 - Mentor junior developers
 - Contribute to technical architecture decisions

 Requirements:
 - 5+ years of software development experience
 - Proficiency in multiple programming languages
 - Experience with cloud platforms (AWS, GCP, Azure)
 - Strong communication skills in English
 - Remote work experience preferred

 Tech Stack:
 - Languages: Python, Go, JavaScript/TypeScript
 - Databases: PostgreSQL, MongoDB, Redis
 - Cloud: AWS, Kubernetes, Docker
 - Tools: Git, Jira, Slack, Zoom

 Benefits:
 - 100% remote work
 - Competitive salary + equity
 - Health insurance
 - Home office budget
 - Flexible working hours
 - Annual company retreat',
 (SELECT id FROM companies WHERE email = 'hello@cloudfirst.fr'),
 (SELECT id FROM users WHERE email = 'marie.dupont@techcorp.fr'),
 65000.00, 85000.00, 'active');

-- CVs de test
INSERT INTO cvs (user_id, file_path, original_filename, file_size, file_type, parsed_data, upload_date)
VALUES
-- CV pour Alice Dubois (user_id = 6)
(6, 'uploads/cvs/alice_cv_frontend.pdf', 'CV_Alice_Frontend_Developer.pdf', '2567890', 'pdf',
 '{"raw_text": "Alice Dubois\\nDéveloppeur Frontend\\nParis, France\\nalice.dubois@gmail.com\\n+33 6 12 34 56 78\\n\\nEXPÉRIENCE PROFESSIONNELLE\\n\\nDéveloppeur Frontend Senior - WebAgency (2021-2024)\\n• Développement d''interfaces utilisateur avec React.js et Vue.js\\n• Collaboration avec l''équipe UX/UI pour l''implémentation des designs\\n• Optimisation des performances web (Core Web Vitals)\\n• Encadrement de 2 développeurs junior\\n• Migration de jQuery vers React pour 5 projets clients\\n\\nDéveloppeur Frontend - DigitalStudio (2019-2021)\\n• Création de sites web responsive avec HTML5, CSS3, JavaScript\\n• Intégration de maquettes Figma/Adobe XD\\n• Développement de composants réutilisables\\n• Tests automatisés avec Jest et Cypress\\n\\nCOMPÉTENCES TECHNIQUES\\n• Frontend: React.js, Vue.js, Angular, TypeScript\\n• Styling: CSS3, SASS, Styled Components, Tailwind CSS\\n• JavaScript: ES6+, jQuery, Webpack, Vite\\n• Outils: Git, NPM, Yarn, VS Code\\n• Tests: Jest, React Testing Library, Cypress\\n• Design: Figma, Adobe Creative Suite\\n\\nFORMATION\\n• Master Informatique - Université Paris Diderot (2019)\\n• Certification React Developer - Meta (2022)\\n• Formation TypeScript - École 42 (2023)\\n\\nLANGUES\\n• Français (natif)\\n• Anglais (courant - C1)\\n• Espagnol (intermédiaire - B2)", "extracted_at": "2025-05-26T10:30:00", "text_length": 1247, "skills": ["React", "Vue.js", "JavaScript", "TypeScript", "CSS3", "HTML5"], "email": "alice.dubois@gmail.com", "experience_years": 5}',
 '2025-05-25 14:30:00'),

-- CV pour Thomas Moreau (user_id = 7)
(7, 'uploads/cvs/thomas_cv_backend.pdf', 'CV_Thomas_Backend_Java.pdf', '3245678', 'pdf',
 '{"raw_text": "Thomas Moreau\\nDéveloppeur Backend Java\\nLyon, France\\nthomas.moreau@gmail.com\\n+33 6 98 76 54 32\\n\\nEXPÉRIENCE PROFESSIONNELLE\\n\\nLead Developer Java - TechCorp (2022-2024)\\n• Management d''une équipe de 4 développeurs\\n• Architecture microservices avec Spring Boot\\n• Migration d''applications legacy vers Spring Boot\\n• Mise en place CI/CD avec Jenkins et Docker\\n• Code review et mentoring technique\\n\\nDéveloppeur Backend Senior - StartupTech (2019-2022)\\n• Développement d''APIs REST avec Spring Boot\\n• Intégration avec bases de données PostgreSQL et MongoDB\\n• Optimisation des performances et requêtes SQL\\n• Tests unitaires et d''intégration\\n• Documentation technique avec Swagger\\n\\nDéveloppeur Java Junior - SoftwareCompany (2017-2019)\\n• Développement d''applications web avec Spring MVC\\n• Maintenance et évolution d''applications existantes\\n• Participation aux daily meetings et sprints Agile\\n\\nCOMPÉTENCES TECHNIQUES\\n• Langages: Java 11+, Python, SQL\\n• Frameworks: Spring Boot, Spring Security, Spring Data\\n• Bases de données: PostgreSQL, MongoDB, Redis\\n• Infrastructure: Docker, Kubernetes, AWS\\n• Outils: Maven, Gradle, Git, IntelliJ IDEA\\n• Tests: JUnit, Mockito, TestContainers\\n• Méthodologies: Agile, Scrum, DevOps\\n\\nCERTIFICATIONS\\n• Oracle Certified Professional Java SE 11 (2021)\\n• AWS Solutions Architect Associate (2023)\\n• Spring Professional Certification (2022)\\n\\nFORMATION\\n• Ingénieur Informatique - EPITECH Lyon (2017)\\n• Master en Génie Logiciel - Université Lyon 1 (2019)\\n\\nLANGUES\\n• Français (natif)\\n• Anglais (professionnel - C1)\\n• Allemand (scolaire - A2)", "extracted_at": "2025-05-26T11:15:00", "text_length": 1456, "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "AWS"], "email": "thomas.moreau@gmail.com", "experience_years": 7}',
 '2025-05-24 09:45:00'),

-- CV pour Emma Laurent (user_id = 8)
(8, 'uploads/cvs/emma_cv_fullstack.docx', 'CV_Emma_Fullstack_Python.docx', '1987654', 'docx',
 '{"raw_text": "Emma Laurent\\nDéveloppeur Full-Stack Python\\nMarseille, France\\nemma.laurent@gmail.com\\n+33 7 11 22 33 44\\n\\nEXPÉRIENCE PROFESSIONNELLE\\n\\nFull-Stack Developer - StartupInc (2021-2024)\\n• Développement d''une plateforme SaaS avec Django et React\\n• Conception et implémentation d''APIs REST\\n• Gestion de bases de données PostgreSQL\\n• Déploiement sur AWS avec Docker\\n• Collaboration étroite avec l''équipe produit\\n\\nDéveloppeur Python - WebFactory (2019-2021)\\n• Développement de sites web avec Django\\n• Intégration de systèmes de paiement (Stripe, PayPal)\\n• Optimisation SEO et performances\\n• Formation et support aux clients\\n\\nDéveloppeur Junior - TechSolutions (2018-2019)\\n• Développement d''applications Python\\n• Scripts d''automatisation et traitement de données\\n• Support technique et debugging\\n\\nCOMPÉTENCES TECHNIQUES\\n• Backend: Python, Django, FastAPI, Flask\\n• Frontend: React.js, TypeScript, HTML5, CSS3\\n• Bases de données: PostgreSQL, MongoDB, Redis\\n• DevOps: Docker, AWS, CI/CD\\n• Outils: Git, VS Code, PyCharm, Postman\\n• Tests: Pytest, Jest, Selenium\\n\\nPROJETS PERSONNELS\\n• API de recommandation musicale avec FastAPI\\n• Application mobile React Native pour le sport\\n• Bot Discord en Python avec gestion BDD\\n• Contributions open source (Django, FastAPI)\\n\\nSOFT SKILLS\\n• Travail en équipe et communication\\n• Méthodologie Agile et Scrum\\n• Mentoring de développeurs junior\\n• Veille technologique active\\n\\nFORMATION\\n• École 42 - Cursus complet (2018)\\n• Autoformation continue (Coursera, Udemy)\\n• Participation à des hackathons\\n\\nLANGUES\\n• Français (natif)\\n• Anglais (professionnel - B2)\\n• Italien (conversationnel - B1)", "extracted_at": "2025-05-26T12:00:00", "text_length": 1523, "skills": ["Python", "Django", "React", "PostgreSQL", "AWS"], "email": "emma.laurent@gmail.com", "experience_years": 6}',
 '2025-05-23 16:20:00');