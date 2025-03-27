<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Api\Common\Exception\UnauthorizedException;

abstract class BaseService
{
	protected int $loggedUserId;
	private AuthService $authService;

	public function __construct(AuthService $authService)
	{
		$this->authService = $authService;
	}

	/**
	 * @throws UnauthorizedException
	 */
	protected function validateToken(): void
	{
		$token = $this->authService->getCurrentToken();
		if (!$token || !$this->authService->isTokenValid($token)) {
			throw new UnauthorizedException('Invalid or missing token');
		}
		$this->loggedUserId = $this->authService->getUserIdFromToken($token);
	}

	public function setLoggedUserId(int $loggedUserId): void
	{
		$this->loggedUserId = $loggedUserId;
	}
}
