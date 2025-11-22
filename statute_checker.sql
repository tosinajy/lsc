-- Create Database
CREATE DATABASE IF NOT EXISTS statute_checker;
USE statute_checker;

-- Table: States
CREATE TABLE IF NOT EXISTS states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE
);

-- Table: Small Claims
CREATE TABLE IF NOT EXISTS small_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_id INT NOT NULL,
    small_claims_cap DECIMAL(10, 2) DEFAULT 0.00,
    small_claims_info TEXT,
    updated_by VARCHAR(50) DEFAULT 'admin',
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_id) REFERENCES states(id),
    UNIQUE KEY unique_state_claim (state_id)
);

-- NEW: Small Claims Approvals Queue
CREATE TABLE IF NOT EXISTS small_claims_approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    claim_id INT DEFAULT NULL, -- Link to existing record (NULL for new creates)
    state_id INT NOT NULL,
    small_claims_cap DECIMAL(10, 2),
    small_claims_info TEXT,
    action_type VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED'
    submitted_by VARCHAR(50),
    submitted_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES small_claims(id) ON DELETE SET NULL,
    FOREIGN KEY (state_id) REFERENCES states(id)
);

-- Table: Issue Types
CREATE TABLE IF NOT EXISTS issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    updated_by VARCHAR(50) DEFAULT 'admin',
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: Statutes
CREATE TABLE IF NOT EXISTS statutes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_id INT NOT NULL,
    issue_id INT NOT NULL,
    duration VARCHAR(10) NOT NULL DEFAULT 'years',
    time_limit_type VARCHAR(20) DEFAULT 'exact',
    time_limit_min INT NOT NULL,
    time_limit_max INT DEFAULT NULL,
    details TEXT,
    issue_info TEXT,
    conditions_exceptions TEXT,
    examples TEXT,
    code_reference VARCHAR(255),
    official_source_url TEXT,
    other_source_url TEXT,
    updated_by VARCHAR(50) DEFAULT 'admin',
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_id) REFERENCES states(id),
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    UNIQUE KEY unique_statute (state_id, issue_id)
);

-- NEW AUTHENTICATION TABLES --

-- Table: Roles
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    permissions JSON, -- Stores CRUD flags
    updated_by VARCHAR(50) DEFAULT 'system',
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT,
    updated_by VARCHAR(50) DEFAULT 'system',
    updated_dt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- SEED DATA --

-- 1. Insert States
INSERT INTO states (name, state_code, slug) VALUES
('Texas', 'TX', 'texas'),
('California', 'CA', 'california'),
('New York', 'NY', 'new-york')
ON DUPLICATE KEY UPDATE name=name;

-- 2. Insert Small Claims
INSERT INTO small_claims (state_id, small_claims_cap, small_claims_info) VALUES
(1, 20000.00, 'Justice of the Peace Court'),
(2, 10000.00, 'Small Claims Division'),
(3, 5000.00, 'City/Town Courts (varies by location, generally $5k)')
ON DUPLICATE KEY UPDATE small_claims_cap=small_claims_cap;

-- 3. Insert Issues
INSERT INTO issues (name, slug, description) VALUES
('Personal Injury', 'personal-injury', 'Injury to the body, mind, or emotions.'),
('Breach of Written Contract', 'written-contract', 'Violation of a written agreement.'),
('Medical Malpractice', 'medical-malpractice', 'Negligence by a health care provider.'),
('Debt Collection', 'debt-collection', 'Pursuit of payments of debts owed by individuals or businesses.')
ON DUPLICATE KEY UPDATE name=name;

-- 4. Insert Statutes
INSERT INTO statutes (state_id, issue_id, duration, time_limit_type, time_limit_min, time_limit_max, details, issue_info, conditions_exceptions, examples, code_reference, official_source_url, other_source_url) VALUES
(1, 1, 'years', 'exact', 2, 2, 'Two years from the day the cause of action accrues.', 'Personal injury claims involving negligence or intentional torts.', 'None explicitly stated for general injury.', 'If injury occurred on Jan 5, 2023, deadline is Jan 5, 2025.', 'Tex. Civ. Prac. & Rem. Code § 16.003', 'https://statutes.capitol.texas.gov/Docs/CP/htm/CP.16.htm', 'https://www.nolo.com/legal-encyclopedia/texas-personal-injury-laws-statute-limitations.html'),
(1, 2, 'years', 'exact', 4, 4, 'Four years after the day the cause of action accrues.', 'Failure to perform any term of a written contract without a legitimate legal excuse.', 'The clock starts when the breach occurs, not when the contract was signed.', 'Breach on July 1, 2020 -> Deadline July 1, 2024.', 'Tex. Civ. Prac. & Rem. Code § 16.004', 'https://statutes.capitol.texas.gov/Docs/CP/htm/CP.16.htm', NULL),
(1, 3, 'years', 'exact', 2, 2, 'Strict two year limit from date of breach or tort.', 'Negligence committed by a professional health care provider.', 'Statute of Repose: Not more than 10 years total regardless of discovery.', NULL, 'Tex. Civ. Prac. & Rem. Code § 74.251', 'https://statutes.capitol.texas.gov/', NULL),
(2, 1, 'years', 'exact', 2, 2, 'Two years from the date of injury.', 'Physical or emotional injury caused by another party.', 'Delayed discovery rule may apply if injury was not immediately apparent.', 'Accident: 1/1/23. File by: 1/1/25.', 'Cal. Civ. Proc. Code § 335.1', 'https://leginfo.legislature.ca.gov/', 'https://www.courts.ca.gov/9618.htm'),
(2, 2, 'years', 'exact', 4, 4, 'Four years for written contracts.', 'Disputes regarding the terms of a written agreement.', 'Oral contracts have a shorter (2 year) limit.', NULL, 'Cal. Civ. Proc. Code § 337', 'https://leginfo.legislature.ca.gov/', NULL),
(2, 3, 'years', 'range', 1, 3, 'Three years from date of injury or one year from discovery, whichever is first.', 'Malpractice by doctors or hospitals.', 'The "whichever comes first" rule makes this variable.', 'Discovered injury immediately? 3 years. Discovered it 4 years later? Too late.', 'Cal. Civ. Proc. Code § 340.5', 'https://leginfo.legislature.ca.gov/', NULL),
(3, 1, 'years', 'exact', 3, 3, 'Three years usually.', 'Harm to person or property.', 'Toxic torts may have different discovery rules.', 'Slip and fall on Dec 1, 2022 -> File by Dec 1, 2025.', 'N.Y. C.P.L.R. § 214', 'https://www.nysenate.gov/legislation/laws/CVP', NULL),
(3, 2, 'years', 'exact', 6, 6, 'Six years for contractual obligations.', 'Breach of a contract that is in writing.', 'Counterclaims may be allowed after this if related to the same transaction.', NULL, 'N.Y. C.P.L.R. § 213', 'https://www.nysenate.gov/legislation/laws/CVP', NULL)
ON DUPLICATE KEY UPDATE details=details;

-- 5. Insert Roles
-- Updated permissions to include 'approvals'
INSERT INTO roles (name, slug, permissions) VALUES
('Administrator', 'admin', '{"users": {"create": 1, "read": 1, "update": 1, "delete": 1}, "roles": {"create": 1, "read": 1, "update": 1, "delete": 1}, "issues": {"create": 1, "read": 1, "update": 1, "delete": 1}, "small_claims": {"create": 1, "read": 1, "update": 1, "delete": 1}, "statutes": {"create": 1, "read": 1, "update": 1, "delete": 1}, "approvals": {"create": 1, "read": 1, "update": 1, "delete": 1}}'),
('Editor', 'editor', '{"users": {"create": 0, "read": 1, "update": 0, "delete": 0}, "roles": {"create": 0, "read": 1, "update": 0, "delete": 0}, "issues": {"create": 1, "read": 1, "update": 1, "delete": 0}, "small_claims": {"create": 1, "read": 1, "update": 1, "delete": 0}, "statutes": {"create": 1, "read": 1, "update": 1, "delete": 0}, "approvals": {"create": 0, "read": 0, "update": 0, "delete": 0}}')
ON DUPLICATE KEY UPDATE permissions=permissions;

-- 6. Insert Users
INSERT INTO users (username, email, password_hash, role_id) VALUES
('admin', 'admin@statutechecker.com', 'scrypt:32768:8:1$9kM5f3hS$6b8c40f4b40c45858585858585858585', 1),
('editor', 'editor@statutechecker.com', 'scrypt:32768:8:1$9kM5f3hS$6b8c40f4b40c45858585858585858585', 2)
ON DUPLICATE KEY UPDATE email=email;