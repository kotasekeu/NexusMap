<?php

declare(strict_types=1);

use Nette\Configurator;

// Načtení autoloaderu Composeru
require __DIR__ . '/../vendor/autoload.php';

// Vytvoření konfigurátoru
$configurator = new Configurator;

// Nastavení režimu ladění
$configurator->setDebugMode(true);

// Nastavení adresáře pro cache
$configurator->setTempDirectory(__DIR__ . '/../temp');

// Načtení konfiguračních souborů
$configurator->addConfig(__DIR__ . '/../app/config/config.neon');
//$configurator->addConfig(__DIR__ . '/../app/config/local.neon');

// Vytvoření kontejneru
$container = $configurator->createContainer();

// Registrace kontejneru pro testy
Tester\Environment::setup();
Tester\Environment::bypassFinals();

return $container; 