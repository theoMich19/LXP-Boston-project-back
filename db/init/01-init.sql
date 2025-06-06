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

-- Test data (optional)
INSERT INTO companies (name, city, country, email, phone) VALUES
('TechCorp', 'San Francisco', 'USA', 'contact@techcorp.com', '+14155551234'),
('StartupInc', 'Austin', 'USA', 'hello@startupinc.com', '+15125554567'),
('DevSolutions', 'Seattle', 'USA', 'info@devsolutions.com', '+12065557890'),
('InnovateTech', 'Boston', 'USA', 'contact@innovatetech.com', '+16175551234'),
('CloudFirst', 'Denver', 'USA', 'hello@cloudfirst.com', '+13035554567')
ON CONFLICT (email) DO NOTHING;

-- Test users
-- Password: "password123" hashed with bcrypt (cost 12)
INSERT INTO users (email, password_hash, first_name, last_name, role, company_id, is_active) VALUES

-- HR users
('mary.smith@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Mary', 'Smith', 'hr', (SELECT id FROM companies WHERE email = 'contact@techcorp.com'), true),
('john.johnson@startupinc.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'John', 'Johnson', 'hr', (SELECT id FROM companies WHERE email = 'hello@startupinc.com'), true),
('sarah.williams@devsolutions.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Sarah', 'Williams', 'hr', (SELECT id FROM companies WHERE email = 'info@devsolutions.com'), true),
('peter.brown@innovatetech.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Peter', 'Brown', 'hr', (SELECT id FROM companies WHERE email = 'contact@innovatetech.com'), true),

-- Candidates
('alice.davis@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Alice', 'Davis', 'candidate', NULL, true),
('thomas.wilson@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Thomas', 'Wilson', 'candidate', NULL, true),
('emma.miller@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Emma', 'Miller', 'candidate', NULL, true),
('lucas.taylor@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Lucas', 'Taylor', 'candidate', NULL, true),
('chloe.anderson@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Chloe', 'Anderson', 'candidate', NULL, true),
('max.garcia@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Max', 'Garcia', 'candidate', NULL, true),
('lea.martinez@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8kW.8o3vE6', 'Lea', 'Martinez', 'candidate', NULL, true)
ON CONFLICT (email) DO NOTHING;

-- Test job offers
INSERT INTO job_offers (title, description, company_id, created_by, salary_min, salary_max, status) VALUES
-- Jobs at TechCorp (created by Mary Smith)
('Senior Frontend React Developer',
'We are looking for a Senior Frontend Developer with solid React.js experience to join our development team.

Responsibilities:
- Develop modern and responsive user interfaces
- Collaborate with UX/UI team to implement designs
- Optimize application performance
- Mentor junior developers

Required skills:
- 5+ years of Frontend development experience
- Expertise in React.js, TypeScript, Redux
- Knowledge of modern tools (Webpack, Babel, etc.)
- Experience with unit testing (Jest, RTL)

Benefits:
- Remote work possible 3 days/week
- Continuous training
- Premium health insurance
- Meal vouchers',
(SELECT id FROM companies WHERE email = 'contact@techcorp.com'),
(SELECT id FROM users WHERE email = 'mary.smith@techcorp.com'),
55000.00, 70000.00, 'active'),

('DevOps Engineer',
'Join our infrastructure team as a DevOps Engineer to automate and optimize our deployment processes.

Missions:
- Manage cloud infrastructure (AWS/Azure)
- Set up and maintain CI/CD pipelines
- Application monitoring and observability
- Deployment automation

Required profile:
- 3+ years of DevOps/Infrastructure experience
- Proficiency in Docker, Kubernetes
- Knowledge of CI/CD tools (Jenkins, GitLab CI)
- Scripting (Python, Bash)
- Cloud experience (AWS, Azure)

Technical environment:
- AWS/Azure, Terraform
- Kubernetes, Docker
- Prometheus, Grafana
- GitLab, Jenkins',
(SELECT id FROM companies WHERE email = 'contact@techcorp.com'),
(SELECT id FROM users WHERE email = 'mary.smith@techcorp.com'),
50000.00, 65000.00, 'active'),

-- Jobs at StartupInc (created by John Johnson)
('Full-Stack JavaScript Developer',
'Fast-growing startup seeks a passionate Full-Stack developer to develop our SaaS platform.

What you''ll do:
- Frontend development with React/Next.js
- Backend development with Node.js/Express
- Architecture and design of new features
- Participate in technical decisions

Tech stack:
- Frontend: React, Next.js, TypeScript
- Backend: Node.js, Express, PostgreSQL
- Infrastructure: Docker, AWS
- Tools: Git, Jira, Slack

Profile:
- 2-4 years of web development experience
- Passion for new technologies
- Startup mindset and autonomy
- Good English level',
 (SELECT id FROM companies WHERE email = 'hello@startupinc.com'),
 (SELECT id FROM users WHERE email = 'john.johnson@startupinc.com'),
 42000.00, 55000.00, 'active'),

('Lead Python Developer',
 'We''re looking for a Lead Python Developer to lead our technical team and evolve our architecture.

 Responsibilities:
 - Technical management of a team of 5 developers
 - Architecture and evolution of our Python/Django platform
 - Code review and best practices
 - Recruitment and training

 Technical skills:
 - 6+ years of Python/Django experience
 - Team management experience
 - Microservices architecture
 - Databases (PostgreSQL, Redis)
 - Agile methodologies

 Startup benefits:
 - Equity package
 - $2k/year training budget
 - MacBook Pro + home office setup
 - Regular team building
 - Flexible hours',
 (SELECT id FROM companies WHERE email = 'hello@startupinc.com'),
 (SELECT id FROM users WHERE email = 'john.johnson@startupinc.com'),
 60000.00, 75000.00, 'active'),

-- Jobs at DevSolutions (created by Sarah Williams)
('Java Spring Boot Backend Developer',
 'Consulting company seeks a Backend Java developer for various client missions.

 Missions:
 - Develop Java/Spring Boot applications
 - Integration with external APIs
 - Performance optimization
 - Technical documentation

 Technologies:
 - Java 11+, Spring Boot, Spring Security
 - Relational databases
 - Maven/Gradle, Git
 - Unit and integration testing

 Profile:
 - 3-5 years of Java/Spring experience
 - Rigorous and methodical
 - Adaptability (client missions)
 - Java certifications appreciated',
 (SELECT id FROM companies WHERE email = 'info@devsolutions.com'),
 (SELECT id FROM users WHERE email = 'sarah.williams@devsolutions.com'),
 45000.00, 58000.00, 'active'),

-- Jobs at InnovateTech (created by Peter Brown)
('Machine Learning Data Scientist',
 'Tech scale-up seeks a Data Scientist to develop our machine learning algorithms.

 Missions:
 - Develop ML/AI models
 - Analyze massive datasets
 - Deploy models to production
 - Collaborate with product teams

 Skills:
 - Python (Pandas, Scikit-learn, TensorFlow)
 - Statistics and mathematics
 - SQL, databases
 - MLOps (Docker, Kubernetes)
 - Cloud (AWS/GCP)

 Education:
 - Master/PhD in Data Science, Mathematics or equivalent
 - 2+ years of ML experience
 - Publications or personal projects appreciated

 Environment:
 - R&D team of 10 people
 - Dedicated cloud infrastructure
 - Conference participation
 - Open source encouraged',
 (SELECT id FROM companies WHERE email = 'contact@innovatetech.com'),
 (SELECT id FROM users WHERE email = 'peter.brown@innovatetech.com'),
 55000.00, 70000.00, 'active'),

('React Native Mobile Developer',
 'Mobile Developer React Native to create tomorrow''s apps.

 Projects:
 - Develop iOS/Android mobile applications
 - Integration with REST/GraphQL APIs
 - Performance optimization
 - Store publication

 Stack:
 - React Native, TypeScript
 - Redux/Context API
 - Firebase, AWS Amplify
 - CodePush, Flipper
 - Jest, Detox

 Experience:
 - 2+ years in mobile development
 - Apps published on stores
 - Native knowledge (Swift/Kotlin) appreciated
 - UX/UI sense

 Benefits:
 - Innovative projects
 - iPhone/Android provided
 - 100% remote work possible
 - Conference/training budget',
 (SELECT id FROM companies WHERE email = 'contact@innovatetech.com'),
 (SELECT id FROM users WHERE email = 'peter.brown@innovatetech.com'),
 45000.00, 60000.00, 'active'),

-- Remote job at CloudFirst
('Senior Software Engineer (Remote)',
 '100% remote position for experienced developer in an international company.

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
 (SELECT id FROM companies WHERE email = 'hello@cloudfirst.com'),
 (SELECT id FROM users WHERE email = 'mary.smith@techcorp.com'),
 65000.00, 85000.00, 'active');

-- Test CVs
INSERT INTO cvs (user_id, file_path, original_filename, file_size, file_type, parsed_data, upload_date)
VALUES
-- CV for Alice Davis (user_id = 6)
(6, 'uploads/cvs/alice_cv_frontend.pdf', 'CV_Alice_Frontend_Developer.pdf', '2567890', 'pdf',
 '{"raw_text": "Alice Davis\\nFrontend Developer\\nSan Francisco, CA\\nalice.davis@gmail.com\\n+1 415-555-1234\\n\\nPROFESSIONAL EXPERIENCE\\n\\nSenior Frontend Developer - WebAgency (2021-2024)\\n• Developed user interfaces with React.js and Vue.js\\n• Collaborated with UX/UI team for design implementation\\n• Optimized web performance (Core Web Vitals)\\n• Mentored 2 junior developers\\n• Migrated 5 client projects from jQuery to React\\n\\nFrontend Developer - DigitalStudio (2019-2021)\\n• Created responsive websites with HTML5, CSS3, JavaScript\\n• Integrated Figma/Adobe XD mockups\\n• Developed reusable components\\n• Automated testing with Jest and Cypress\\n\\nTECHNICAL SKILLS\\n• Frontend: React.js, Vue.js, Angular, TypeScript\\n• Styling: CSS3, SASS, Styled Components, Tailwind CSS\\n• JavaScript: ES6+, jQuery, Webpack, Vite\\n• Tools: Git, NPM, Yarn, VS Code\\n• Testing: Jest, React Testing Library, Cypress\\n• Design: Figma, Adobe Creative Suite\\n\\nEDUCATION\\n• Master in Computer Science - Stanford University (2019)\\n• React Developer Certification - Meta (2022)\\n• TypeScript Training - Google (2023)\\n\\nLANGUAGES\\n• English (native)\\n• Spanish (fluent - C1)\\n• French (intermediate - B2)", "extracted_at": "2025-05-26T10:30:00", "text_length": 1247, "skills": ["React", "Vue.js", "JavaScript", "TypeScript", "CSS3", "HTML5"], "email": "alice.davis@gmail.com", "experience_years": 5}',
 '2025-05-25 14:30:00'),

-- CV for Thomas Wilson (user_id = 7)
(7, 'uploads/cvs/thomas_cv_backend.pdf', 'CV_Thomas_Backend_Java.pdf', '3245678', 'pdf',
 '{"raw_text": "Thomas Wilson\\nBackend Java Developer\\nAustin, TX\\nthomas.wilson@gmail.com\\n+1 512-555-4567\\n\\nPROFESSIONAL EXPERIENCE\\n\\nLead Java Developer - TechCorp (2022-2024)\\n• Managed a team of 4 developers\\n• Microservices architecture with Spring Boot\\n• Migrated legacy applications to Spring Boot\\n• Set up CI/CD with Jenkins and Docker\\n• Code review and technical mentoring\\n\\nSenior Backend Developer - StartupTech (2019-2022)\\n• Developed REST APIs with Spring Boot\\n• Integrated with PostgreSQL and MongoDB databases\\n• Optimized performance and SQL queries\\n• Unit and integration testing\\n• Technical documentation with Swagger\\n\\nJunior Java Developer - SoftwareCompany (2017-2019)\\n• Developed web applications with Spring MVC\\n• Maintained and evolved existing applications\\n• Participated in daily meetings and Agile sprints\\n\\nTECHNICAL SKILLS\\n• Languages: Java 11+, Python, SQL\\n• Frameworks: Spring Boot, Spring Security, Spring Data\\n• Databases: PostgreSQL, MongoDB, Redis\\n• Infrastructure: Docker, Kubernetes, AWS\\n• Tools: Maven, Gradle, Git, IntelliJ IDEA\\n• Testing: JUnit, Mockito, TestContainers\\n• Methodologies: Agile, Scrum, DevOps\\n\\nCERTIFICATIONS\\n• Oracle Certified Professional Java SE 11 (2021)\\n• AWS Solutions Architect Associate (2023)\\n• Spring Professional Certification (2022)\\n\\nEDUCATION\\n• Computer Science Engineer - UT Austin (2017)\\n• Master in Software Engineering - UT Austin (2019)\\n\\nLANGUAGES\\n• English (native)\\n• Spanish (professional - C1)\\n• German (basic - A2)", "extracted_at": "2025-05-26T11:15:00", "text_length": 1456, "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "AWS"], "email": "thomas.wilson@gmail.com", "experience_years": 7}',
 '2025-05-24 09:45:00'),

-- CV for Emma Miller (user_id = 8)
(8, 'uploads/cvs/emma_cv_fullstack.docx', 'CV_Emma_Fullstack_Python.docx', '1987654', 'docx',
 '{"raw_text": "Emma Miller\\nFull-Stack Python Developer\\nSeattle, WA\\nemma.miller@gmail.com\\n+1 206-555-7890\\n\\nPROFESSIONAL EXPERIENCE\\n\\nFull-Stack Developer - StartupInc (2021-2024)\\n• Developed a SaaS platform with Django and React\\n• Designed and implemented REST APIs\\n• Managed PostgreSQL databases\\n• Deployed to AWS with Docker\\n• Close collaboration with product team\\n\\nPython Developer - WebFactory (2019-2021)\\n• Developed websites with Django\\n• Integrated payment systems (Stripe, PayPal)\\n• SEO and performance optimization\\n• Client training and support\\n\\nJunior Developer - TechSolutions (2018-2019)\\n• Developed Python applications\\n• Automation scripts and data processing\\n• Technical support and debugging\\n\\nTECHNICAL SKILLS\\n• Backend: Python, Django, FastAPI, Flask\\n• Frontend: React.js, TypeScript, HTML5, CSS3\\n• Databases: PostgreSQL, MongoDB, Redis\\n• DevOps: Docker, AWS, CI/CD\\n• Tools: Git, VS Code, PyCharm, Postman\\n• Testing: Pytest, Jest, Selenium\\n\\nPERSONAL PROJECTS\\n• Music recommendation API with FastAPI\\n• React Native sports mobile app\\n• Discord bot in Python with database management\\n• Open source contributions (Django, FastAPI)\\n\\nSOFT SKILLS\\n• Teamwork and communication\\n• Agile and Scrum methodology\\n• Junior developer mentoring\\n• Active tech watch\\n\\nEDUCATION\\n• Computer Science Bootcamp - Lambda School (2018)\\n• Continuous self-learning (Coursera, Udemy)\\n• Hackathon participation\\n\\nLANGUAGES\\n• English (native)\\n• Spanish (professional - B2)\\n• Italian (conversational - B1)", "extracted_at": "2025-05-26T12:00:00", "text_length": 1523, "skills": ["Python", "Django", "React", "PostgreSQL", "AWS"], "email": "emma.miller@gmail.com", "experience_years": 6}',
 '2025-05-23 16:20:00');