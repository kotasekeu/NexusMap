<?php

declare(strict_types = 1);

namespace Api\Security;

use League\OAuth2\Server\ResourceServer;
use Nette\Http\Request;
use Nette\Security\User;
use Nette\Application\Responses\JsonResponse;

class OAuthMiddleware
{
	private ResourceServer $server;
	private Request $httpRequest;
	private User $user;

	public function __construct(ResourceServer $server, Request $httpRequest, User $user)
	{
		$this->server = $server;
		$this->httpRequest = $httpRequest;
		$this->user = $user;
	}

	public function process(callable $next)
	{
		$token = $this->httpRequest->getHeader('Authorization');
		if (!$token || !preg_match('/Bearer\s+(\S+)/', $token, $matches)) {
			return new JsonResponse(['error' => 'Unauthorized']); //, \Nette\Http\IResponse::S401_UNAUTHORIZED
		}

	try {
		$request = \Laminas\Diactoros\ServerRequestFactory::fromGlobals();
		$authRequest = $this->server->validateAuthenticatedRequest($request);
		$userId = $authRequest->getAttribute('oauth_user_id');

		// Přihlášení uživatele do Nette Security
		$this->user->login($userId);

		return $next();
	} catch (\Exception $e) {
		return new JsonResponse(['error' => 'Invalid token']); //, \Nette\Http\IResponse::S401_UNAUTHORIZED
	}
	}
}