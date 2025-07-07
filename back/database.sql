-- This script defines the necessary tables for the Life Insurance Chatbot.
-- It includes DROP statements to ensure a clean setup.

DROP TABLE IF EXISTS `chat_log`;
DROP TABLE IF EXISTS `lead_capture`;
DROP TABLE IF EXISTS `user_quotations`;
-- DROP TABLE IF EXISTS `policy_catalog`;
DROP TABLE IF EXISTS `user_context`;
DROP TABLE IF EXISTS `user_info`;

-- -----------------------------------------------------
-- Table `user_info`
-- Stores unique information for each user interacting with the chatbot.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS user_info (
  user_id INT NOT NULL AUTO_INCREMENT,
  phone_number VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(100),
  email VARCHAR(100),
  dob DATE,
  gender VARCHAR(20),
  nationality VARCHAR(100),
  marital_status VARCHAR(50),
  education VARCHAR(100),
  employment_status VARCHAR(100),
  existing_policy VARCHAR(100),
  annual_income BIGINT,
  gst_applicable VARCHAR(10) DEFAULT 'No',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id)
);

-- -----------------------------------------------------
-- Table `user_context`
-- Stores the conversational state and collected data for each user.
-- This allows the chatbot to have stateful conversations.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS user_context (
  context_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,

  -- Flow Management
  context_state VARCHAR(100) DEFAULT 'greeting',
  previous_state VARCHAR(100),
  state_history JSON,

  -- Intent Tracking & FAQ
  user_intent VARCHAR(100),
  last_user_intent VARCHAR(100),
  last_user_query TEXT,
  faq_topic_focus VARCHAR(100),
  diversion_count INT DEFAULT 0,

  -- Quotation Input
  primary_need VARCHAR(100),
  insurance_goal VARCHAR(100),
  coverage_and_premium BIGINT,
  premium_budget BIGINT,
  plan_type VARCHAR(100),
  policy_term INT,
  premium_payment_term INT,
  premium_payment_frequency VARCHAR(50),
  payout_frequency VARCHAR(50),

  -- Quotation Output
  quotation_ready BOOLEAN DEFAULT FALSE,
  quote_accepted BOOLEAN DEFAULT FALSE,
  payment_redirected BOOLEAN DEFAULT FALSE,
  quote_number VARCHAR(100),
  sum_assured BIGINT,
  base_premium BIGINT,
  gst_amount BIGINT,
  total_premium BIGINT,

  -- Recommendations
  recommended_policy_type VARCHAR(100),
  shown_recommendations JSON,
  selected_policy VARCHAR(255),
  selected_policy_details JSON,

  -- Lead Info
  lead_contact VARCHAR(255),
  contact_type VARCHAR(50),

  -- Timestamps
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (context_id),
  UNIQUE KEY user_id_UNIQUE (user_id),
  CONSTRAINT fk_user_context_user_id
    FOREIGN KEY (user_id)
    REFERENCES user_info (user_id)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Table `user_quotations`
-- Stores the quotation details for each user.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_quotations` (
  `quotation_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `dob` DATE,
  `gender` VARCHAR(20),
  `nationality` VARCHAR(100),
  `marital_status` VARCHAR(50),
  `education` VARCHAR(100),
  `existing_policy` VARCHAR(100),
  `gst_applicable` VARCHAR(10) DEFAULT 'No',
  `plan_option` VARCHAR(100),
  `coverage_required` BIGINT,
  `premium_budget` BIGINT,
  `policy_term` INT,
  `premium_payment_term` INT,
  `premium_frequency` VARCHAR(50),
  `income_payout_frequency` VARCHAR(50),
  `quote_number` VARCHAR(100),
  `sum_assured` BIGINT,
  `base_premium` BIGINT,
  `gst_amount` BIGINT,
  `total_premium` BIGINT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`quotation_id`),
  INDEX `fk_user_quotations_user_id_idx` (`user_id` ASC),
  CONSTRAINT `fk_user_quotations_user_id`
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
