-- Create Database
CREATE DATABASE IF NOT EXISTS statute_checker;
USE statute_checker;

-- Table: States
CREATE TABLE IF NOT EXISTS states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    small_claims_cap DECIMAL(10, 2) DEFAULT 0.00,
    small_claims_info TEXT
);

-- Table: Issue Types (Categories)
CREATE TABLE IF NOT EXISTS issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Table: Statutes (The junction table with specific time limits)
CREATE TABLE IF NOT EXISTS statutes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_id INT NOT NULL,
    issue_id INT NOT NULL,
    years INT NOT NULL,
    code_reference VARCHAR(255),
    details TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_id) REFERENCES states(id),
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    UNIQUE KEY unique_statute (state_id, issue_id)
);

-- SEED DATA --

-- 1. Insert States
INSERT INTO states (name, slug, small_claims_cap, small_claims_info) VALUES
('Texas', 'texas', 20000.00, 'Justice of the Peace Court'),
('California', 'california', 10000.00, 'Small Claims Division'),
('New York', 'new-york', 5000.00, 'City/Town Courts (varies by location, generally $5k)');

-- 2. Insert Issues
INSERT INTO issues (name, slug, description) VALUES
('Personal Injury', 'personal-injury', 'Injury to the body, mind, or emotions.'),
('Breach of Written Contract', 'written-contract', 'Violation of a written agreement.'),
('Medical Malpractice', 'medical-malpractice', 'Negligence by a health care provider.'),
('Debt Collection', 'debt-collection', 'Pursuit of payments of debts owed by individuals or businesses.');

-- 3. Insert Statutes (Time limits in years)
-- Texas Data
INSERT INTO statutes (state_id, issue_id, years, code_reference, details) VALUES
(1, 1, 2, 'Tex. Civ. Prac. & Rem. Code § 16.003', 'Two years from the day the cause of action accrues.'),
(1, 2, 4, 'Tex. Civ. Prac. & Rem. Code § 16.004', 'Four years after the day the cause of action accrues.'),
(1, 3, 2, 'Tex. Civ. Prac. & Rem. Code § 74.251', 'Strict two year limit from date of breach or tort.'),
(1, 4, 4, 'Tex. Civ. Prac. & Rem. Code § 16.004', 'Four years for debt actions.');

-- California Data
INSERT INTO statutes (state_id, issue_id, years, code_reference, details) VALUES
(2, 1, 2, 'Cal. Civ. Proc. Code § 335.1', 'Two years from the date of injury.'),
(2, 2, 4, 'Cal. Civ. Proc. Code § 337', 'Four years for written contracts.'),
(2, 3, 3, 'Cal. Civ. Proc. Code § 340.5', 'Three years from date of injury or one year from discovery, whichever is first.');

-- New York Data
INSERT INTO statutes (state_id, issue_id, years, code_reference, details) VALUES
(3, 1, 3, 'N.Y. C.P.L.R. § 214', 'Three years usually.'),
(3, 2, 6, 'N.Y. C.P.L.R. § 213', 'Six years for contractual obligations.');