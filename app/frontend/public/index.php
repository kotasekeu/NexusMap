<?php

declare(strict_types=1);

define('WWW_DIR', dirname(__FILE__));

define('APP_DIR', WWW_DIR . '/../app');

require __DIR__ . '/../vendor/autoload.php';

App\Bootstrap::boot()
	->createContainer()
	->getByType(Nette\Application\Application::class)
	->run();
