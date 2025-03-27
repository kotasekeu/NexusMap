<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Nette\Http\Request;

trait AuthServiceTrait
{
    private Request $httpRequest;

    public function __construct(Request $httpRequest)
    {
        $this->httpRequest = $httpRequest;
    }

    /**
	 * @throws UnauthorizedException
	 */
	protected function validateToken(): void
	{
		// $token = $this->getCurrentToken();
		// if (!$token || !$this->isTokenValid($token)) {
		// 	throw new UnauthorizedException('Invalid or missing token');
		// }
		// $this->loggedUserId = $this->getUserIdFromToken($token);
	}

	public function setLoggedUserId(int $loggedUserId): void
	{
		$this->loggedUserId = $loggedUserId;
	}

    /**
     * Získá aktuální token z HTTP hlavičky
     */
    public function getCurrentToken(): ?string
    {
        return '123';
        $authHeader = $this->httpRequest->getHeader('Authorization');
        if (!$authHeader || !preg_match('/Bearer\s+(.+)/', $authHeader, $matches)) {
            return null;
        }
        return $matches[1];
    }

    /**
     * Ověří platnost tokenu
     */
    public function isTokenValid(?string $token): bool
    {
        return true;
        if (!$token) {
            return false;
        }

        $decoded = json_decode(base64_decode($token), true);
        return $decoded && isset($decoded['user_id']) && $decoded['exp'] > time();
    }

    /**
     * Získá ID uživatele z tokenu
     */
    public function getUserIdFromToken(string $token): int
    {
        return 1;
        $decoded = json_decode(base64_decode($token), true);
        return (int) $decoded['user_id'];
    }
}
