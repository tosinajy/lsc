CREATE DATABASE  IF NOT EXISTS `statute_checker` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `statute_checker`;
-- MySQL dump 10.13  Distrib 8.0.34, for Win64 (x86_64)
--
-- Host: localhost    Database: statute_checker
-- ------------------------------------------------------
-- Server version	8.0.34

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `issue_reports`
--

DROP TABLE IF EXISTS `issue_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issue_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `page_context` varchar(255) DEFAULT NULL,
  `details` text NOT NULL,
  `reporter_email` varchar(100) DEFAULT NULL,
  `official_source` varchar(255) DEFAULT NULL,
  `is_valid` tinyint(1) DEFAULT NULL COMMENT 'NULL=Pending, 1=Valid, 0=Invalid',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issue_reports`
--

INSERT INTO `issue_reports` VALUES (1,'/limitations/california/personal-injury','test','aj@bbc.com','https://abc.com',1,'2025-11-22 21:02:48');

--
-- Table structure for table `issues`
--

DROP TABLE IF EXISTS `issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issues` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `description` text,
  `issue_group` varchar(100) DEFAULT NULL,
  `updated_by` varchar(50) DEFAULT 'admin',
  `updated_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issues`
--

INSERT INTO `issues` VALUES (1,'Personal Injury','personal-injury','Injury to the body, mind, or emotions.',NULL,'admin','2025-11-22 19:23:07'),(2,'Breach of Written Contract','written-contract','Violation of a written agreement.',NULL,'admin','2025-11-22 19:23:07'),(3,'Medical Malpractice','medical-malpractice','Negligence by a health care provider.',NULL,'admin','2025-11-22 19:23:07'),(4,'Debt Collection','debt-collection','Pursuit of payments of debts owed by individuals or businesses.',NULL,'admin','2025-11-22 19:23:07');

--
-- Table structure for table `login_logs`
--

DROP TABLE IF EXISTS `login_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `login_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username_attempted` varchar(50) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `login_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `login_logs`
--

INSERT INTO `login_logs` VALUES (1,'admin','FAILURE','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36','2025-11-22 21:00:22'),(2,'admin','SUCCESS','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36','2025-11-22 21:01:27');

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `permissions` json DEFAULT NULL,
  `updated_by` varchar(50) DEFAULT 'system',
  `updated_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` VALUES (1,'Administrator','admin','{\"logs\": {\"read\": 1}, \"roles\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}, \"users\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}, \"issues\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}, \"statutes\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}, \"approvals\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}, \"small_claims\": {\"read\": 1, \"create\": 1, \"delete\": 1, \"update\": 1}}','system','2025-11-22 19:23:07'),(2,'Editor','editor','{\"logs\": {\"read\": 0}, \"roles\": {\"read\": 1, \"create\": 0, \"delete\": 0, \"update\": 0}, \"users\": {\"read\": 1, \"create\": 0, \"delete\": 0, \"update\": 0}, \"issues\": {\"read\": 1, \"create\": 1, \"delete\": 0, \"update\": 1}, \"statutes\": {\"read\": 1, \"create\": 1, \"delete\": 0, \"update\": 1}, \"approvals\": {\"read\": 0, \"create\": 0, \"delete\": 0, \"update\": 0}, \"small_claims\": {\"read\": 1, \"create\": 1, \"delete\": 0, \"update\": 1}}','system','2025-11-22 19:23:07');

--
-- Table structure for table `small_claims`
--

DROP TABLE IF EXISTS `small_claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `small_claims` (
  `id` int NOT NULL AUTO_INCREMENT,
  `state_id` int NOT NULL,
  `small_claims_cap` decimal(10,2) DEFAULT '0.00',
  `small_claims_info` text,
  `updated_by` varchar(50) DEFAULT 'admin',
  `updated_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_state_claim` (`state_id`),
  CONSTRAINT `small_claims_ibfk_1` FOREIGN KEY (`state_id`) REFERENCES `states` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `small_claims`
--

INSERT INTO `small_claims` VALUES (1,1,20000.00,'Justice of the Peace Court','admin','2025-11-22 19:23:07'),(2,2,10000.00,'Small Claims Division','admin','2025-11-22 19:23:07'),(3,3,5000.00,'City/Town Courts (varies by location, generally $5k)','admin','2025-11-22 19:23:07');

--
-- Table structure for table `small_claims_approvals`
--

DROP TABLE IF EXISTS `small_claims_approvals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `small_claims_approvals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `claim_id` int DEFAULT NULL,
  `state_id` int NOT NULL,
  `small_claims_cap` decimal(10,2) DEFAULT NULL,
  `small_claims_info` text,
  `action_type` varchar(10) NOT NULL,
  `status` varchar(20) DEFAULT 'PENDING',
  `submitted_by` varchar(50) DEFAULT NULL,
  `submitted_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `claim_id` (`claim_id`),
  KEY `state_id` (`state_id`),
  CONSTRAINT `small_claims_approvals_ibfk_1` FOREIGN KEY (`claim_id`) REFERENCES `small_claims` (`id`) ON DELETE SET NULL,
  CONSTRAINT `small_claims_approvals_ibfk_2` FOREIGN KEY (`state_id`) REFERENCES `states` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `small_claims_approvals`
--


--
-- Table structure for table `states`
--

DROP TABLE IF EXISTS `states`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `states` (
  `id` int NOT NULL AUTO_INCREMENT,
  `state_code` varchar(2) NOT NULL,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `states`
--

INSERT INTO `states` VALUES (1,'TX','Texas','texas'),(2,'CA','California','california'),(3,'NY','New York','new-york');

--
-- Table structure for table `statute_approvals`
--

DROP TABLE IF EXISTS `statute_approvals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `statute_approvals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `statute_id` int DEFAULT NULL,
  `state_id` int NOT NULL,
  `issue_id` int NOT NULL,
  `duration` varchar(10) NOT NULL DEFAULT 'years',
  `time_limit_type` varchar(20) DEFAULT 'exact',
  `time_limit_min` int DEFAULT NULL,
  `time_limit_max` int DEFAULT NULL,
  `details` text,
  `issue_info` text,
  `conditions_exceptions` text,
  `examples` text,
  `tolling` text,
  `code_reference` varchar(255) DEFAULT NULL,
  `official_source_url` text,
  `other_source_url` text,
  `action_type` varchar(10) NOT NULL,
  `status` varchar(20) DEFAULT 'PENDING',
  `submitted_by` varchar(50) DEFAULT NULL,
  `submitted_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `statute_id` (`statute_id`),
  KEY `state_id` (`state_id`),
  KEY `issue_id` (`issue_id`),
  CONSTRAINT `statute_approvals_ibfk_1` FOREIGN KEY (`statute_id`) REFERENCES `statutes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `statute_approvals_ibfk_2` FOREIGN KEY (`state_id`) REFERENCES `states` (`id`),
  CONSTRAINT `statute_approvals_ibfk_3` FOREIGN KEY (`issue_id`) REFERENCES `issues` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `statute_approvals`
--


--
-- Table structure for table `statutes`
--

DROP TABLE IF EXISTS `statutes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `statutes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `state_id` int NOT NULL,
  `issue_id` int NOT NULL,
  `duration` varchar(10) NOT NULL DEFAULT 'years',
  `time_limit_type` varchar(20) DEFAULT 'exact',
  `time_limit_min` int NOT NULL,
  `time_limit_max` int DEFAULT NULL,
  `details` text,
  `issue_info` text,
  `conditions_exceptions` text,
  `examples` text,
  `tolling` text,
  `code_reference` varchar(255) DEFAULT NULL,
  `official_source_url` text,
  `other_source_url` text,
  `updated_by` varchar(50) DEFAULT 'admin',
  `updated_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_statute` (`state_id`,`issue_id`),
  KEY `issue_id` (`issue_id`),
  CONSTRAINT `statutes_ibfk_1` FOREIGN KEY (`state_id`) REFERENCES `states` (`id`),
  CONSTRAINT `statutes_ibfk_2` FOREIGN KEY (`issue_id`) REFERENCES `issues` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `statutes`
--

INSERT INTO `statutes` VALUES (1,1,1,'years','exact',2,2,'Two years from the day the cause of action accrues.','Personal injury claims involving negligence or intentional torts.','None explicitly stated for general injury.','If injury occurred on Jan 5, 2023, deadline is Jan 5, 2025.',NULL,'Tex. Civ. Prac. & Rem. Code § 16.003','https://statutes.capitol.texas.gov/Docs/CP/htm/CP.16.htm','https://www.nolo.com/legal-encyclopedia/texas-personal-injury-laws-statute-limitations.html','admin','2025-11-22 19:23:07'),(2,1,2,'years','exact',4,4,'Four years after the day the cause of action accrues.','Failure to perform any term of a written contract without a legitimate legal excuse.','The clock starts when the breach occurs, not when the contract was signed.','Breach on July 1, 2020 -> Deadline July 1, 2024.',NULL,'Tex. Civ. Prac. & Rem. Code § 16.004','https://statutes.capitol.texas.gov/Docs/CP/htm/CP.16.htm',NULL,'admin','2025-11-22 19:23:07'),(3,1,3,'years','exact',2,2,'Strict two year limit from date of breach or tort.','Negligence committed by a professional health care provider.','Statute of Repose: Not more than 10 years total regardless of discovery.',NULL,NULL,'Tex. Civ. Prac. & Rem. Code § 74.251','https://statutes.capitol.texas.gov/',NULL,'admin','2025-11-22 19:23:07'),(4,2,1,'years','exact',2,2,'Two years from the date of injury.','Physical or emotional injury caused by another party.','Delayed discovery rule may apply if injury was not immediately apparent.','Accident: 1/1/23. File by: 1/1/25.',NULL,'Cal. Civ. Proc. Code § 335.1','https://leginfo.legislature.ca.gov/','https://www.courts.ca.gov/9618.htm','admin','2025-11-22 19:23:07'),(5,2,2,'years','exact',4,4,'Four years for written contracts.','Disputes regarding the terms of a written agreement.','Oral contracts have a shorter (2 year) limit.',NULL,NULL,'Cal. Civ. Proc. Code § 337','https://leginfo.legislature.ca.gov/',NULL,'admin','2025-11-22 19:23:07'),(6,2,3,'years','range',1,3,'Three years from date of injury or one year from discovery, whichever is first.','Malpractice by doctors or hospitals.','The \"whichever comes first\" rule makes this variable.','Discovered injury immediately? 3 years. Discovered it 4 years later? Too late.',NULL,'Cal. Civ. Proc. Code § 340.5','https://leginfo.legislature.ca.gov/',NULL,'admin','2025-11-22 19:23:07'),(7,3,1,'years','exact',3,3,'Three years usually.','Harm to person or property.','Toxic torts may have different discovery rules.','Slip and fall on Dec 1, 2022 -> File by Dec 1, 2025.',NULL,'N.Y. C.P.L.R. § 214','https://www.nysenate.gov/legislation/laws/CVP',NULL,'admin','2025-11-22 19:23:07'),(8,3,2,'years','exact',6,6,'Six years for contractual obligations.','Breach of a contract that is in writing.','Counterclaims may be allowed after this if related to the same transaction.',NULL,NULL,'N.Y. C.P.L.R. § 213','https://www.nysenate.gov/legislation/laws/CVP',NULL,'admin','2025-11-22 19:23:07');

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role_id` int DEFAULT NULL,
  `updated_by` varchar(50) DEFAULT 'system',
  `updated_dt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

INSERT INTO `users` VALUES (1,'admin','admin@statutechecker.com','scrypt:32768:8:1$smGjbkWRBcVBlm6V$2e803eb4d462fb6b8cc6c2ff58b7754b824a4670f3b939bc265a3852fd8060df08b0e30f52759a3a526bb8654ce4b726cf5ec5e2fc50c7e311d3b6ac02e3031d',1,'system_script','2025-11-22 21:00:51'),(2,'editor','editor@statutechecker.com','scrypt:32768:8:1$9kM5f3hS$6b8c40f4b40c45858585858585858585',2,'system','2025-11-22 19:23:07');

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed
