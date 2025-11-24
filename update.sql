-- Disable foreign key checks to avoid constraints errors
SET FOREIGN_KEY_CHECKS = 0;

-- Truncate tables
TRUNCATE TABLE issue_reports;
TRUNCATE TABLE small_claims;
TRUNCATE TABLE statutes;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;