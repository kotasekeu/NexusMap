-- Definice tabulek

DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers` (
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `passhash` varchar(255) NOT NULL,
  `company` varchar(255) DEFAULT NULL,
  `customer_type` varchar(50) NOT NULL DEFAULT 'basic',
  `monthly_tokens` int(11) NOT NULL DEFAULT 0,
  `remaining_tokens` int(11) NOT NULL DEFAULT 0,
  `customer_settings` varchar(1000) DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `visible` tinyint(1) NOT NULL DEFAULT 1,
  `added` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`row_id`),
  UNIQUE KEY `customer_id_visible` (`customer_id`,`active`),
  KEY `visible` (`active`),
  KEY `customer_type` (`customer_type`),
  CONSTRAINT `customers_ibfk_1` FOREIGN KEY (`customer_type`) REFERENCES `customer_type` (`customer_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `customer_type`;
CREATE TABLE `customer_type` (
  `customer_type` varchar(50) NOT NULL,
  `label` varchar(100) NOT NULL,
  UNIQUE KEY `code` (`customer_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `front_routes`;
CREATE TABLE `front_routes` (
  `route_id` int(11) NOT NULL AUTO_INCREMENT,
  `url_pattern` varchar(255) NOT NULL,
  `presenter` varchar(255) NOT NULL,
  `action` varchar(100) NOT NULL DEFAULT 'default',
  `parameters` varchar(255) DEFAULT NULL,
  `order` int(11) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` int(11) NOT NULL,
  `uid_hash` char(64) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 0,
  `ready_to_analyze` tinyint(1) NOT NULL DEFAULT 0,
  `results` text DEFAULT NULL,
  `som_settings` text NOT NULL,
  `project_settings` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT 1,
  `added` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`row_id`),
  UNIQUE KEY `uid_hash` (`uid_hash`),
  KEY `customer_id` (`customer_id`),
  KEY `result_id` (`results`(255)),
  KEY `analysis_done` (`status`),
  KEY `visible` (`visible`),
  KEY `project_id` (`project_id`,`customer_id`,`visible`),
  CONSTRAINT `fk_project_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `source_files` (
  `source_file_id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` int(11) NOT NULL,
  `row_count` int(11) NOT NULL,
  `column_count` int(11) NOT NULL,
  `column_names` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_size` float NOT NULL,
  `added` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`source_file_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `source_files_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 