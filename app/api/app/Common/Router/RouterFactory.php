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
		$router = new RouteList();

//		$router->addRoute('/v1/login', 'Modules:Auth:login');

		$router->addRoute('/v1/customers',									"Modules:Customers:default");
		$router->addRoute('/v1/customers/<id>',									"Modules:Customers:detail");

		$router->addRoute('/v1/swagger',									"Modules:Default:swagger");

		$router->addRoute('/v1[/<presenter>[/<action>[/<id>]]]', [
			'presenter' => 'Modules:Default',
			'action' => 'default',
			'id' => null
		]);

		return $router;
	}
}
