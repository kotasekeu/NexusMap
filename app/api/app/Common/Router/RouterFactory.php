<?php

declare(strict_types=1);

namespace Api\Common\Router;

use Nette;
use Nette\Application\Routers\RouteList;
use Api\Common\Service\RouterService;

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

        $router->addRoute('/v1[/<presenter>[/<action>[/<id>]]]', [
            'presenter' => 'Modules:Default',
            'action' => 'default',
            'id' => null
        ]);

        return $router;
    }
}
