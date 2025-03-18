<?php

declare(strict_types=1);

namespace Api;

use Nette\Bootstrap\Configurator;

class Bootstrap
{
	public static function boot(): Configurator
	{
		$configurator = new Configurator;

		$appDir = dirname(__DIR__ . '/app');

		$configurator->setDebugMode(true); // enable for your remote IP

		$configurator->enableTracy($appDir . '/../log');

		$configurator->setTimeZone('Europe/Prague');
		$configurator->setTempDirectory($appDir . '/../temp');

		$configurator->createRobotLoader()
			->addDirectory($appDir)
			->register();

		$configurator->addConfig($appDir . '/config/config.neon');

		return $configurator;
	}
}