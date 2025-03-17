<?php

declare(strict_types=1);

namespace App\Router;

use Nette;
use Nette\Application\Routers\Route;
use Nette\Application\Routers\RouteList;
use Nette\Caching\Cache;

final class RouterFactory
{
	use Nette\StaticClass;

	public static function createRouter(): RouteList
	{
		$router = new RouteList;
		$router[] = new Route('detail-projektu/<project_id>',																	'Front:Projects:detail');

		$router->addRoute('[<locale=cs cs|en>/]<presenter>/<action>[/<id>]', [
			'locale' => 'cs',
			'module' => 'Front',
			'presenter' => 'Default',
			'action' => 'default',
			'id' => NULL,
		]);

		return $router;
	}
}
