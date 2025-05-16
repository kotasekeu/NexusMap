-- Základní data pro aplikaci

-- Typy zákazníků
INSERT INTO `customer_type` (`customer_type`, `label`) VALUES
('basic', 'Základní uživatel'),
('expert', 'Expertní uživatel');

-- Základní uživatelé
INSERT INTO `customers` (`row_id`, `customer_id`, `name`, `email`, `passhash`, `company`, `customer_type`, `monthly_tokens`, `remaining_tokens`, `customer_settings`, `active`, `visible`, `added`) VALUES
(1, 1, 'Tomáš Kotásek', 'expert@nexusmap.cz', '$2y$12$gtUmjkzHN4OfSVPVERlps.xvwyWOL7vLZwwpibCAoM4YO4CTBNQbi', '', 'expert', 100, 100, NULL, 1, 1, '2025-05-15 17:05:00'),
(2, 2, 'Základní uživatel', 'basic@nexusmap.cz', '$2y$12$m/58fPYkJ4TNZm43ntgq0.MeYy/HRZwsMHd3KhGtthv4L1ZKUxiNe', NULL, 'basic', 0, 0, NULL, 1, 1, '2025-05-15 17:07:57');

-- Základní routy
INSERT INTO `front_routes` (`route_id`, `url_pattern`, `presenter`, `action`, `parameters`, `order`, `created`) VALUES
(1, 'detail-projektu/<project_id>', 'Modules:Projects', 'detail', NULL, 1, '2025-04-06 19:06:43'),
(2, 'prehled-projektu', 'Modules:Projects', 'default', NULL, 2, '2025-04-22 12:57:05'),
(3, 'login', 'Modules:Login', 'default', NULL, 3, '2025-04-22 12:57:30'),
(4, 'upravit-som-atributy-projektu/<project_id>', 'Modules:Projects', 'editSom', NULL, 6, '2025-05-04 19:18:32'),
(5, 'upravit-projekt/<project_id>', 'Modules:Projects', 'edit', NULL, 7, '2025-05-04 19:19:13'),
(6, 'mapa-projektu/<project_id>/<map_name>', 'Modules:Projects', 'map', NULL, 8, '2025-05-14 17:16:24'),
(7, 'detail-bunky/<project_id>/<cell_id>', 'Modules:Projects', 'cell', NULL, 8, '2025-05-14 20:49:14'); 