<?php

declare(strict_types=1);

namespace Api\Common\Facade;

use Api\Common\Exception\UnauthorizedException;

abstract class BaseFacade
{
	protected int $loggedUserId;
	private AuthService $authService;  // service pro práci s JWT tokenem

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

	public function setLoggedUserId(int $loggedUserId)
	{
		$this->loggedUserId = $loggedUserId;
	}


	// /**
	//  * Všechny public metody facade by měly volat validateToken
	//  */
	// public function findAll(): array
	// {
	// 	$this->validateToken();
	// 	// implementace
	// }

	// public function findById(int $id): ?object
	// {
	// 	$this->validateToken();
	// 	// implementace
	// }
}
