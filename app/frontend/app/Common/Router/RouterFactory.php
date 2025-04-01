<?php

declare(strict_types=1);

namespace App\Common\Router;

use Nette;
use Nette\Application\Routers\RouteList;
use App\Common\Services\RouterService;

/**
 * Factory for creating application router
 */
final class RouterFactory
{
	use Nette\StaticClass;

	/**
	 * Creates and configures application router
	 *
	 * @param RouterService $routerService Service for loading route configuration
	 * @return RouteList Configured router
	 */
	public static function createRouter(RouterService $routerService): RouteList
	{
		$router = new RouteList();

		$routes = $routerService->getAllRoutes();

		foreach ($routes as $key => $item) {
			$router->addRoute($key, $item);
		}

		$router->addRoute('projekty/', 'Modules:Projects:default');
		$router->addRoute('login/', 'Modules:Login:default');

		$router->addRoute('<presenter>/<action>/[<id>]', [
			'presenter' => 'Modules:Dashboard',
			'action' => 'default',
			'id' => null
		]);

		return $router;
	}
}
