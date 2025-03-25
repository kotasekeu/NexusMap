<?php

declare(strict_types=1);

namespace Api\Common\Router;

use Nette;
use Nette\Application\Routers\RouteList;


final class RouterFactory
{
	use Nette\StaticClass;

	public static function createRouter(): RouteList
	{
		$router = new RouteList;


		$router->addRoute('/v1/login', 'Api:Auth:login');
		$router->addRoute('/v1/swagger', "Api:Default:swagger");
		$router->addRoute('/v1[/<presenter>[/<action>[/<id>]]]', [
			'module' => 'Api',
			'presenter' => 'Default',
			'action' => 'default',
			'id' => null
		]);

		return $router;
	}
}
