SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `api_log`;
CREATE TABLE `api_log` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) DEFAULT NULL,
  `method` varchar(10) NOT NULL,
  `endpoint` varchar(255) NOT NULL,
  `request_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `response_code` int(4) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`log_id`),
  KEY `customer_id` (`customer_id`),
  KEY `response_code` (`response_code`),
  CONSTRAINT `fk_log_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `api_routes`;
CREATE TABLE `api_routes` (
  `route_id` int(11) NOT NULL AUTO_INCREMENT,
  `url_pattern` varchar(255) NOT NULL,
  `presenter` varchar(255) NOT NULL,
  `action` varchar(100) NOT NULL DEFAULT 'default',
  `default_id` varchar(50) DEFAULT NULL,
  `order` int(11) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers` (
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `company` varchar(255) DEFAULT NULL,
  `monthly_tokens` int(11) NOT NULL DEFAULT 0,
  `remaining_tokens` int(11) NOT NULL DEFAULT 0,
  `visible` tinyint(1) NOT NULL DEFAULT 1,
  `added` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `type_id` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`row_id`),
  UNIQUE KEY `customer_id_visible` (`customer_id`,`visible`),
  KEY `visible` (`visible`),
  KEY `fk_customer_type` (`type_id`),
  CONSTRAINT `fk_customer_type` FOREIGN KEY (`type_id`) REFERENCES `customer_type` (`type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `customer_type`;
CREATE TABLE `customer_type` (
  `type_id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `label` varchar(100) NOT NULL,
  PRIMARY KEY (`type_id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `files`;
CREATE TABLE `files` (
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  `file_id` int(11) NOT NULL,
  `project_id` int(11) NOT NULL,
  `hash_name` char(64) NOT NULL,
  `original_name` varchar(255) NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT 1,
  `added` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `size` int(11) NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `extension` varchar(10) NOT NULL,
  PRIMARY KEY (`row_id`),
  KEY `file_project` (`file_id`,`project_id`,`visible`),
  KEY `fk_file_project` (`project_id`),
  CONSTRAINT `fk_file_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `migrations`;
CREATE TABLE `migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `applied_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `filename` (`filename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` int(11) NOT NULL,
  `uid_hash` char(64) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `analysis_done` tinyint(1) NOT NULL DEFAULT 0,
  `result_id` int(11) DEFAULT NULL,
  `som_settings` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT 1,
  `added` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`row_id`),
  UNIQUE KEY `uid_hash` (`uid_hash`),
  KEY `customer_id` (`customer_id`),
  KEY `result_id` (`result_id`),
  KEY `analysis_done` (`analysis_done`),
  KEY `visible` (`visible`),
  KEY `project_id` (`project_id`,`customer_id`,`visible`),
  CONSTRAINT `fk_project_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `idSetting` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `editable` tinyint(1) unsigned NOT NULL DEFAULT 1,
  `main` tinyint(3) unsigned NOT NULL DEFAULT 1,
  `locale` varchar(3) NOT NULL DEFAULT 'all',
  `title` varchar(50) DEFAULT NULL,
  `key` varchar(20) DEFAULT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idSetting`),
  KEY `key` (`editable`),
  KEY `locale` (`locale`),
  KEY `main` (`main`),
  CONSTRAINT `settings_ibfk_1` FOREIGN KEY (`locale`) REFERENCES `list_languages` (`shortcut`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
