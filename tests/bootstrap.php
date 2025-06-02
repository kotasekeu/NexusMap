<?php

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

Tester\Environment::setup();
Tester\Environment::bypassFinals();

// Nastavení časové zóny pro testy
date_default_timezone_set('Europe/Prague');

// Vytvoření dočasné složky pro testy
define('TEMP_DIR', __DIR__ . '/../var/temp/' . getmypid());
@mkdir(TEMP_DIR, 0777, true);

// Registrace autoloaderu pro testy
Tester\Environment::setup();
Tester\Environment::bypassFinals(); 