-- ============================================================
-- Jiinue Loan Engine - MySQL Schema + Data Dump
-- Generated for MySQL 5.7+ / MariaDB 10.3+
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `members` (
  `id`               INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name`             VARCHAR(255) NOT NULL,
  `phone`            VARCHAR(20) DEFAULT NULL,
  `savings_balance`  DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `is_blacklisted`   TINYINT(1) NOT NULL DEFAULT 0,
  `blacklist_reason` VARCHAR(500) DEFAULT NULL,
  `created_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `member_credit_scores` (
  `id`                   INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `member_id`            INT NOT NULL UNIQUE,
  `score`                INT NOT NULL DEFAULT 60,
  `label`                VARCHAR(20) NOT NULL DEFAULT 'Fair',
  `on_time_payments`     INT NOT NULL DEFAULT 0,
  `underpayments`        INT NOT NULL DEFAULT 0,
  `missed_payments`      INT NOT NULL DEFAULT 0,
  `loans_closed_on_time` INT NOT NULL DEFAULT 0,
  `updated_at`           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`member_id`) REFERENCES `members`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loan_products` (
  `id`                         INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_code`               VARCHAR(50) NOT NULL,
  `version_number`             INT NOT NULL DEFAULT 1,
  `product_name`               VARCHAR(255) NOT NULL,
  `is_active`                  TINYINT(1) NOT NULL DEFAULT 1,
  `effective_date`             DATE NOT NULL,
  `interest_method`            ENUM('flat','reducing_balance','compound') NOT NULL,
  `interest_rate`              DECIMAL(8,4) NOT NULL,
  `interest_period`            ENUM('monthly','yearly') NOT NULL,
  `repayment_frequency`        ENUM('daily','weekly','monthly','yearly') NOT NULL,
  `max_repayment_period`       INT DEFAULT NULL,
  `requires_guarantor`         TINYINT(1) NOT NULL DEFAULT 0,
  `is_multiple_of_savings`     TINYINT(1) NOT NULL DEFAULT 0,
  `savings_multiplier`         DECIMAL(8,4) DEFAULT NULL,
  `requires_security`          TINYINT(1) NOT NULL DEFAULT 0,
  `security_type`              ENUM('percentage','fixed_amount','custom_text') DEFAULT NULL,
  `security_value`             DECIMAL(15,2) DEFAULT NULL,
  `security_notes`             TEXT DEFAULT NULL,
  `requires_deposit`           TINYINT(1) NOT NULL DEFAULT 0,
  `deposit_type`               ENUM('percentage','fixed_amount') DEFAULT NULL,
  `deposit_value`              DECIMAL(15,2) DEFAULT NULL,
  `late_payment_penalty_type`  ENUM('percentage','fixed_amount') DEFAULT NULL,
  `late_payment_penalty_value` DECIMAL(15,2) DEFAULT NULL,
  `requires_appraisal`         TINYINT(1) NOT NULL DEFAULT 0,
  `requires_board_approval`    TINYINT(1) NOT NULL DEFAULT 0,
  `watchful_after_days`        INT DEFAULT 30,
  `non_performing_after_days`  INT DEFAULT 90,
  `doubtful_after_days`        INT DEFAULT 180,
  `allows_rescheduling`        TINYINT(1) NOT NULL DEFAULT 0,
  `reschedule_fee_type`        ENUM('percentage','fixed_amount') DEFAULT NULL,
  `reschedule_fee_value`       DECIMAL(15,2) DEFAULT NULL,
  `allows_offset`              TINYINT(1) NOT NULL DEFAULT 0,
  `offset_covers`              ENUM('savings','security','both') DEFAULT NULL,
  `offset_fee_type`            ENUM('percentage','fixed_amount') DEFAULT NULL,
  `offset_fee_value`           DECIMAL(15,2) DEFAULT NULL,
  `created_at`                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX (`product_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loan_product_fees` (
  `id`                  INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_product_id`     INT NOT NULL,
  `fee_name`            VARCHAR(255) NOT NULL,
  `fee_type`            ENUM('percentage','fixed_amount') NOT NULL,
  `fee_value`           DECIMAL(15,4) NOT NULL,
  `affects_principal`   TINYINT(1) NOT NULL DEFAULT 0,
  `show_in_statement`   TINYINT(1) NOT NULL DEFAULT 1,
  `ledger_account_name` VARCHAR(255) NOT NULL,
  FOREIGN KEY (`loan_product_id`) REFERENCES `loan_products`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loan_product_penalties` (
  `id`                  INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_product_id`     INT NOT NULL,
  `penalty_name`        VARCHAR(255) NOT NULL,
  `trigger`             ENUM('late_payment','missed_payment','meeting_absence') NOT NULL,
  `basis`               ENUM('fixed_amount','percent_of_balance','percent_of_principal') NOT NULL,
  `value`               DECIMAL(15,4) NOT NULL,
  `is_active`           TINYINT(1) NOT NULL DEFAULT 1,
  `ledger_account_name` VARCHAR(255) NOT NULL,
  FOREIGN KEY (`loan_product_id`) REFERENCES `loan_products`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loans` (
  `id`                      INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_number`             VARCHAR(50) NOT NULL UNIQUE,
  `member_id`               INT NOT NULL,
  `loan_product_id`         INT NOT NULL,
  `guarantor_member_id`     INT DEFAULT NULL,
  `principal_amount`        DECIMAL(15,2) NOT NULL,
  `security_provided_value` DECIMAL(15,2) DEFAULT NULL,
  `security_provided_notes` TEXT DEFAULT NULL,
  `deposit_paid_amount`     DECIMAL(15,2) DEFAULT NULL,
  `application_date`        DATE NOT NULL,
  `disbursement_date`       DATE DEFAULT NULL,
  `num_periods`             INT DEFAULT NULL,
  `status`                  ENUM('pending_application','appraised','approved','active','watchful','non_performing','doubtful','closed','written_off','rejected') NOT NULL DEFAULT 'pending_application',
  `outstanding_balance`     DECIMAL(15,2) NOT NULL,
  `appraisal_notes`         TEXT DEFAULT NULL,
  `approval_notes`          TEXT DEFAULT NULL,
  `rejection_reason`        TEXT DEFAULT NULL,
  `days_overdue`            INT NOT NULL DEFAULT 0,
  `created_at`              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`member_id`) REFERENCES `members`(`id`),
  FOREIGN KEY (`loan_product_id`) REFERENCES `loan_products`(`id`),
  FOREIGN KEY (`guarantor_member_id`) REFERENCES `members`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `repayments` (
  `id`                      INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_id`                 INT NOT NULL,
  `payment_date`            DATE NOT NULL,
  `amount_paid`             DECIMAL(15,2) NOT NULL,
  `amount_to_penalty`       DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `amount_to_interest`      DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `amount_to_principal`     DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `remaining_balance_after` DECIMAL(15,2) NOT NULL,
  `is_underpaid`            TINYINT(1) NOT NULL DEFAULT 0,
  `is_overpaid`             TINYINT(1) NOT NULL DEFAULT 0,
  `notes`                   TEXT DEFAULT NULL,
  `created_at`              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`loan_id`) REFERENCES `loans`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `ledger_transactions` (
  `id`                         INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `account_name`               VARCHAR(255) NOT NULL,
  `description`                VARCHAR(500) NOT NULL,
  `money_in`                   DECIMAL(15,2) DEFAULT NULL,
  `money_out`                  DECIMAL(15,2) DEFAULT NULL,
  `related_loan_id`            INT DEFAULT NULL,
  `transaction_date`           DATE NOT NULL,
  `is_reversed`                TINYINT(1) NOT NULL DEFAULT 0,
  `reversal_of_transaction_id` INT DEFAULT NULL,
  `created_at`                 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (`account_name`),
  FOREIGN KEY (`related_loan_id`) REFERENCES `loans`(`id`),
  FOREIGN KEY (`reversal_of_transaction_id`) REFERENCES `ledger_transactions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loan_schedule_entries` (
  `id`                   INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_id`              INT NOT NULL,
  `period_number`        INT NOT NULL,
  `due_date`             DATE NOT NULL,
  `expected_amount`      DECIMAL(15,2) NOT NULL,
  `expected_principal`   DECIMAL(15,2) NOT NULL,
  `expected_interest`    DECIMAL(15,2) NOT NULL,
  `opening_balance`      DECIMAL(15,2) NOT NULL,
  `closing_balance`      DECIMAL(15,2) NOT NULL,
  `is_paid`              TINYINT(1) NOT NULL DEFAULT 0,
  `is_missed`            TINYINT(1) NOT NULL DEFAULT 0,
  `is_cancelled`         TINYINT(1) NOT NULL DEFAULT 0,
  `amount_actually_paid` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `created_at`           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`loan_id`) REFERENCES `loans`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `loan_reschedules` (
  `id`                      INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `loan_id`                 INT NOT NULL,
  `reschedule_date`         DATE NOT NULL,
  `reason`                  TEXT DEFAULT NULL,
  `old_num_periods`         INT NOT NULL,
  `old_outstanding_balance` DECIMAL(15,2) NOT NULL,
  `new_num_periods`         INT NOT NULL,
  `new_installment`         DECIMAL(15,2) NOT NULL,
  `fee_charged`             DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  `created_at`              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`loan_id`) REFERENCES `loans`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `audit_log` (
  `id`          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `entity_type` VARCHAR(100) NOT NULL,
  `entity_id`   INT NOT NULL,
  `action`      VARCHAR(100) NOT NULL,
  `details`     TEXT DEFAULT NULL,
  `timestamp`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (`entity_type`, `entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- DATA
-- ============================================================

-- members
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (1, 'Alice Wanjiku', '0712 345 678', 150000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (2, 'Brian Otieno', '0723 456 789', 45000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (3, 'Catherine Njeri', '0734 567 890', 320000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (4, 'David Kamau', '0745 678 901', 8000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (5, 'Esther Achieng', '0756 789 012', 210000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (6, 'Francis Mwangi', '0767 890 123', 60000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (7, 'Grace Chebet', '0778 901 234', 95000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (8, 'Hassan Omar', '0789 012 345', 0.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (9, 'Irene Mutua', '0790 123 456', 500000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (10, 'James Kariuki', '0701 234 567', 33000.00, 0, NULL, '2026-07-13 09:46:23.532175+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (11, 'Bram', '+254741797609', 50000.00, 0, NULL, '2026-07-13 10:37:14.428626+03:00');
INSERT INTO `members` (`id`, `name`, `phone`, `savings_balance`, `is_blacklisted`, `blacklist_reason`, `created_at`) VALUES (12, 'Bramwel Oranga', '34543', 0.03, 0, NULL, '2026-07-14 02:29:56.351772+03:00');

-- No data in member_credit_scores

-- loan_products
INSERT INTO `loan_products` (`id`, `product_code`, `version_number`, `product_name`, `is_active`, `effective_date`, `interest_method`, `interest_rate`, `interest_period`, `repayment_frequency`, `max_repayment_period`, `requires_guarantor`, `is_multiple_of_savings`, `savings_multiplier`, `requires_security`, `security_type`, `security_value`, `security_notes`, `requires_deposit`, `deposit_type`, `deposit_value`, `late_payment_penalty_type`, `late_payment_penalty_value`, `requires_appraisal`, `requires_board_approval`, `watchful_after_days`, `non_performing_after_days`, `doubtful_after_days`, `allows_rescheduling`, `reschedule_fee_type`, `reschedule_fee_value`, `allows_offset`, `offset_covers`, `offset_fee_type`, `offset_fee_value`, `created_at`, `updated_at`) VALUES (1, 'EMERGENCY_LOAN', 1, 'Emergency Loan', 1, '2026-07-13', 'reducing_balance', 5.0000, 'monthly', 'daily', 6, 1, 0, NULL, 0, NULL, NULL, NULL, 0, NULL, NULL, NULL, 5000.00, 0, 0, NULL, NULL, NULL, 0, NULL, NULL, 0, NULL, NULL, NULL, '2026-07-13 10:21:01.618017+03:00', '2026-07-13 10:21:01.618017+03:00');
INSERT INTO `loan_products` (`id`, `product_code`, `version_number`, `product_name`, `is_active`, `effective_date`, `interest_method`, `interest_rate`, `interest_period`, `repayment_frequency`, `max_repayment_period`, `requires_guarantor`, `is_multiple_of_savings`, `savings_multiplier`, `requires_security`, `security_type`, `security_value`, `security_notes`, `requires_deposit`, `deposit_type`, `deposit_value`, `late_payment_penalty_type`, `late_payment_penalty_value`, `requires_appraisal`, `requires_board_approval`, `watchful_after_days`, `non_performing_after_days`, `doubtful_after_days`, `allows_rescheduling`, `reschedule_fee_type`, `reschedule_fee_value`, `allows_offset`, `offset_covers`, `offset_fee_type`, `offset_fee_value`, `created_at`, `updated_at`) VALUES (4, 'EMERGENCY_LOAN2', 1, 'Emergency Loan', 1, '2026-07-09', 'flat', 8.0000, 'monthly', 'daily', NULL, 1, 0, NULL, 1, 'percentage', 25.00, NULL, 0, NULL, NULL, 'percentage', 10.00, 0, 0, 30, 90, 180, 0, NULL, NULL, 0, NULL, NULL, NULL, '2026-07-14 03:14:59.982648+03:00', '2026-07-14 03:14:59.982648+03:00');

-- No data in loan_product_fees

-- No data in loan_product_penalties

-- loans
INSERT INTO `loans` (`id`, `loan_number`, `member_id`, `loan_product_id`, `guarantor_member_id`, `principal_amount`, `security_provided_value`, `security_provided_notes`, `deposit_paid_amount`, `application_date`, `disbursement_date`, `num_periods`, `status`, `outstanding_balance`, `appraisal_notes`, `approval_notes`, `rejection_reason`, `days_overdue`, `created_at`) VALUES (2, 'LN-20260714-00001', 2, 1, 9, 8888.00, NULL, NULL, NULL, '2026-07-14', '2026-07-14', 6, 'active', 8888.00, NULL, NULL, NULL, 0, '2026-07-14 03:00:15.806331+03:00');
INSERT INTO `loans` (`id`, `loan_number`, `member_id`, `loan_product_id`, `guarantor_member_id`, `principal_amount`, `security_provided_value`, `security_provided_notes`, `deposit_paid_amount`, `application_date`, `disbursement_date`, `num_periods`, `status`, `outstanding_balance`, `appraisal_notes`, `approval_notes`, `rejection_reason`, `days_overdue`, `created_at`) VALUES (3, 'LN-20260714-00002', 1, 1, 10, 6000.00, NULL, NULL, NULL, '2026-07-14', '2026-07-14', 7, 'active', 6000.00, NULL, NULL, NULL, 0, '2026-07-14 03:14:11.450889+03:00');

-- No data in repayments

-- ledger_transactions
INSERT INTO `ledger_transactions` (`id`, `account_name`, `description`, `money_in`, `money_out`, `related_loan_id`, `transaction_date`, `is_reversed`, `reversal_of_transaction_id`, `created_at`) VALUES (3, 'Jiinue Loan Account', 'Loan disbursement — LN-20260714-00001 to Brian Otieno', NULL, 8888.00, 2, '2026-07-14', 0, NULL, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `ledger_transactions` (`id`, `account_name`, `description`, `money_in`, `money_out`, `related_loan_id`, `transaction_date`, `is_reversed`, `reversal_of_transaction_id`, `created_at`) VALUES (4, 'Jiinue Loan Account', 'Loan disbursement — LN-20260714-00002 to Alice Wanjiku', NULL, 6000.00, 3, '2026-07-14', 0, NULL, '2026-07-14 03:15:28.263275+03:00');

-- loan_schedule_entries
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (1, 2, 1, '2026-07-15', 1489.87, 1475.26, 14.61, 8888.00, 7412.74, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (2, 2, 2, '2026-07-16', 1489.87, 1477.68, 12.19, 7412.74, 5935.06, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (3, 2, 3, '2026-07-17', 1489.87, 1480.11, 9.76, 5935.06, 4454.95, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (4, 2, 4, '2026-07-18', 1489.87, 1482.54, 7.32, 4454.95, 2972.40, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (5, 2, 5, '2026-07-19', 1489.87, 1484.98, 4.89, 2972.40, 1487.42, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (6, 2, 6, '2026-07-20', 1489.87, 1487.42, 2.45, 1487.42, 0.00, 0, 0, 0, 0.00, '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (7, 3, 1, '2026-07-15', 862.79, 852.93, 9.86, 6000.00, 5147.07, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (8, 3, 2, '2026-07-16', 862.79, 854.33, 8.46, 5147.07, 4292.75, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (9, 3, 3, '2026-07-17', 862.79, 855.73, 7.06, 4292.75, 3437.02, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (10, 3, 4, '2026-07-18', 862.79, 857.14, 5.65, 3437.02, 2579.88, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (11, 3, 5, '2026-07-19', 862.79, 858.55, 4.24, 2579.88, 1721.33, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (12, 3, 6, '2026-07-20', 862.79, 859.96, 2.83, 1721.33, 861.37, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');
INSERT INTO `loan_schedule_entries` (`id`, `loan_id`, `period_number`, `due_date`, `expected_amount`, `expected_principal`, `expected_interest`, `opening_balance`, `closing_balance`, `is_paid`, `is_missed`, `is_cancelled`, `amount_actually_paid`, `created_at`) VALUES (13, 3, 7, '2026-07-21', 862.79, 861.37, 1.42, 861.37, 0.00, 0, 0, 0, 0.00, '2026-07-14 03:15:28.263275+03:00');

-- No data in loan_reschedules

-- audit_log
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (1, 'loan_product', 1, 'created', '{"product_code": "EMERGENCY_LOAN", "version": 1, "product_name": "Emergency Loan"}', '2026-07-13 10:21:01.618017+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (2, 'loan', 1, 'created', '{"loan_number": "LN-20260713-00001", "member": "Bram", "product_id": 1, "principal": "5000"}', '2026-07-13 11:09:50.197716+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (3, 'ledger_transaction', 1, 'reversed', '{"offset_transaction_id": 2}', '2026-07-13 11:10:47.224900+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (4, 'ledger_transaction', 2, 'created', '{"type": "reversal", "reversal_of": 1}', '2026-07-13 11:10:47.224900+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (5, 'loan_product', 2, 'created', '{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}', '2026-07-14 02:38:13.535715+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (6, 'loan_product', 2, 'deleted', '{"product_code": "EMERGENCY_LOAN2"}', '2026-07-14 02:38:19.250156+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (7, 'loan_product', 3, 'created', '{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}', '2026-07-14 02:51:44.767010+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (8, 'loan_product', 3, 'deleted', '{"product_code": "EMERGENCY_LOAN2"}', '2026-07-14 02:51:56.660330+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (9, 'loan', 2, 'created', '{"loan_number": "LN-20260714-00001", "member": "Brian Otieno", "product_id": 1, "principal": "8888", "status": "approved"}', '2026-07-14 03:00:15.806331+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (10, 'loan', 2, 'disbursed', '{"date": "2026-07-14"}', '2026-07-14 03:08:12.559421+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (11, 'loan', 1, 'deleted', '{"loan_number": "LN-20260713-00001"}', '2026-07-14 03:08:24.336972+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (12, 'loan', 3, 'created', '{"loan_number": "LN-20260714-00002", "member": "Alice Wanjiku", "product_id": 1, "principal": "6000", "status": "approved"}', '2026-07-14 03:14:11.450889+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (13, 'loan_product', 4, 'created', '{"product_code": "EMERGENCY_LOAN2", "version": 1, "product_name": "Emergency Loan"}', '2026-07-14 03:14:59.982648+03:00');
INSERT INTO `audit_log` (`id`, `entity_type`, `entity_id`, `action`, `details`, `timestamp`) VALUES (14, 'loan', 3, 'disbursed', '{"date": "2026-07-14"}', '2026-07-14 03:15:28.263275+03:00');


SET FOREIGN_KEY_CHECKS = 1;
