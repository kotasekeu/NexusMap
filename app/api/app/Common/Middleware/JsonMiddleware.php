<?php

declare(strict_types=1);

namespace Api\Common\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

class JsonMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $response = $handler->handle($request);
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function formatResponse($data): string
    {
        return json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }

    public function addMetadata(array $response): array
    {
        return array_merge($response, [
            'metadata' => [
                'timestamp' => time(),
                'version' => '1.0'
            ]
        ]);
    }
}
