-- This script defines the necessary tables for the Life Insurance Chatbot.
-- It includes DROP statements to ensure a clean setup.

DROP TABLE IF EXISTS `chat_log`;
DROP TABLE IF EXISTS `lead_capture`;
-- DROP TABLE IF EXISTS `policy_catalog`;
DROP TABLE IF EXISTS `user_context`;
DROP TABLE IF EXISTS `user_info`;

-- -----------------------------------------------------
-- Table `user_info`
-- Stores unique information for each user interacting with the chatbot.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_info` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `phone_number` VARCHAR(50) NOT NULL UNIQUE,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
);

-- -----------------------------------------------------
-- Table `user_context`
-- Stores the conversational state and collected data for each user.
-- This allows the chatbot to have stateful conversations.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_context` (
  `context_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `name` VARCHAR(255) NULL,
  `context_state` VARCHAR(100) NULL DEFAULT 'greeting',
  `user_intent` VARCHAR(100) NULL,
  `primary_need` VARCHAR(100) NULL,
  `insurance_goal` VARCHAR(100) NULL,
  `age` INT NULL,
  `income` BIGINT NULL,
  `coverage_required` VARCHAR(255) NULL,
  `term_length` VARCHAR(100) NULL,
  `budget` BIGINT NULL,
  `recommended_policy_type` VARCHAR(100) NULL,
  `selected_policy` VARCHAR(255) NULL,
  `lead_contact` VARCHAR(255) NULL,
  `contact_type` VARCHAR(50) NULL,
  `shown_recommendations` TEXT NULL,
  `state_history` JSON NULL,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`context_id`),
  UNIQUE INDEX `user_id_UNIQUE` (`user_id` ASC),
  CONSTRAINT `fk_user_context_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `user_info` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Table `policy_catalog`
-- Stores details of all available insurance policies. Used for RAG.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `policy_catalog` (
  `policy_id` VARCHAR(50) PRIMARY KEY,
  `policy_name` VARCHAR(200),
  `provider_name` VARCHAR(100),
  `policy_type` VARCHAR(50),
  `coverage_min` BIGINT,
  `coverage_max` BIGINT,
  `term_min` INT,
  `term_max` INT,
  `premium_min` BIGINT,
  `premium_max` BIGINT,
  `age_min` INT,
  `age_max` INT,
  `claim_settlement_ratio` DECIMAL(5,2),
  `riders` TEXT,
  `exclusions` TEXT,
  `tax_benefits` VARCHAR(100),
  `payout_options` VARCHAR(100),
  `benefits` TEXT,
  `claim_process` TEXT,
  `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Table `lead_capture`
-- Stores contact information for users who request a callback from an advisor.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lead_capture` (
  `lead_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `name` VARCHAR(255) NULL,
  `policy_id` VARCHAR(50) NULL,
  `contact_method` VARCHAR(50) NULL,
  `contact_value` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`lead_id`),
  INDEX `fk_lead_capture_user_id_idx` (`user_id` ASC),
  CONSTRAINT `fk_lead_capture_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `user_info` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Table `chat_log`
-- Logs every message exchanged between the user and the bot for analytics and debugging.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `chat_log` (
  `log_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `message_type` ENUM('user', 'bot') NOT NULL,
  `message` TEXT NOT NULL,
  `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  INDEX `fk_chat_log_user_id_idx` (`user_id` ASC),
  CONSTRAINT `fk_chat_log_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `user_info` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);
