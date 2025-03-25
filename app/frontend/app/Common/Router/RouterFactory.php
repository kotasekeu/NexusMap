<?php

declare(strict_types=1);

namespace App\Common\Router;

use Nette;
use Nette\Application\Routers\Route;
use Nette\Application\Routers\RouteList;

final class RouterFactory
{
    use Nette\StaticClass;

    public static function createRouter(): RouteList
    {
        $router = new RouteList();

        $router->addRoute('projekty', 'Modules:Projects:default');

        $router->addRoute('<presenter>/<action>[/<id>]', [
            'presenter' => 'Modules:Dashboard',
            'action' => 'default',
            'id' => null
        ]);

        return $router;
    }
}
